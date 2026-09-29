# IMPORTING THE REQUIRED MODULES
from tkinter import *
from tkinter import ttk, messagebox, filedialog
import yt_dlp
from yt_dlp.utils import DownloadError
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading


if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DOWNLOAD_FOLDER_NAME = "Downly downloads"
COOKIE_FILE_NAME = "youtube_cookies.txt"
SETTINGS_FILE_NAME = "downly_settings.json"
FFMPEG_EXE_NAME = 'ffmpeg.exe' if os.name == 'nt' else 'ffmpeg'
FFPROBE_EXE_NAME = 'ffprobe.exe' if os.name == 'nt' else 'ffprobe'

# These are filled in by init_storage() once the window exists, because it may
# need to show an error dialog if no writable folder can be found.
DATA_DIR = None
DOWNLOAD_DIR = None
COOKIE_FILE_PATH = None
SETTINGS_PATH = None
SETTINGS = {}

# Phrases in yt-dlp's error text that mean "YouTube wants a signed-in session".
# Deliberately specific: a bare '403' or 'forbidden' can match video IDs or
# unrelated errors, so HTTP status codes are checked separately (see is_auth_error).
AUTH_PHRASES = (
    'sign in to confirm',      # bot check and age check
    'not a bot',
    'age-restricted',
    'age restricted',
    'private video',
    'members-only',
    'members only',
    'join this channel',
    '--cookies',               # yt-dlp appends this hint to its sign-in errors
)

# --- FILENAME SANITIZING ---
INVALID_FILENAME_CHARS = r'[<>:"/\\|?*%\x00-\x1f]'
WINDOWS_RESERVED = {"CON", "PRN", "AUX", "NUL",
                    *(f"COM{i}" for i in range(1, 10)),
                    *(f"LPT{i}" for i in range(1, 10))}
MAX_FILENAME_LEN = 150


def sanitize_filename(name):
    """Make a user-typed name safe to use as a filename inside DOWNLOAD_DIR.
    Replaces characters that are illegal on Windows, that would let the name
    escape the folder (/ and \\), or that yt-dlp would read as template syntax (%)."""
    name = re.sub(INVALID_FILENAME_CHARS, "_", name).strip().strip(".").strip()
    name = name[:MAX_FILENAME_LEN].rstrip(". ")
    if name.split(".")[0].upper() in WINDOWS_RESERVED:
        name = f"_{name}"
    return name


# --- ERROR CLASSIFICATION ---
def _http_status(error):
    """Dig an HTTP status code out of a DownloadError's cause chain, if there is one."""
    exc_info = getattr(error, 'exc_info', None)
    cause = exc_info[1] if exc_info else None
    for _ in range(5):
        if cause is None:
            return None
        status = getattr(cause, 'status', None)
        if isinstance(status, int):
            return status
        cause = getattr(cause, 'cause', None) or getattr(cause, '__cause__', None)
    return None


def is_auth_error(error):
    """True if the failure looks like YouTube demanding authentication."""
    if _http_status(error) in (401, 403):
        return True
    message = str(error).lower().replace('\u2019', "'")   # yt-dlp uses a curly apostrophe
    return any(phrase in message for phrase in AUTH_PHRASES)


# --- COOKIE FILE CHECK ---
def check_cookie_file(path):
    """Light sanity check on a user-selected cookies file.
    Returns an error message, or None if it looks usable."""
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read(2_000_000).lower()
    except OSError as e:
        return f"Couldn't read that file: {e}"
    if 'youtube.com' not in text:
        return "That doesn't look like a YouTube cookies file (no youtube.com entries found)."
    return None


# --- SETTINGS (tiny JSON file, currently just the FFmpeg folder) ---
def load_settings():
    try:
        with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_settings():
    try:
        with open(SETTINGS_PATH, 'w', encoding='utf-8') as f:
            json.dump(SETTINGS, f, indent=2)
    except OSError as e:
        print(f"Couldn't save settings: {e}")


# --- STORAGE LOCATION ---
def _is_writable(folder):
    """Really try to write there -- os.access() is unreliable for folders on Windows."""
    try:
        os.makedirs(folder, exist_ok=True)
        with tempfile.TemporaryFile(dir=folder):
            pass
        return True
    except OSError:
        return False


