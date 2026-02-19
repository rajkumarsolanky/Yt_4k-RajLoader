import os
import re
import threading
import webbrowser
from flask import Flask, request, jsonify, Response
import yt_dlp

app = Flask(__name__)

# ── Config ─────────────────────────────────────────────────────────────────────
DOWNLOAD_FOLDER = os.path.join(os.path.expanduser("~"), "Downloads", "YT_4K")
# Use "ffmpeg" if it's in your System PATH (recommended).
FFMPEG_PATH = r"C:\Users\rajku\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.0.1-full_build\bin\ffmpeg.exe"


os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# ── Shared progress state ───────────────────────────────────────────────────────
progress_data = {
    "status": "idle", "percent": 0,
    "speed": "", "eta": "", "filename": "", "error": "", "fmt": ""
}

# ── ANSI cleaner ───────────────────────────────────────────────────────────────
def clean_ansi(text: str) -> str:
    return re.sub(r'\x1b\[[0-9;]*m', '', text)

# ── Progress hook ──────────────────────────────────────────────────────────────
def ydl_progress_hook(d):
    status = d.get("status", "")

    if status == "downloading":
        downloaded = d.get("downloaded_bytes") or 0
        total      = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
        if total > 0:
            pct = round((downloaded / total) * 100, 1)
        else:
            raw = clean_ansi(d.get("_percent_str", "0%")).strip().replace("%", "")
            try:
                pct = float(raw)
            except ValueError:
                pct = 0

        speed = clean_ansi(d.get("_speed_str", "")).strip()
        if not speed or speed in ("Unknown B/s", ""):
            spd_bytes = d.get("speed") or 0
            speed = f"{spd_bytes/1024/1024:.1f} MiB/s" if spd_bytes else "—"

        eta = clean_ansi(d.get("_eta_str", "")).strip()
        if not eta or eta == "Unknown":
            eta_sec = d.get("eta") or 0
            if eta_sec:
                m, s = divmod(int(eta_sec), 60)
                eta = f"{m}m {s}s" if m else f"{s}s"
            else:
                eta = "—"

        filename = os.path.basename(d.get("filename", ""))
        progress_data.update({
            "status":   "downloading",
            "percent":  pct,
            "speed":    speed,
            "eta":      eta,
            "filename": filename,
            "error":    ""
        })

    elif status == "finished":
        progress_data.update({
            "status": "merging", "percent": 99,
            "speed": "", "eta": "Merging…",
            "filename": os.path.basename(d.get("filename", ""))
        })

    elif status == "error":
        progress_data.update({
            "status": "error",
            "error": str(d.get("error", "Unknown error"))
        })

