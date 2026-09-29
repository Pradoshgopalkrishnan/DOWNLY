# Downly — YouTube MP3 & MP4 Downloader

A desktop application built with Python and Tkinter for downloading YouTube videos as MP4 or extracting audio as MP3. Uses `yt-dlp` for extraction and `FFmpeg` for muxing/audio conversion.

## Features

- Download YouTube videos in MP4, with a quality picker (1080p, 720p, 480p, or best available)
- Extract audio as MP3 (192kbps)
- Tkinter GUI with basic error handling
- Chunked, concurrent downloads to avoid connection-level throttling
- Output saved to `Downly downloads/`

## Requirements

### Python packages

```
pip install -r requirements.txt
```

### External dependencies (not installed via pip)

FFmpeg — required for muxing video/audio streams and for MP3 extraction. Update `ffmpeg_location` in `1.py` to point at your local FFmpeg `bin` directory.

A JavaScript runtime — YouTube obfuscates media URLs with JS that yt-dlp needs to execute. [Deno](https://deno.com/) is recommended:

```
winget install DenoLand.Deno
```

YouTube cookies file — recommended to avoid bot-detection and rate-limiting. Export cookies scoped to `youtube.com` only (not a whole-browser export) using an extension such as "Get cookies.txt LOCALLY" while logged into YouTube. Point `cookiefile` in `1.py` to the exported file's path.

Do not commit your cookies file. It contains live session tokens equivalent to a password. `.gitignore` in this repo excludes `*cookies*.txt` by default.

## Project structure

```
Downly/
├── 1.py
├── requirements.txt
├── .gitignore
└── Downly downloads/   (auto-created, git-ignored)
```

## How it works

### MP4

1. User provides a URL, output filename, and picks a quality (1080p, 720p, 480p, or best available)
2. yt-dlp fetches video capped at the selected height (or uncapped for "best available") and audio streams separately
3. FFmpeg merges them into a single `.mp4` in `Downly downloads/`

### MP3

1. User provides a URL and output filename
2. yt-dlp extracts the best available audio stream
3. FFmpeg converts it to `.mp3` in `Downly downloads/`

## Running

```
python DOWNLY  SOURCE CODE.py
```

Launches the GUI with MP3/MP4 selection on the main menu.

## Notes

- `Downly downloads/` is created automatically if it doesn't exist
- Avoid special characters in filenames
- YouTube's anti-automation measures change frequently — keep dependencies current:

```
pip install -U yt-dlp yt-dlp-ejs
```

## License

Free to use for personal, educational, and non-commercial purposes.