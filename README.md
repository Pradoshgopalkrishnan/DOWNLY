Downly — YouTube MP3 & MP4 Downloader
A desktop application built with Python and Tkinter for downloading YouTube videos as MP4 or extracting audio as MP3. Uses yt-dlp for extraction and FFmpeg for muxing/audio conversion.

Features
Download YouTube videos in MP4, with a quality picker (1080p, 720p, 480p, or best available)

Extract audio as MP3 (192kbps)

Tkinter GUI with interactive error handling and authentication-recovery screens

Chunked, concurrent downloads to avoid connection-level throttling

Automatic FFmpeg discovery with a GUI fallback file picker

Automatic filename sanitization

Output saved to Downly downloads/

Requirements
Python packages
pip install -r requirements.txt
External dependencies (not installed via pip)
FFmpeg — required for muxing video/audio streams and for MP3 extraction. Downly will search your system automatically. If not found, a popup will ask you to select ffmpeg.exe and will save its location permanently.

A JavaScript runtime — YouTube obfuscates media URLs with JS that yt-dlp needs to execute. Deno is recommended:

winget install DenoLand.Deno
YouTube cookies file — recommended to avoid bot-detection and required for age-restricted or members-only videos. Export cookies scoped to youtube.com only (not a whole-browser export) using an extension such as "Get cookies.txt LOCALLY" while logged into YouTube. If YouTube blocks a download, Downly will prompt you to select this file and automatically save a copy to retry.

Do not commit your cookies file. It contains live session tokens equivalent to a password. .gitignore in this repo excludes *cookies*.txt by default.

Project structure
Downly/
├── downly.py
├── requirements.txt
├── .gitignore
├── downly_settings.json   (auto-created, git-ignored)
├── youtube_cookies.txt    (auto-created, git-ignored)
└── Downly downloads/      (auto-created, git-ignored)
How it works
MP4
User provides a URL, output filename, and picks a quality (1080p, 720p, 480p, or best available)

yt-dlp fetches video capped at the selected height (or uncapped for "best available") and audio streams separately

FFmpeg merges them into a single .mp4 in Downly downloads/

MP3
User provides a URL and output filename

yt-dlp extracts the best available audio stream

FFmpeg converts it to .mp3 in Downly downloads/

Running
python downly.py
Launches the GUI with MP3/MP4 selection on the main menu.

Notes
Downly downloads/ is created automatically. If the app folder is read-only, it falls back to ~/Downly.

Filenames are automatically sanitized to remove illegal system characters.

YouTube's anti-automation measures change frequently — keep dependencies current:

pip install -U yt-dlp yt-dlp-ejs
License
Free to use for personal, educational, and non-commercial purposes.