def init_storage():
    """Pick a folder we can actually write to (next to the app if possible,
    otherwise ~/Downly) and set up all the paths that live inside it."""
    global DATA_DIR, DOWNLOAD_DIR, COOKIE_FILE_PATH, SETTINGS_PATH, SETTINGS

    candidates = [BASE_DIR, os.path.join(os.path.expanduser("~"), "Downly")]
    for folder in candidates:
        downloads = os.path.join(folder, DOWNLOAD_FOLDER_NAME)
        if _is_writable(folder) and _is_writable(downloads):
            DATA_DIR = folder
            DOWNLOAD_DIR = downloads
            COOKIE_FILE_PATH = os.path.join(folder, COOKIE_FILE_NAME)
            SETTINGS_PATH = os.path.join(folder, SETTINGS_FILE_NAME)
            SETTINGS = load_settings()
            return

    r.withdraw()
    messagebox.showerror(
        "Downly can't start",
        "Downly couldn't find a folder it is allowed to write to.\n\nTried:\n"
        + "\n".join(f"  {c}" for c in candidates)
        + "\n\nTry moving the app to a folder like Documents or Desktop."
    )
    r.destroy()
    sys.exit(1)


def open_folder(path):
    """Open a folder in the system file manager."""
    try:
        if sys.platform.startswith('win'):
            os.startfile(path)
        elif sys.platform == 'darwin':
            subprocess.Popen(['open', path])
        else:
            subprocess.Popen(['xdg-open', path])
    except Exception as e:
        messagebox.showerror("Couldn't open folder", str(e))


# --- FFMPEG DISCOVERY ---
def find_ffmpeg():
    """Look for ffmpeg in the folder the user picked earlier, then ./ffmpeg
    (or ./ffmpeg/bin), then on the system PATH.
    Returns the folder containing ffmpeg, or None if it isn't found."""
    folders = []
    saved = SETTINGS.get('ffmpeg_dir')
    if saved:
        folders.append(saved)
    folders += [
        os.path.join(BASE_DIR, "ffmpeg"),
        os.path.join(BASE_DIR, "ffmpeg", "bin"),
    ]
    search_path = os.pathsep.join(folders + [os.environ.get("PATH", "")])
    exe = shutil.which("ffmpeg", path=search_path)
    return os.path.dirname(exe) if exe else None


def ensure_ffmpeg():
    """Make sure FFmpeg is available, offering to auto-install it if missing.
    Returns True if FFmpeg can be used. Must be called from the main thread."""
    if find_ffmpeg():
        return True

    # If the user is on Windows, offer the automated winget install
    if sys.platform.startswith('win'):
        wants_to_install = messagebox.askyesno(
            "FFmpeg Missing",
            "Downly needs FFmpeg to merge video and convert MP3s.\n\n"
            "Would you like Downly to automatically install it now? (This will open a terminal window)."
        )
        
        if wants_to_install:
            try:
                # 'start cmd /wait /c' opens a visible terminal window, runs the command, and waits for it to finish before closing
                subprocess.run('start cmd /wait /c "winget install ffmpeg"', shell=True)
                
                # Check if the installation was successful and it's now on the PATH
                if find_ffmpeg():
                    messagebox.showinfo("Success", "FFmpeg installed successfully!")
                    return True
                else:
                    messagebox.showwarning("Warning", "Install finished, but FFmpeg still wasn't found. You may need to restart Downly.")
                    return False
            except Exception as e:
                messagebox.showerror("Error", f"Failed to run installer: {e}")
                return False

    # Fallback for Mac/Linux users, or if they clicked "No" to the auto-install
    wants_to_browse = messagebox.askyesno(
        "Locate FFmpeg",
        "Could not auto-install. Would you like to locate the ffmpeg folder yourself?"
    )
    
    if not wants_to_browse:
        return False

    path = filedialog.askopenfilename(
        title=f"Select {FFMPEG_EXE_NAME}",
        filetypes=[("FFmpeg", FFMPEG_EXE_NAME), ("All files", "*.*")],
    )
    
    if not path:
        return False

    folder = os.path.dirname(path)
    SETTINGS['ffmpeg_dir'] = folder
    save_settings()
    
    return find_ffmpeg() is not None


def common_opts():
    """Options shared by both MP3 and MP4 downloads."""
    opts = {
        'remote_components': ['ejs:github'],
        'throttledratelimit': 100_000,  # Helps bypass throttling without cookies
    }
    ffmpeg_dir = find_ffmpeg()
    if ffmpeg_dir:
        opts['ffmpeg_location'] = ffmpeg_dir

    # Once a cookies file exists in DATA_DIR (via the auth screen), every future
    # download picks it up automatically, including after restarting the app.
    if COOKIE_FILE_PATH and os.path.exists(COOKIE_FILE_PATH):
        opts['cookiefile'] = COOKIE_FILE_PATH

    return opts


