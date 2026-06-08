#IMPORTING THE REQUIRED MODULES
from tkinter import *
from pytubefix import YouTube
from moviepy.audio.io.AudioFileClip import AudioFileClip
import os

#INITIAL TKINTER FRAME
r = Tk()

#FIRST FRAME/MENU FRAME
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

def mp4_converter():
    global entry2
    global entry1
    global mp4_frame
    menu_frame.grid_forget()
    mp4_frame = Frame(r, bg="white")
    mp4_frame.grid(padx=20, pady=20, sticky="nsew")
    l = Label(mp4_frame, text='Enter the url', font=("Arial", 16, "bold"), bg="white", fg="black")
    l2 = Label(mp4_frame, text='Enter the file name for the video (mp4)', font=("Arial", 16, "bold"), bg="white", fg="black")
    entry1 = Entry(mp4_frame, width=30, font=("Arial", 14))
    entry2 = Entry(mp4_frame, width=30, font=("Arial", 14))
    back_button = Button(mp4_frame, text='back', padx=40, pady=15, bg='#6d7985', fg='white', command=firstfunction)
    ok_button = Button(mp4_frame, text='OK', padx=40, pady=15, fg='white', bg='#4285F4', font=("Arial", 14, "bold"),
                command=mp4_download)
    
    l.grid(row=0, column=0, pady=10, sticky="w")
    entry1.grid(row=1, column=0, pady=10, sticky="ew")
    l2.grid(row=2, column=0, pady=10, sticky="w")
    entry2.grid(row=3, column=0, pady=10, sticky="ew")
    back_button.grid(row=4, column=0, pady=20, sticky="ew")
    ok_button.grid(row=5, column=0, sticky='ew')

def mp4_download():
    link = entry1.get()
    yt = YouTube(link)
    stream = yt.streams.get_highest_resolution()
    filename = entry2.get() + ".mp4"
    stream.download(output_path="Downly downloads/", filename=filename)
    file_path = "Downly downloads/" + filename

    if os.path.exists(file_path):
        success()
    else:
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
    entry3.grid(row=1, column=0, pady=10, sticky="ew")
    l2.grid(row=2, column=0, pady=10, sticky="w")
    entry4.grid(row=3, column=0, pady=10, sticky="ew")
    back_button.grid(row=4, column=0, pady=20, sticky="ew")
    ok_button.grid(row=5, column=0, sticky='ew')

def mp3_download():
    link = entry3.get()
    yt = YouTube(link)
    stream = yt.streams.filter(only_audio=True).first()
    filename = entry4.get() + ".mp3"
    stream.download(output_path="Downly downloads/", filename=filename)
    file_path = "Downly downloads/" + filename
    if os.path.exists(file_path):
        success()
    else:
        failed_download()

firstfunction()
r.mainloop()