# ── Download logic ─────────────────────────────────────────────────────────────
def run_download(url: str, quality: str):
    progress_data.update({
        "status": "starting", "percent": 0,
        "speed": "", "eta": "", "filename": "", "error": ""
    })

    q = int(quality)

    if q <= 1080:
        # 720p / 1080p → MP4  (H.264 + AAC, maximum compatibility)
        fmt = (
            f"bestvideo[height<={q}][ext=mp4][vcodec^=avc]+bestaudio[ext=m4a]/"
            f"bestvideo[height<={q}][ext=mp4]+bestaudio[ext=m4a]/"
            f"best[height<={q}][ext=mp4]"
        )
        merge_format = "mp4"
        fmt_label    = "MP4"
    else:
        # 1440p / 2160p → WebM  (VP9 + Opus, best quality/size ratio)
        fmt = (
            f"bestvideo[height<={q}][ext=webm]+bestaudio[ext=webm]/"
            f"bestvideo[height<={q}]+bestaudio/"
            f"best[height<={q}]"
        )
        merge_format = "webm"
        fmt_label    = "WebM"

    progress_data["fmt"] = fmt_label

    ydl_opts = {
        "format":             fmt,
        "ffmpeg_location":    FFMPEG_PATH,
        "merge_output_format": merge_format,
        "outtmpl":            os.path.join(DOWNLOAD_FOLDER, "%(title)s.%(ext)s"),
        "restrictfilenames":  True,
        "noplaylist":         True,
        "progress_hooks":     [ydl_progress_hook],
        "quiet":              True,
        "no_warnings":        True,
        "noprogress":         False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        progress_data.update({"status": "done", "percent": 100, "eta": "Complete!"})
    except Exception as e:
        progress_data.update({"status": "error", "error": str(e)})

# ── Routes ─────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return HTML_PAGE

@app.route("/download", methods=["POST"])
def download():
    data    = request.get_json()
    url     = (data or {}).get("url", "").strip()
    quality = (data or {}).get("quality", "2160")
    if not url:
        return jsonify({"error": "No URL provided"}), 400
    if progress_data["status"] in ("downloading", "starting", "merging"):
        return jsonify({"error": "A download is already running"}), 409
    threading.Thread(target=run_download, args=(url, quality), daemon=True).start()
    return jsonify({"ok": True})

@app.route("/progress")
def progress():
    """Server-Sent Events — real-time progress stream."""
    import time, json
    def stream():
        last = None
        while True:
            snap = dict(progress_data)
            if snap != last:
                yield f"data: {json.dumps(snap)}\n\n"
                last = snap
            if snap["status"] in ("done", "error"):
                break
            time.sleep(0.3)
    return Response(
        stream(),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )

@app.route("/open-folder")
def open_folder():
    os.startfile(DOWNLOAD_FOLDER)
    return jsonify({"ok": True})

# ── Embedded HTML ───────────────────────────────────────────────────────────────
HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>YT 4K Rajloader</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  ::-webkit-scrollbar{width:8px}
  ::-webkit-scrollbar-track{background:#0a0a0f}
  ::-webkit-scrollbar-thumb{background:#333;border-radius:10px}
  ::-webkit-scrollbar-thumb:hover{background:#f00}
  body{background:#0a0a0f;color:#e0e0e0;font-family:'Segoe UI',sans-serif;
       display:flex;flex-direction:column;align-items:center;min-height:100vh;padding:30px 16px}
  h1{font-size:2rem;color:#ff0033;text-shadow:0 0 12px #f003;letter-spacing:2px;margin-bottom:6px}
  .sub{color:#888;font-size:.85rem;margin-bottom:28px}
  .card{background:#111;border:1px solid #222;border-radius:12px;padding:28px;width:100%;max-width:640px;margin-bottom:20px}
  .row{display:flex;gap:10px;margin-bottom:16px}
  input[type=text]{flex:1;background:#1a1a1a;border:1px solid #333;border-radius:8px;
                   padding:10px 14px;color:#fff;font-size:.95rem;outline:none}
  input[type=text]:focus{border-color:#ff0033;box-shadow:0 0 8px #f002}
  button{background:#ff0033;border:none;border-radius:8px;padding:10px 18px;
         color:#fff;font-weight:700;cursor:pointer;transition:background .2s}
  button:hover{background:#cc0029}
  button:disabled{background:#555;cursor:not-allowed}
  .quality-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:16px}
  .q-btn{background:#1a1a1a;border:1px solid #333;border-radius:8px;padding:10px 0;
         color:#aaa;font-size:.85rem;cursor:pointer;transition:all .2s;text-align:center}
  .q-btn .tag{display:block;font-size:.7rem;color:#555;margin-top:2px}
  .q-btn.active{background:#1a0008;border-color:#ff0033;color:#fff}
  .q-btn.active .tag{color:#ff0033}
  /* comparison table */
  .tbl-wrap{overflow-x:auto}
  table{width:100%;border-collapse:collapse;font-size:.82rem}
  th,td{padding:8px 12px;text-align:center;border-bottom:1px solid #1e1e1e}
  th{color:#ff0033;font-weight:600;background:#0f0f0f}
  tr:last-child td{border-bottom:none}
  .badge{display:inline-block;background:#1a0008;border:1px solid #ff0033;
         color:#ff6677;font-size:.7rem;padding:1px 6px;border-radius:20px;margin-left:4px}
  /* progress */
  #progressSection{display:none}
  .prog-label{display:flex;justify-content:space-between;margin-bottom:6px;font-size:.85rem}
  .prog-bar-bg{background:#1e1e1e;border-radius:99px;height:10px;overflow:hidden}
  .prog-bar{background:linear-gradient(90deg,#ff0033,#ff6600);height:10px;width:0;
            border-radius:99px;transition:width .4s ease}
  .meta{display:flex;gap:16px;margin-top:10px;font-size:.8rem;color:#888}
  .meta span b{color:#e0e0e0}
  #statusMsg{margin-top:10px;font-size:.85rem;color:#aaa;min-height:1.2em}
  #statusMsg.err{color:#ff4455}
  /* fmt badge in footer */
  .fmt-strip{display:flex;gap:12px;flex-wrap:wrap;margin-top:4px}
  .fmt-item{font-size:.75rem;color:#555}
  .fmt-item span{color:#888}
  #fmtDynamic{color:#ff6677;font-weight:700}
</style>
</head>
<body>
<h1>⚡ YT 4K Downloader</h1>
<p class="sub">Paste URL → Select Quality → Download. No CMD needed.</p>

<!-- Input card -->
<div class="card">
  <div class="row">
    <input type="text" id="urlInput" placeholder="https://www.youtube.com/watch?v=...">
    <button onclick="pasteUrl()">📋 Paste</button>
  </div>

  <div class="quality-grid">
    <div class="q-btn" data-q="720"  onclick="selectQ(this)">720p<span class="tag">MP4</span></div>
    <div class="q-btn" data-q="1080" onclick="selectQ(this)">1080p<span class="tag">MP4</span></div>
    <div class="q-btn active" data-q="1440" onclick="selectQ(this)">1440p<span class="tag">WebM ✓</span></div>
    <div class="q-btn" data-q="2160" onclick="selectQ(this)">2160p<span class="tag">WebM ★</span></div>
  </div>

  <button id="dlBtn" onclick="startDownload()" style="width:100%;padding:13px">
    ⬇ Download Video
  </button>

  <!-- Progress -->
  <div id="progressSection" style="margin-top:20px">
    <div class="prog-label">
      <span id="statusMsg">Initializing…</span>
      <span id="pctText">0%</span>
    </div>
    <div class="prog-bar-bg"><div class="prog-bar" id="progBar"></div></div>
    <div class="meta">
      <span>Speed: <b id="speedVal">—</b></span>
      <span>ETA: <b id="etaVal">—</b></span>
      <span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">
        File: <b id="fileVal">—</b>
      </span>
    </div>
  </div>
</div>

<!-- Quality comparison -->
<div class="card">
  <b style="color:#ff0033;display:block;margin-bottom:12px">📊 Quality & Format Guide</b>
  <div class="tbl-wrap">
  <table>
    <tr><th>Feature</th><th>720p</th><th>1080p</th><th>1440p</th><th>2160p</th></tr>
    <tr><td>Format</td><td>MP4</td><td>MP4</td><td>WebM</td><td>WebM</td></tr>
    <tr><td>Codec</td><td>H.264</td><td>H.264</td><td>VP9</td><td>VP9/AV1</td></tr>
    <tr><td>Compatibility</td><td>Universal</td><td>Universal</td><td>High</td><td>High</td></tr>
    <tr><td>~10 min size</td><td>150 MB</td><td>400 MB</td><td>900 MB</td><td>2.5 GB</td></tr>
    <tr><td>Best for</td><td>Mobile</td><td>Laptop</td><td>Monitor</td><td>TV / Edit</td></tr>
  </table>
  </div>
</div>

<!-- Footer -->
<div class="card" style="text-align:center">
  <button onclick="openFolder()" style="background:#1a1a1a;border:1px solid #333;color:#aaa;margin-bottom:14px">
    📂 Open Download Folder
  </button>
  <div class="fmt-strip" style="justify-content:center">
    <span class="fmt-item">Auto Format: <span id="fmtDynamic">WebM</span></span>
    <span class="fmt-item">Saves to: <span>~/Downloads/YT_4K</span></span>
  </div>
</div>

<script>
let selectedQ = "1440";
let evtSource = null;

function selectQ(el){
  document.querySelectorAll('.q-btn').forEach(b=>b.classList.remove('active'));
  el.classList.add('active');
  selectedQ = el.dataset.q;
  document.getElementById('fmtDynamic').textContent = parseInt(selectedQ) <= 1080 ? 'MP4' : 'WebM';
}

async function pasteUrl(){
  try{
    const t = await navigator.clipboard.readText();
    document.getElementById('urlInput').value = t;
  } catch(e){ alert('Clipboard access denied — please paste manually.'); }
}

async function startDownload(){
  const url = document.getElementById('urlInput').value.trim();
  if(!url){ alert('Please enter a YouTube URL.'); return; }
  if(evtSource){ evtSource.close(); evtSource=null; }

  document.getElementById('dlBtn').disabled = true;
  document.getElementById('progressSection').style.display = 'block';
  setProgress({status:'starting', percent:0, speed:'', eta:'', filename:'', error:''});

  const res = await fetch('/download',{
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({url, quality: selectedQ})
  });
  const json = await res.json();
  if(json.error){ alert(json.error); document.getElementById('dlBtn').disabled=false; return; }

  evtSource = new EventSource('/progress');
  evtSource.onmessage = e => {
    const d = JSON.parse(e.data);
    setProgress(d);
    if(d.status === 'done' || d.status === 'error'){
      evtSource.close(); evtSource=null;
      document.getElementById('dlBtn').disabled = false;
    }
  };
}

function setProgress(d){
  const bar = document.getElementById('progBar');
  const pct = document.getElementById('pctText');
  const msg = document.getElementById('statusMsg');
  const fmt = d.fmt || (parseInt(selectedQ)<=1080 ? 'MP4':'WebM');

  bar.style.width = (d.percent||0) + '%';
  pct.textContent = (d.percent||0) + '%';
  document.getElementById('speedVal').textContent = d.speed || '—';
  document.getElementById('etaVal').textContent   = d.eta   || '—';
  document.getElementById('fileVal').textContent  = d.filename || '—';

  msg.className = '';
  if(d.status==='starting')    msg.textContent = '⏳ Starting…';
  else if(d.status==='downloading') msg.textContent = `⬇ Downloading ${fmt}…`;
  else if(d.status==='merging')     msg.textContent = '🔧 Merging streams…';
  else if(d.status==='done'){       msg.textContent = '✅ Download complete!'; bar.style.background='#00c853';}
  else if(d.status==='error'){      msg.textContent = '❌ ' + d.error; msg.className='err';}
}

async function openFolder(){
  await fetch('/open-folder');
}
</script>
</body>
</html>"""

# ── Launch ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    threading.Timer(1.2, lambda: webbrowser.open("http://localhost:5000")).start()
    print("🚀 Server running → http://localhost:5000")
    print(f"📁 Downloads → {DOWNLOAD_FOLDER}")
    app.run(debug=False, port=5000, threaded=True)