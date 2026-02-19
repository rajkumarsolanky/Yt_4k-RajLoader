
# ⚡ YT 4K Rajloader (Flask & yt-dlp)

Ek modern, sleek aur user-friendly YouTube video downloader jo **4K (2160p)** tak ki videos download kar sakta hai. Yeh tool Python, Flask aur `yt-dlp` ka use karta hai, jisme real-time progress tracking ke liye **Server-Sent Events (SSE)** ka istemal kiya gaya hai.

---

## 🚀 Features

- **High Resolution Support:** 720p, 1080p (MP4) aur 1440p, 2160p (WebM) formats.
- **Real-time Progress:** GUI par speed, ETA, percentage aur merging status live dekhein.
- **Smart Format Selection:** 1080p tak maximum compatibility (H.264) aur usse upar best quality (VP9) ka automatic selection.
- **Modern UI:** Dark-themed, responsive dashboard jo "No CMD" experience deta hai.
- **One-Click Folder Access:** Seedhe browser se hi download folder open karne ka option.
- **Robust Backend:** `yt-dlp` aur `FFmpeg` ki power se fast downloading aur error-free merging.

---

## 🛠️ Requirements

1. **Python 3.x**
2. **FFmpeg:** Videos aur Audio ko merge karne ke liye system mein FFmpeg hona zaroori hai.
   - [FFmpeg Download karein](https://ffmpeg.org/download.html) aur iska path script mein update karein.
     

### 2. Dependencies Install Karein

```bash
pip install flask yt-dlp

```

### 3. Path Configuration

Apni script mein `FFMPEG_PATH` variable ko apne system ke FFmpeg path se badal dein:

```python
FFMPEG_PATH = r"C:\path\to\your\ffmpeg.exe"

```

### 4. App Run Karein

```bash
python app.py

```

App automatically aapke default browser mein `http://localhost:5000` par open ho jayegi.

---

## 🖥️ Screenshots / UI Guide

* **URL Paste:** Clipboard se URL paste karne ke liye button.
* **Quality Grid:** Resolution select karein (Default: 1440p).
* **Progress Bar:** Download start hote hi live status update.

---

## 📂 Download Path

Default download location:
`C:\Users\<Your_User>\Downloads\YT_4K`

---

## 🛠️ Built With

* **Python** - Core Logic
* **Flask** - Web Framework
* **yt-dlp** - Powerful YouTube backend
* **JavaScript (Vanilla)** - Frontend interactivity
* **CSS3** - Custom Dark Neon UI

---

## 📜 License

Yahi project "Educational Purposes" ke liye banaya gaya hai. YouTube ke Terms of Service ka samman karein.

---

**Made with ❤️ by [Aapka Naam]**

```

---

### **Kuch Tips GitHub ke liye:**
1. **Repository Name:** Iska naam `yt-4k-rajloader-web` ya `ultimate-yt-dlp-gui` rakh sakte hain.
2. **FFmpeg Disclaimer:** README mein yeh zaroor batayein ki FFmpeg ke bina 1080p se upar ki videos merge nahi hongi (sirf video aayegi audio nahi, ya process fail ho jayega).
3. **Tags:** Repository mein `python`, `flask`, `yt-dlp`, `youtube-downloader`, aur `4k-video` jaise tags zaroor add karein.

```
