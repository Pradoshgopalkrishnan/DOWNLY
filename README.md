
# **Downly – YouTube MP3 & MP4 Downloader**

Downly is a simple, user-friendly desktop application built using **Python** and **Tkinter** that allows you to download YouTube videos in **MP4** format or extract **MP3** audio with ease.
The application uses **pytubefix** for fetching YouTube content and **moviepy** for audio conversion.

---

## 🚀 **Features**

* Download YouTube videos in **high-resolution MP4**
* Convert YouTube videos to **MP3 audio**
* Simple & clean GUI using Tkinter
* Error-handling for invalid downloads
* Organized output folder:
  → All files saved into **Downly downloads/**

---

## 📦 **Requirements**

Make sure you have the following packages installed:

```
pip install pytubefix
pip install moviepy
```

Tkinter comes preinstalled with most Python distributions.

---

## 📁 **Project Structure**

```
Downly/
│
├── DOWNLY SOURCE CODE.py
├── Downly downloads/   (auto-created)
```

---

## 🛠️ **How It Works**

### **MP4 Download**

1. User enters a YouTube link
2. Provides desired file name
3. Downly fetches the video in highest resolution
4. Saves to *Downly downloads/* with `.mp4` extension

### **MP3 Download**

1. User enters a YouTube link
2. Provides desired MP3 file name
3. Extracts audio from the video using moviepy
4. Saves audio into *Downly downloads/* with `.mp3`

---

## ▶️ **Running the Application**

Run the program:

```
python "DOWNLY SOURCE CODE.py"
```

The GUI will launch with the main menu where you can select:

* **MP3 Downloader**
* **MP4 Downloader**

---

## 📸 **Screens & Navigation**

* Main Menu → MP3/MP4 selection
* Input screen → URL + File name
* Success / Failure Screen
* Back to menu or Exit option

---

## ⚠️ **Important Notes**

* The folder **Downly downloads/** must exist in the same directory
  (or will be created automatically by the script).
* You must have a stable internet connection for downloading.
* Avoid using special characters in file names.

---

## 📜 **License**

This project is free to use for personal, educational, and non-commercial purposes.

---

