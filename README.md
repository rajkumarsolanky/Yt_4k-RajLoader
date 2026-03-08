# ⚡ YT 4K Rajloader (Flask & yt-dlp)

A modern, sleek, and user-friendly YouTube video downloader that can download videos up to **4K (2160p)**.
This tool is built using **Python, Flask, and `yt-dlp`**, and uses **Server-Sent Events (SSE)** for real-time progress tracking.

---

## 🚀 Features

* **High Resolution Support:** Download videos in **720p, 1080p (MP4)** and **1440p, 2160p (WebM)** formats.
* **Real-time Progress:** View **speed, ETA, percentage, and merging status** live in the GUI.
* **Smart Format Selection:** Automatically selects **H.264 for maximum compatibility up to 1080p**, and **VP9 for best quality above that**.
* **Modern UI:** A **dark-themed, responsive dashboard** that provides a smooth **“No CMD” experience**.
* **One-Click Folder Access:** Open the download folder directly from the browser.
* **Robust Backend:** Powered by **`yt-dlp` and `FFmpeg`** for fast downloading and reliable audio-video merging.

---

## 🛠️ Requirements

1. **Python 3.x**
2. **FFmpeg:** Required for merging video and audio files.

Download FFmpeg:
[https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)

After downloading, update the FFmpeg path in your script.

---

## ⚙️ Setup Guide

### 1. Install Dependencies

```bash
pip install flask yt-dlp
```

### 2. Configure FFmpeg Path

Update the `FFMPEG_PATH` variable in your script:

```python
FFMPEG_PATH = r"C:\path\to\your\ffmpeg.exe"
```

### 3. Run the Application

```bash
python app.py
```

The app will automatically open in your default browser at:

```
http://localhost:5000
```

---

## 🖥️ Screenshots / UI Guide

* **URL Paste:** Button to quickly paste the video URL from the clipboard.
* **Quality Grid:** Select the desired resolution (Default: **1440p**).
* **Progress Bar:** Displays live download status once the download starts.

---

## 📂 Download Path

Default download location:

```
C:\Users\<Your_User>\Downloads\YT_4K
```

---

## 🛠️ Built With

* **Python** – Core Logic
* **Flask** – Web Framework
* **yt-dlp** – Powerful YouTube backend
* **JavaScript (Vanilla)** – Frontend interactivity
* **CSS3** – Custom dark neon UI

---

## 📜 License

This project is created for **educational purposes**.
Please respect the Terms of Service of YouTube when using this tool.

---

**Made with ❤️ by Raj Kumar Solanky**

---