# INITIAL TKINTER FRAME
r = Tk()

# Global variables for the current active UI elements
current_progress_bar = None
current_percent_label = None
current_status_label = None


# --- INPUT VALIDATION ---
def validate_download_inputs(link, filename):
    """Checks the URL and filename before a download starts.
    Returns None if everything looks fine, or an error message string if not."""
    link = link.strip()
    filename = filename.strip()

    if not link:
        return 'Please enter a URL.'
    if not (link.startswith('http://') or link.startswith('https://')):
        return "That doesn't look like a valid URL (must start with http:// or https://)."
    if not filename:
        return 'Please enter a valid filename.'
    return None


# FIRST FRAME/MENU FRAME
def hide_frames():
    """Hides all frames or widgets in the main window."""
    for frames in r.winfo_children():
        frames.grid_forget()


def firstfunction():
    hide_frames()
    global menu_frame
    menu_frame = Frame(r, bg="white")
    menu_frame.grid(sticky="nsew")
    r.title('Downly')

    l = Label(menu_frame, text='Welcome to Downly', font=("Helvetica", 24, "bold"), fg="dark blue", bg="white")
    l.grid(row=0, column=0, columnspan=2, pady=(20, 10), padx=10, sticky="n")

    mp3_button = Button(menu_frame, text='MP3', padx=40, pady=20, fg='white', bg='#007ACC', font=("Arial", 14, "bold"),
                        command=mp3_converter)
    mp4_button = Button(menu_frame, text='MP4', padx=40, pady=20, fg='white', bg='#5F6368', font=("Arial", 14, "bold"),
                        command=mp4_converter)
    mp3_button.grid(row=1, column=0, padx=10, pady=10)
    mp4_button.grid(row=1, column=1, padx=10, pady=10)

    exit_home_button = Button(menu_frame, text='Exit', padx=40, pady=12, fg='white', bg='#d9534f',
                              font=("Arial", 14, "bold"), command=r.destroy)
    exit_home_button.grid(row=2, column=0, columnspan=2, padx=10, pady=(10, 20), sticky="ew")

    r.grid_columnconfigure(0, weight=1)
    r.grid_columnconfigure(1, weight=1)
    r.grid_rowconfigure(1, weight=1)


# --- AUTHENTICATION / COOKIE SCREEN ---
def retry_download(link, filename, file_type, quality_label=None):
    """Rebuild the right download screen, refill it, and start the download again."""
    hide_frames()
    if file_type == 'mp4':
        mp4_converter()
        entry1.insert(0, link)
        entry2.insert(0, filename)
        quality_var.set(quality_label)
        mp4_download()
    else:
        mp3_converter()
        entry3.insert(0, link)
        entry4.insert(0, filename)
        mp3_download()


