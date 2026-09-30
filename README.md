# Downly

A desktop app for downloading YouTube videos as MP4 or extracting the audio as MP3. Built with Python and Tkinter. It uses [yt-dlp](https://github.com/yt-dlp/yt-dlp) to fetch the media and [FFmpeg](https://ffmpeg.org/) to merge video and audio and to convert to MP3.

Educational use only. Respect YouTube's Terms of Service and the copyright of the content you download. You are responsible for what you download.

## Features

- MP4 download with a quality picker: 1080p, 720p, 480p, or best available
- MP3 extraction at 192 kbps
- Progress bar with percentage, running in a background thread so the window stays responsive
- Chunked downloads with concurrent fragments (MP4) to avoid connection-level throttling
- Automatic FFmpeg discovery, with a file picker if it can't be found (the choice is remembered)
- Sign-in recovery screen: if YouTube blocks a download, Downly asks for a cookies file and retries
- Filename sanitizing, so illegal characters can't break the save path
- Startup check that tells you when `yt-dlp` or `yt-dlp-ejs` has a newer version
- Falls back to `~/Downly` if the app folder is read-only

## Requirements

- Python 3 with Tkinter (developed and tested on Python 3.13 on Windows; recent yt-dlp releases need a fairly recent Python)
- Python packages: `yt-dlp` and `yt-dlp-ejs` (listed in `requirements.txt`)
- FFmpeg, including `ffprobe` (needed for merging and MP3 conversion)
- A JavaScript runtime, [Deno](https://deno.com/) (YouTube hides media URLs behind JavaScript that yt-dlp has to run)
- An internet connection. yt-dlp is configured to fetch its JavaScript solver component from GitHub (`remote_components: ejs:github`), so downloads need GitHub to be reachable as well as YouTube.

Downly has been tested on Windows only. The folder-opening code has macOS and Linux branches, but those are untested.

## Setup

1. Get the code:

   ```bash
   git clone https://github.com/Pradoshgopalkrishnan/DOWNLY.git
   cd DOWNLY
   ```

2. Install the Python packages:

   ```bash
   pip install -r requirements.txt
   ```

3. Install FFmpeg and Deno (on Windows, with winget):

   ```bash
   winget install Gyan.FFmpeg
   winget install DenoLand.Deno
   ```

   Open a new terminal afterwards so the updated PATH is picked up.

4. Run the app:

   ```bash
   python downly.py
   ```

## Usage

**MP4**

1. Click MP4 on the main menu.
2. Paste the video URL (it must start with `http://` or `https://`).
3. Type a filename (without the extension).
4. Pick a quality and click OK.

**MP3**

1. Click MP3 on the main menu.
2. Paste the video URL and type a filename.
3. Click OK.

When the download finishes, the success screen shows the folder and has a button to open it. Files are saved in `Downly downloads/`.

About the quality options: 1080p, 720p and 480p set a maximum height. "Best available" has no limit, so it can give you 4K when the video offers it in a format Downly accepts. What you get depends on the video. Very high resolutions may use AV1, which some players can only play with an AV1 decoder installed.

## FFmpeg

Downly looks for FFmpeg in this order:

1. The folder you picked earlier (saved in `downly_settings.json`)
2. `ffmpeg/` or `ffmpeg/bin/` next to the app
3. Your system PATH

If none of these works, a popup asks you to locate `ffmpeg.exe`. The folder you pick is saved, so you only do this once. Keep `ffprobe.exe` in the same folder; MP3 conversion may fail without it.

## Sign-in and cookies

Most public videos download with no cookies at all, and Downly works without a cookies file.

Sometimes YouTube asks for a signed-in session (bot check, age-restricted, members-only or private videos, some 403 errors). When that happens, Downly shows a "YouTube Blocked the Download" screen. To continue:

1. Open Google Chrome and install the extension "Get cookies.txt LOCALLY".
2. Go to `youtube.com` while logged in.
3. Use the extension to export the cookies for `youtube.com` only.
4. Click "Select cookies file" in Downly and choose the exported file.

Downly saves a copy as `youtube_cookies.txt` next to the app and retries the download. From then on, the file is used automatically for every download, including after a restart. If it expires, Downly tells you on the next block screen and you can select a fresh export.

**Treat the cookies file like a password.** It contains live session tokens for your Google account.

- Export cookies for `youtube.com` only, never a whole-browser export.
- Never share the file or commit it. `.gitignore` excludes `*cookies*.txt`.
- Downly copies the file as it is; it does not filter out other sites' cookies.

## Files and folders

```
DOWNLY/
├── downly.py               the app
├── requirements.txt
├── README.md
├── LICENSE
├── .gitignore
├── downly_settings.json    created automatically (FFmpeg folder), git-ignored
├── youtube_cookies.txt     created if you import cookies, git-ignored
└── Downly downloads/       created automatically, git-ignored
```

Downly stores these next to the app. If that folder is read-only, it uses `~/Downly` instead.

## How it works

- The UI runs on the main thread. Each download runs on a background thread, and every UI update goes through Tkinter's `after()` so the window stays safe and responsive.
- **MP4:** yt-dlp downloads the video and audio streams separately, using 10 MB range requests and 5 concurrent fragments, then FFmpeg merges them into one `.mp4`.
- **MP3:** yt-dlp downloads the best audio stream and FFmpeg converts it to `.mp3` at 192 kbps.
- **Errors:** sign-in problems (bot check, age restriction, private or members-only video, HTTP 401/403) open the cookie screen. Other failures show a FAILED screen.
- **Updates:** on launch, a background check compares your installed `yt-dlp` and `yt-dlp-ejs` with the latest versions on PyPI and shows a notice if either is behind. If you are offline, nothing is shown.

## Known limitations

- Paste a link to a single video. Playlist links (URLs containing `&list=`) are not handled specially and may download more than you expect.
- Use a new filename each time. If a file with that name already exists, yt-dlp may skip the download and Downly can still report success.
- There is no cancel button.
- The FAILED screen doesn't show the reason. The details are printed in the terminal or console you launched Downly from.
- A 403 error is treated as a sign-in problem, but it can also come from an outdated yt-dlp or a blocked network.
- Windows only has been tested.

## Troubleshooting

**FAILED, or "Only images are available" / "n challenge solving failed"**
Check that Deno is installed (`deno --version`), that you have internet access to GitHub, and that yt-dlp is current (`pip install -U yt-dlp yt-dlp-ejs`).

**FFmpeg popup keeps appearing**
Select the `ffmpeg.exe` file itself (not the folder). Make sure `ffprobe.exe` is next to it.

**The cookie screen keeps appearing after you import a file**
The export is probably expired or not logged in. Log into YouTube in Chrome, export `youtube.com` cookies again, and select the new file.

**Downloads are slow or return HTTP 429**
YouTube is rate-limiting your connection. Wait a while before retrying. Cookies do not fix rate limiting.

**A 4K file won't play**
It may be AV1. Install an AV1 decoder or use a player such as VLC or mpv.

## Keeping it working

YouTube changes often, and yt-dlp usually needs a matching update. Keep both packages current:

```bash
pip install -U yt-dlp yt-dlp-ejs
```

## License

Released under the MIT License. See the [LICENSE](LICENSE) file.