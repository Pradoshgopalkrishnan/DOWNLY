# IMPORTING THE REQUIRED MODULES
from tkinter import *
from tkinter import ttk  
import yt_dlp
import os
import sys
import shutil
import threading




if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DOWNLOAD_DIR = os.path.join(BASE_DIR, "Downly downloads")


def find_ffmpeg():
    """Look for ffmpeg in ./ffmpeg (or ./ffmpeg/bin) first, then on the system PATH.
    Returns the folder containing ffmpeg, or None if it isn't found."""
    search_path = os.pathsep.join([
        os.path.join(BASE_DIR, "ffmpeg"),
        os.path.join(BASE_DIR, "ffmpeg", "bin"),
        os.environ.get("PATH", ""),
    ])
    exe = shutil.which("ffmpeg", path=search_path)
    return os.path.dirname(exe) if exe else None


def find_cookies():
    """Use the DOWNLY_COOKIES environment variable, or youtube_cookies.txt
    next to the app, if present. Returns None if neither exists."""
    env_path = os.environ.get("DOWNLY_COOKIES")
    if env_path and os.path.isfile(env_path):
        return env_path
    local = os.path.join(BASE_DIR, "youtube_cookies.txt")
    return local if os.path.isfile(local) else None


def common_opts():
    """Options shared by both MP3 and MP4 downloads."""
    opts = {'remote_components': ['ejs:github']}
    ffmpeg_dir = find_ffmpeg()
    if ffmpeg_dir:
        opts['ffmpeg_location'] = ffmpeg_dir
    cookies = find_cookies()
    if cookies:
        opts['cookiefile'] = cookies
    return opts


# INITIAL TKINTER FRAME
r = Tk()

# Global variables for the current active UI elements
current_progress_bar = None
current_percent_label = None
current_status_label = None


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
            # Tkinter isn't thread-safe, so we use r.after to schedule the update on the main UI thread
            r.after(0, lambda: _update_progress_ui(percent_float, percent_str))

    elif d['status'] == 'finished':
        r.after(0, lambda: current_status_label.config(text="Processing and merging files... Please wait."))


def _update_progress_ui(val, text):
    """Safely updates the progress bar and label from the main thread."""
    if current_progress_bar and current_percent_label:
        current_progress_bar['value'] = val
        current_percent_label.config(text=text)


# --- MP4 LOGIC ---
def mp4_converter():
    global entry2, entry1, mp4_frame, quality_var, mp4_ok_button, mp4_back_button
    global current_progress_bar, current_percent_label, current_status_label

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

    current_status_label = Label(mp4_frame, text='', font=("Arial", 12), bg="white", fg="#555555")
    current_progress_bar = ttk.Progressbar(mp4_frame, orient=HORIZONTAL, length=300, mode='determinate')
    current_percent_label = Label(mp4_frame, text="0.0%", font=("Arial", 12, "bold"), bg="white", fg="#4285F4")

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
    link = entry1.get()
    filename = entry2.get()
    quality_label = quality_var.get()

    mp4_ok_button.config(state=DISABLED)
    mp4_back_button.grid_remove()
    current_status_label.config(text='Downloading...')

    # Show progress elements
    current_progress_bar.grid(row=9, column=0, pady=(10, 5), sticky="ew")
    current_percent_label.grid(row=10, column=0, sticky="w")
    current_progress_bar['value'] = 0

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
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([link])

        file_path = os.path.join(DOWNLOAD_DIR, f"{filename}.mp4")
        if os.path.exists(file_path):
            r.after(0, _mp4_download_finished, True)
        else:
            r.after(0, _mp4_download_finished, False)
    except Exception as e:
        print(f"Error downloading MP4: {e}")
        r.after(0, _mp4_download_finished, False)


def _mp4_download_finished(was_successful):
    if was_successful:
        success()
    else:
        failed_download()


# --- MP3 LOGIC ---
def mp3_converter():
    global entry3, entry4, mp3_frame, mp3_ok_button, mp3_back_button
    global current_progress_bar, current_percent_label, current_status_label

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

    current_status_label = Label(mp3_frame, text='', font=("Arial", 12), bg="white", fg="#555555")
    current_progress_bar = ttk.Progressbar(mp3_frame, orient=HORIZONTAL, length=300, mode='determinate')
    current_percent_label = Label(mp3_frame, text="0.0%", font=("Arial", 12, "bold"), bg="white", fg="#4285F4")

    l.grid(row=0, column=0, pady=10, sticky="w")
    entry3.grid(row=1, column=0, pady=10, sticky="w")
    l2.grid(row=2, column=0, pady=10, sticky="w")
    entry4.grid(row=3, column=0, pady=10, sticky="ew")
    mp3_back_button.grid(row=4, column=0, pady=20, sticky="ew")
    mp3_ok_button.grid(row=5, column=0, sticky='ew')
    current_status_label.grid(row=6, column=0, pady=(10, 0), sticky="w")


def mp3_download():
    link = entry3.get()
    filename = entry4.get()

    mp3_ok_button.config(state=DISABLED)
    mp3_back_button.grid_remove()
    current_status_label.config(text='Downloading...')

    # Show progress elements
    current_progress_bar.grid(row=7, column=0, pady=(10, 5), sticky="ew")
    current_percent_label.grid(row=8, column=0, sticky="w")
    current_progress_bar['value'] = 0

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

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([link])

        file_path = os.path.join(DOWNLOAD_DIR, f"{filename}.mp3")
        if os.path.exists(file_path):
            r.after(0, _mp3_download_finished, True)
        else:
            r.after(0, _mp3_download_finished, False)
    except Exception as e:
        print(f"Error downloading MP3: {e}")
        r.after(0, _mp3_download_finished, False)


def _mp3_download_finished(was_successful):
    if was_successful:
        success()
    else:
        failed_download()


# --- SUCCESS/FAIL SCREENS ---
def success():
    hide_frames()
    global success_frame
    success_frame = Frame(r, bg="white")
    l = Label(success_frame, text='SUCCESSFULLY DOWNLOADED', font=("Arial", 16, "bold"), bg="white", fg="black")
    back_button = Button(success_frame, text='back to main menu', padx=40, pady=15, bg='#6d7985', fg='white', command=firstfunction)
    exit_button = Button(success_frame, text='exit', padx=40, pady=15, fg='white', bg='#4285F4', font=("Arial", 14, "bold"),
                         command=r.destroy)
    success_frame.grid(sticky="nsew")
    l.grid(row=0, column=0, pady=10, sticky="w")
    back_button.grid(row=4, column=0, pady=20, sticky="ew")
    exit_button.grid(row=5, column=0, sticky='ew')


def failed_download():
    hide_frames()
    global failed_frame
    failed_frame = Frame(r, bg="white")
    failed_frame.grid(sticky="nsew")
    l = Label(failed_frame, text='FAILED', font=("Arial", 16, "bold"), bg="white", fg="black")
    back_button = Button(failed_frame, text='back', padx=40, pady=15, bg='#6d7985', fg='white', command=firstfunction)
    l.grid(row=0, column=0, pady=10, sticky="w")
    back_button.grid(row=4, column=0, pady=20, sticky="ew")


# Ensure the download directory exists before the app starts
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

firstfunction()
r.mainloop()