def auth_required_screen(link, filename, file_type, quality_label=None):
    hide_frames()
    global auth_frame
    auth_frame = Frame(r, bg="white")
    auth_frame.grid(padx=20, pady=20, sticky="nsew")

    l1 = Label(auth_frame, text='YouTube Blocked the Download', font=("Arial", 16, "bold"), bg="white", fg="#d9534f")

    stale_note = ""
    if os.path.exists(COOKIE_FILE_PATH):
        stale_note = ("A cookies file is already installed, but YouTube still blocked this download.\n"
                      "It may have expired. Export a fresh one and select it below.\n\n")

    instructions = (
        stale_note +
        "YouTube is requiring authentication (Bot Check / Age Restriction / 403 Error).\n\n"
        "To get past this:\n"
        "1. Open Google Chrome.\n"
        "2. Install the extension called 'Get cookies.txt locally'.\n"
        "3. Go to www.youtube.com (make sure you are logged in).\n"
        "4. Click the extension icon and export the cookies (youtube.com only).\n"
        "5. Click 'Select cookies file' below and choose the exported file.\n\n"
        "Downly keeps a copy, so you only need to do this once."
    )

    l2 = Label(auth_frame, text=instructions, font=("Arial", 12), bg="white", justify=LEFT)

    l1.grid(row=0, column=0, pady=(10, 5), sticky="w")
    l2.grid(row=1, column=0, sticky="w", pady=(0, 10))

    error_label = Label(auth_frame, text="", font=("Arial", 10, "bold"), fg="red", bg="white",
                        wraplength=460, justify=LEFT)
    error_label.grid(row=2, column=0, sticky="w")

    def choose_cookie_file():
        path = filedialog.askopenfilename(
            title="Select your exported YouTube cookies file",
            filetypes=[("Cookies file", "*.txt"), ("All files", "*.*")],
        )
        if not path:
            return

        problem = check_cookie_file(path)
        if problem:
            error_label.config(text=problem)
            return

        try:
            if os.path.abspath(path) != os.path.abspath(COOKIE_FILE_PATH):
                shutil.copyfile(path, COOKIE_FILE_PATH)
        except OSError as e:
            error_label.config(text=f"Couldn't save the cookies file: {e}")
            return

        retry_download(link, filename, file_type, quality_label)

    select_button = Button(auth_frame, text='Select cookies file', padx=20, pady=10, fg='white', bg='#f0ad4e',
                           font=("Arial", 12, "bold"), command=choose_cookie_file)
    back_button = Button(auth_frame, text='Cancel', padx=40, pady=10, bg='#6d7985', fg='white', command=firstfunction)

    select_button.grid(row=3, column=0, pady=10, sticky="ew")
    back_button.grid(row=4, column=0, pady=10, sticky="ew")


# Quality options
QUALITY_OPTIONS = {
    '1080p': 1080,
    '720p': 720,
    '480p': 480,
    'Best available': None,
}


def build_mp4_format(quality_label):
    max_height = QUALITY_OPTIONS.get(quality_label)
    if max_height is None:
        return 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
    return f'bestvideo[height<={max_height}][ext=mp4]+bestaudio[ext=m4a]/best[height<={max_height}][ext=mp4]/best'


# --- PROGRESS HOOK DEFINITIONS ---
def yt_dlp_hook(d):
    """Fired by yt-dlp during download to track progress."""
    if d['status'] == 'downloading':
        total = d.get('total_bytes') or d.get('total_bytes_estimate')
        downloaded = d.get('downloaded_bytes', 0)

        if total and total > 0:
            percent_float = (downloaded / total) * 100
            percent_str = f"{percent_float:.1f}%"
            r.after(0, lambda: _update_progress_ui(percent_float, percent_str))

    elif d['status'] == 'finished':
        r.after(0, lambda: current_status_label.config(text="Processing and merging files... Please wait."))


def _update_progress_ui(val, text):
    """Safely updates the progress bar and label from the main thread."""
    if current_progress_bar and current_percent_label:
        current_progress_bar['value'] = val
        current_percent_label.config(text=text)


# --- SHARED DOWNLOAD HELPERS (used by both the MP3 and MP4 screens) ---
def _build_status_widgets(parent):
    """Creates the status label, progress bar and percent label for a download screen."""
    global current_progress_bar, current_percent_label, current_status_label
    current_status_label = Label(parent, text='', font=("Arial", 12), bg="white", fg="#555555",
                                 wraplength=460, justify=LEFT)
    current_progress_bar = ttk.Progressbar(parent, orient=HORIZONTAL, length=300, mode='determinate')
    current_percent_label = Label(parent, text="0.0%", font=("Arial", 12, "bold"), bg="white", fg="#4285F4")


def _preflight_ok(link, filename):
    """Validate inputs and make sure FFmpeg is available. Shows the problem in the
    status label and returns False if the download shouldn't start."""
    error = validate_download_inputs(link, filename)
    if error:
        current_status_label.config(text=error, fg='#d9534f')
        return False
    if not ensure_ffmpeg():
        current_status_label.config(text="FFmpeg is required. Click OK to try again and locate it.", fg='#d9534f')
        return False
    return True


def _begin_download_ui(ok_button, back_button, first_row, raw_name, filename):
    """Lock the screen and show the progress widgets once a download starts."""
    ok_button.config(state=DISABLED)
    back_button.grid_remove()

    text = 'Downloading...'
    if filename != raw_name.strip():
        text = f"Downloading... (saved as '{filename}')"
    current_status_label.config(text=text, fg='#555555')

    current_progress_bar.grid(row=first_row, column=0, pady=(10, 5), sticky="ew")
    current_percent_label.grid(row=first_row + 1, column=0, sticky="w")
    current_progress_bar['value'] = 0


