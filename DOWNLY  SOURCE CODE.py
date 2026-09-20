# IMPORTING THE REQUIRED MODULES
from tkinter import *
import yt_dlp
import os

# INITIAL TKINTER FRAME
r = Tk()

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
    l.grid(row=0, column=0, columnspan=3, pady=(20, 10), padx=10, sticky="n")

    mp3_button = Button(menu_frame, text='MP3', padx=40, pady=20, fg='white', bg='#007ACC', font=("Arial", 14, "bold"),
                        command=mp3_converter)
    mp4_button = Button(menu_frame, text='MP4', padx=40, pady=20, fg='white', bg='#5F6368', font=("Arial", 14, "bold"),
                        command=mp4_converter)
    mp3_button.grid(row=1, column=0, padx=10, pady=10)
    mp4_button.grid(row=1, column=1, padx=10, pady=10)

    r.grid_columnconfigure(0, weight=1)
    r.grid_columnconfigure(1, weight=1)
    r.grid_rowconfigure(1, weight=1)

# Quality options shown to the user, mapped to a max height.
# "Best available" means no height cap at all (true best stream yt-dlp can find).
QUALITY_OPTIONS = {
    '1080p': 1080,
    '720p': 720,
    '480p': 480,
    'Best available': None,
}

def build_mp4_format(quality_label):
    """Builds the yt-dlp format selector string for the chosen quality."""
    max_height = QUALITY_OPTIONS.get(quality_label)

    if max_height is None:
        # No cap — grab the actual best video+audio yt-dlp can find.
        return (
            'bestvideo[ext=mp4]+bestaudio[ext=m4a]/'
            'best[ext=mp4]/'
            'best'
        )

    # Capped at the requested height, with a fallback chain in case that
    # exact combo isn't available for a given video.
    return (
        f'bestvideo[height<={max_height}][ext=mp4]+bestaudio[ext=m4a]/'
        f'best[height<={max_height}][ext=mp4]/'
        'best'
    )

def mp4_converter():
    global entry2
    global entry1
    global mp4_frame
    global quality_var
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

    back_button = Button(mp4_frame, text='back', padx=40, pady=15, bg='#6d7985', fg='white', command=firstfunction)
    ok_button = Button(mp4_frame, text='OK', padx=40, pady=15, fg='white', bg='#4285F4', font=("Arial", 14, "bold"),
                command=mp4_download)

    l.grid(row=0, column=0, pady=10, sticky="w")
    entry1.grid(row=1, column=0, pady=10, sticky="ew")
    l2.grid(row=2, column=0, pady=10, sticky="w")
    entry2.grid(row=3, column=0, pady=10, sticky="ew")
    l3.grid(row=4, column=0, pady=10, sticky="w")
    quality_menu.grid(row=5, column=0, pady=10, sticky="w")
    back_button.grid(row=6, column=0, pady=20, sticky="ew")
    ok_button.grid(row=7, column=0, sticky='ew')

def mp4_download():
    link = entry1.get()
    filename = entry2.get()
    quality_label = quality_var.get()

    ydl_opts = {
        'format': build_mp4_format(quality_label),
        'outtmpl': f'Downly downloads/{filename}.%(ext)s',
        'merge_output_format': 'mp4',
        'ffmpeg_location': r'C:\Users\HP\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.1-full_build\bin',

        # Real YouTube login cookies (SID/APISID/LOGIN_INFO etc.),
        # exported for youtube.com only — never the whole browser.
        'cookiefile': r'C:\Users\HP\Downloads\youtube_cookies.txt',

        # Allows yt-dlp to fetch the JS challenge solver component
        # required to decode YouTube's obfuscated media URLs.
        'remote_components': ['ejs:github'],

        # Splits long continuous streams into range-request chunks
        # so a single connection doesn't get progressively throttled.
        'http_chunk_size': 10 * 1024 * 1024,

        # Fetches multiple DASH fragments in parallel instead of
        # yt-dlp's slow default sequential fragment downloading.
        'concurrent_fragment_downloads': 5,

        'socket_timeout': 10,
        'retries': 15,
        'fragment_retries': 15,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([link])

        file_path = f"Downly downloads/{filename}.mp4"
        if os.path.exists(file_path):
            success()
        else:
            failed_download()
    except Exception as e:
        print(f"Error downloading MP4: {e}")
        failed_download()

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

def mp3_converter():
    global entry3
    global entry4
    global mp3_frame
    menu_frame.grid_forget()
    mp3_frame = Frame(r, bg="white")
    mp3_frame.grid(padx=20, pady=20, sticky="nsew")
    l = Label(mp3_frame, text='Enter the url', font=("Arial", 16, "bold"), bg="white", fg="black")
    l2 = Label(mp3_frame, text='Enter the file name for the audio (mp3)', font=("Arial", 16, "bold"), bg="white", fg="black")
    entry3 = Entry(mp3_frame, width=30, font=("Arial", 14))
    entry4 = Entry(mp3_frame, width=30, font=("Arial", 14))
    back_button = Button(mp3_frame, text='back', padx=40, pady=15, bg='#6d7985', fg='white', command=firstfunction)
    ok_button = Button(mp3_frame, text='OK', padx=40, pady=15, fg='white', bg='#4285F4', font=("Arial", 14, "bold"),
                command=mp3_download)

    l.grid(row=0, column=0, pady=10, sticky="w")
    entry3.grid(row=1, column=0, pady=10, sticky="w")
    l2.grid(row=2, column=0, pady=10, sticky="w")
    entry4.grid(row=3, column=0, pady=10, sticky="ew")
    back_button.grid(row=4, column=0, pady=20, sticky="ew")
    ok_button.grid(row=5, column=0, sticky='ew')

def mp3_download():
    link = entry3.get()
    filename = entry4.get()

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'Downly downloads/{filename}.%(ext)s',
        'ffmpeg_location': r'C:\Users\HP\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.1-full_build\bin',
        'cookiefile': r'C:\Users\HP\Downloads\youtube_cookies.txt',
        'remote_components': ['ejs:github'],
        'retries': 15,
        'fragment_retries': 15,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([link])

        file_path = f"Downly downloads/{filename}.mp3"
        if os.path.exists(file_path):
            success()
        else:
            failed_download()
    except Exception as e:
        print(f"Error downloading MP3: {e}")
        failed_download()

# Ensure the download directory exists before the app starts
if not os.path.exists("Downly downloads"):
    os.makedirs("Downly downloads")

firstfunction()
r.mainloop()