def _run_download(link, filename, ydl_opts, ext, on_auth_error):
    """Runs on the background thread. Never touches widgets directly;
    every UI change goes through r.after(0, ...)."""
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([link])

        file_path = os.path.join(DOWNLOAD_DIR, f"{filename}.{ext}")
        r.after(0, _download_finished, os.path.exists(file_path))

    except DownloadError as e:
        if is_auth_error(e):
            r.after(0, on_auth_error)
        else:
            print(f"Error downloading {ext.upper()}: {e}")
            r.after(0, _download_finished, False)
    except Exception as e:
        print(f"Error downloading {ext.upper()}: {e}")
        r.after(0, _download_finished, False)


def _download_finished(was_successful):
    if was_successful:
        success()
    else:
        failed_download()


# --- MP4 LOGIC ---
def mp4_converter():
    global entry2, entry1, mp4_frame, quality_var, mp4_ok_button, mp4_back_button

    menu_frame.grid_forget()
    mp4_frame = Frame(r, bg="white")
    mp4_frame.grid(padx=20, pady=20, sticky="nsew")

    l = Label(mp4_frame, text='Enter the url', font=("Arial", 16, "bold"), bg="white", fg="black")
    l2 = Label(mp4_frame, text='Enter the file name for the video (mp4)', font=("Arial", 16, "bold"), bg="white", fg="black")
    l3 = Label(mp4_frame, text='Select quality', font=("Arial", 16, "bold"), bg="white", fg="black")
    entry1 = Entry(mp4_frame, width=30, font=("Arial", 14))
    entry2 = Entry(mp4_frame, width=30, font=("Arial", 14))

    quality_var = StringVar(value='1080p')
    quality_menu = OptionMenu(mp4_frame, quality_var, *QUALITY_OPTIONS.keys())
    quality_menu.config(font=("Arial", 14), width=15)

    mp4_back_button = Button(mp4_frame, text='back', padx=40, pady=15, bg='#6d7985', fg='white', command=firstfunction)
    mp4_ok_button = Button(mp4_frame, text='OK', padx=40, pady=15, fg='white', bg='#4285F4', font=("Arial", 14, "bold"),
                           command=mp4_download)

    _build_status_widgets(mp4_frame)

    l.grid(row=0, column=0, pady=10, sticky="w")
    entry1.grid(row=1, column=0, pady=10, sticky="ew")
    l2.grid(row=2, column=0, pady=10, sticky="w")
    entry2.grid(row=3, column=0, pady=10, sticky="ew")
    l3.grid(row=4, column=0, pady=10, sticky="w")
    quality_menu.grid(row=5, column=0, pady=10, sticky="w")
    mp4_back_button.grid(row=6, column=0, pady=20, sticky="ew")
    mp4_ok_button.grid(row=7, column=0, sticky='ew')
    current_status_label.grid(row=8, column=0, pady=(10, 0), sticky="w")


def mp4_download():
    link = entry1.get().strip()
    raw_name = entry2.get()
    filename = sanitize_filename(raw_name)
    quality_label = quality_var.get()

    if not _preflight_ok(link, filename):
        return

    _begin_download_ui(mp4_ok_button, mp4_back_button, 9, raw_name, filename)

    thread = threading.Thread(
        target=_mp4_download_worker,
        args=(link, filename, quality_label),
        daemon=True,
    )
    thread.start()


def _mp4_download_worker(link, filename, quality_label):
    ydl_opts = {
        **common_opts(),
        'format': build_mp4_format(quality_label),
        'outtmpl': os.path.join(DOWNLOAD_DIR, f'{filename}.%(ext)s'),
        'merge_output_format': 'mp4',
        'http_chunk_size': 10 * 1024 * 1024,
        'concurrent_fragment_downloads': 5,
        'socket_timeout': 10,
        'retries': 15,
        'fragment_retries': 15,
        'progress_hooks': [yt_dlp_hook],
    }
    _run_download(
        link, filename, ydl_opts, 'mp4',
        on_auth_error=lambda: auth_required_screen(link, filename, 'mp4', quality_label),
    )


# --- MP3 LOGIC ---
def mp3_converter():
    global entry3, entry4, mp3_frame, mp3_ok_button, mp3_back_button

    menu_frame.grid_forget()
    mp3_frame = Frame(r, bg="white")
    mp3_frame.grid(padx=20, pady=20, sticky="nsew")

    l = Label(mp3_frame, text='Enter the url', font=("Arial", 16, "bold"), bg="white", fg="black")
    l2 = Label(mp3_frame, text='Enter the file name for the audio (mp3)', font=("Arial", 16, "bold"), bg="white", fg="black")
    entry3 = Entry(mp3_frame, width=30, font=("Arial", 14))
    entry4 = Entry(mp3_frame, width=30, font=("Arial", 14))

    mp3_back_button = Button(mp3_frame, text='back', padx=40, pady=15, bg='#6d7985', fg='white', command=firstfunction)
    mp3_ok_button = Button(mp3_frame, text='OK', padx=40, pady=15, fg='white', bg='#4285F4', font=("Arial", 14, "bold"),
                           command=mp3_download)

    _build_status_widgets(mp3_frame)

    l.grid(row=0, column=0, pady=10, sticky="w")
    entry3.grid(row=1, column=0, pady=10, sticky="w")
    l2.grid(row=2, column=0, pady=10, sticky="w")
    entry4.grid(row=3, column=0, pady=10, sticky="ew")
    mp3_back_button.grid(row=4, column=0, pady=20, sticky="ew")
    mp3_ok_button.grid(row=5, column=0, sticky='ew')
    current_status_label.grid(row=6, column=0, pady=(10, 0), sticky="w")


def mp3_download():
    link = entry3.get().strip()
    raw_name = entry4.get()
    filename = sanitize_filename(raw_name)

    if not _preflight_ok(link, filename):
        return

    _begin_download_ui(mp3_ok_button, mp3_back_button, 7, raw_name, filename)

    thread = threading.Thread(
        target=_mp3_download_worker,
        args=(link, filename),
        daemon=True,
    )
    thread.start()


def _mp3_download_worker(link, filename):
    ydl_opts = {
        **common_opts(),
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(DOWNLOAD_DIR, f'{filename}.%(ext)s'),
        'retries': 15,
        'fragment_retries': 15,
        'progress_hooks': [yt_dlp_hook],
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    _run_download(
        link, filename, ydl_opts, 'mp3',
        on_auth_error=lambda: auth_required_screen(link, filename, 'mp3'),
    )


# --- SUCCESS/FAIL SCREENS ---
def success():
    hide_frames()
    global success_frame
    success_frame = Frame(r, bg="white")
    l = Label(success_frame, text='SUCCESSFULLY DOWNLOADED', font=("Arial", 16, "bold"), bg="white", fg="black")
    path_label = Label(success_frame, text=f"Saved in:\n{DOWNLOAD_DIR}", font=("Arial", 10), bg="white",
                       fg="#555555", justify=LEFT, wraplength=460)
    open_button = Button(success_frame, text='open downloads folder', padx=40, pady=12, fg='white', bg='#5cb85c',
                         font=("Arial", 12, "bold"), command=lambda: open_folder(DOWNLOAD_DIR))
    back_button = Button(success_frame, text='back to main menu', padx=40, pady=15, bg='#6d7985', fg='white', command=firstfunction)
    exit_button = Button(success_frame, text='exit', padx=40, pady=15, fg='white', bg='#4285F4', font=("Arial", 14, "bold"),
                         command=r.destroy)
    success_frame.grid(sticky="nsew")
    l.grid(row=0, column=0, pady=10, sticky="w")
    path_label.grid(row=1, column=0, pady=(0, 10), sticky="w")
    open_button.grid(row=2, column=0, pady=(0, 10), sticky="ew")
    back_button.grid(row=3, column=0, pady=10, sticky="ew")
    exit_button.grid(row=4, column=0, sticky='ew')


def failed_download():
    hide_frames()
    global failed_frame
    failed_frame = Frame(r, bg="white")
    failed_frame.grid(sticky="nsew")
    l = Label(failed_frame, text='FAILED', font=("Arial", 16, "bold"), bg="white", fg="black")
    back_button = Button(failed_frame, text='back', padx=40, pady=15, bg='#6d7985', fg='white', command=firstfunction)
    l.grid(row=0, column=0, pady=10, sticky="w")
    back_button.grid(row=4, column=0, pady=20, sticky="ew")


# --- STARTUP ---
init_storage()          # finds a writable folder, or shows an error and exits
firstfunction()
r.after(300, ensure_ffmpeg)   # startup check: offer the file picker right away if FFmpeg is missing
r.mainloop()