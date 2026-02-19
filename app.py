import os
import threading
import webbrowser
from flask import Flask, request, jsonify, Response
import yt_dlp

app = Flask(__name__)

# ── Config ───────────────────────────────────────────────────────────────────
DOWNLOAD_FOLDER = "downloads"
FFMPEG_PATH = "/tmp/ffmpeg/ffmpeg" if os.path.exists("/tmp/ffmpeg/ffmpeg") else "ffmpeg"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# ── Shared progress state ────────────────────────────────────────────────────
progress_data = {
    "status": "idle", "percent": 0,
    "speed": "", "eta": "", "filename": "", "error": ""
}


def ydl_progress_hook(d):
    status = d.get("status", "")

    if status == "downloading":
        # yt-dlp newer versions: use raw bytes to calc percent
        downloaded = d.get("downloaded_bytes") or 0
        total      = d.get("total_bytes") or d.get("total_bytes_estimate") or 0

        if total > 0:
            pct = round((downloaded / total) * 100, 1)
        else:
            # fallback: try _percent_str
            raw = d.get("_percent_str", "0%").strip().replace("%", "").replace("\x1b[0;94m", "").replace("\x1b[0m", "")
            try:
                pct = float(raw)
            except ValueError:
                pct = 0

        # Speed: prefer _speed_str, fallback to bytes/s
        speed = d.get("_speed_str", "")
        if not speed or speed == "Unknown":
            spd_bytes = d.get("speed") or 0
            if spd_bytes:
                speed = f"{spd_bytes/1024/1024:.1f} MiB/s"

        # ETA
        eta = d.get("_eta_str", "")
        if not eta or eta == "Unknown":
            eta_sec = d.get("eta") or 0
            if eta_sec:
                m, s = divmod(int(eta_sec), 60)
                eta = f"{m}m {s}s" if m else f"{s}s"

        filename = os.path.basename(d.get("filename", ""))

        progress_data.update({
            "status":   "downloading",
            "percent":  pct,
            "speed":    speed.strip(),
            "eta":      eta.strip(),
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


def run_download(url: str, quality: str):
    progress_data.update({
        "status": "starting", "percent": 0,
        "speed": "", "eta": "", "filename": "", "error": ""
    })

    fmt = (
        f"bestvideo[height<={quality}][ext=webm]+bestaudio[ext=webm]/"
        f"bestvideo[height<={quality}]+bestaudio/"
        f"best[height<={quality}]"
    )

    ydl_opts = {
        "format":             fmt,
        "ffmpeg_location":    FFMPEG_PATH,
        "merge_output_format":"webm",
        "outtmpl":            os.path.join(DOWNLOAD_FOLDER, "%(title)s.%(ext)s"),
        "restrictfilenames":  True,
        "noplaylist":         True,
        "progress_hooks":     [ydl_progress_hook],
        "quiet":              True,
        "no_warnings":        True,
        # Force yt-dlp to report progress even in quiet mode
        "noprogress":         False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        progress_data.update({"status": "done", "percent": 100, "eta": "Complete!"})
    except Exception as e:
        progress_data.update({"status": "error", "error": str(e)})


# ── Routes ───────────────────────────────────────────────────────────────────
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


# ── Embedded HTML ─────────────────────────────────────────────────────────────
HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>YT 4K Downloader</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{min-height:100vh;background:#0a0a0f;font-family:'Segoe UI',sans-serif;display:flex;align-items:center;justify-content:center}
body::before{content:'';position:fixed;inset:0;background:radial-gradient(ellipse at 20% 50%,rgba(255,0,0,.08),transparent 50%),radial-gradient(ellipse at 80% 20%,rgba(120,0,255,.08),transparent 50%);pointer-events:none}
body::after{content:'';position:fixed;inset:0;background-image:linear-gradient(rgba(255,255,255,.02) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.02) 1px,transparent 1px);background-size:40px 40px;pointer-events:none}
.card{background:rgba(15,15,25,.9);border:1px solid rgba(255,255,255,.08);border-radius:24px;padding:44px 38px;width:520px;max-width:95vw;backdrop-filter:blur(20px);box-shadow:0 40px 80px rgba(0,0,0,.6);position:relative;z-index:10}
.card::before{content:'';position:absolute;top:0;left:20%;right:20%;height:1px;background:linear-gradient(90deg,transparent,#f00,#a855f7,transparent);border-radius:999px}
.logo-row{display:flex;align-items:center;gap:14px;margin-bottom:30px}
.yt-icon{width:48px;height:48px;background:#f00;border-radius:12px;display:flex;align-items:center;justify-content:center;box-shadow:0 0 20px rgba(255,0,0,.4);flex-shrink:0}
.yt-icon svg{width:26px;height:26px;fill:#fff}
.title-group h1{font-size:1.25rem;font-weight:700;color:#fff}
.title-group p{font-size:.75rem;color:rgba(255,255,255,.4);margin-top:2px}
.badge{margin-left:auto;background:linear-gradient(135deg,rgba(255,0,0,.2),rgba(168,85,247,.2));border:1px solid rgba(255,100,100,.3);color:#ff6b6b;font-size:.68rem;font-weight:700;padding:4px 10px;border-radius:999px}
label{display:block;font-size:.72rem;font-weight:600;color:rgba(255,255,255,.45);text-transform:uppercase;letter-spacing:1px;margin-bottom:8px}
.input-wrap{position:relative;margin-bottom:18px}
.input-wrap input{width:100%;background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.1);border-radius:12px;padding:14px 60px 14px 18px;color:#fff;font-size:.9rem;outline:none;transition:all .3s}
.input-wrap input:focus{border-color:rgba(255,0,0,.5);background:rgba(255,255,255,.06);box-shadow:0 0 0 3px rgba(255,0,0,.08)}
.input-wrap input::placeholder{color:rgba(255,255,255,.2)}
.paste-btn{position:absolute;right:10px;top:50%;transform:translateY(-50%);background:rgba(255,255,255,.07);border:none;border-radius:8px;color:rgba(255,255,255,.5);font-size:.68rem;padding:5px 10px;cursor:pointer;transition:all .2s}
.paste-btn:hover{background:rgba(255,255,255,.15);color:#fff}
.q-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:22px}
.q-btn{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);border-radius:10px;color:rgba(255,255,255,.5);font-size:.78rem;font-weight:600;padding:10px 4px;cursor:pointer;transition:all .2s;text-align:center}
.q-btn:hover{border-color:rgba(255,0,0,.3);color:#fff}
.q-btn.active{background:linear-gradient(135deg,rgba(255,0,0,.2),rgba(168,85,247,.15));border-color:rgba(255,0,0,.5);color:#fff;box-shadow:0 0 12px rgba(255,0,0,.15)}
.q-btn .res{font-size:.95rem;display:block;margin-bottom:2px}
.q-btn .tag{font-size:.58rem;opacity:.6}
.dl-btn{width:100%;padding:15px;background:linear-gradient(135deg,#f00,#c00);border:none;border-radius:12px;color:#fff;font-size:1rem;font-weight:700;cursor:pointer;transition:all .3s;box-shadow:0 4px 20px rgba(255,0,0,.3)}
.dl-btn:hover:not(:disabled){transform:translateY(-1px);box-shadow:0 8px 30px rgba(255,0,0,.4)}
.dl-btn:disabled{opacity:.5;cursor:not-allowed;transform:none}
.progress-section{margin-top:22px;display:none}
.progress-section.show{display:block}
.prog-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}
.prog-label{font-size:.78rem;color:rgba(255,255,255,.5)}
.prog-pct{font-size:1.1rem;font-weight:700;color:#f87171;font-variant-numeric:tabular-nums}
.prog-bg{background:rgba(255,255,255,.06);border-radius:999px;height:10px;overflow:hidden;margin-bottom:10px;position:relative}
.prog-fill{height:100%;background:linear-gradient(90deg,#f00,#a855f7);border-radius:999px;width:0%;transition:width .4s ease;box-shadow:0 0 10px rgba(255,0,0,.5)}
/* animated shimmer on bar */
.prog-fill::after{content:'';position:absolute;inset:0;background:linear-gradient(90deg,transparent 0%,rgba(255,255,255,.15) 50%,transparent 100%);animation:shimmer 1.5s infinite;border-radius:999px}
@keyframes shimmer{0%{transform:translateX(-100%)}100%{transform:translateX(200%)}}
.prog-meta{display:flex;gap:16px;font-size:.72rem;color:rgba(255,255,255,.35);flex-wrap:wrap}
.prog-meta span b{color:rgba(255,255,255,.65);font-weight:600}
.status-box{margin-top:14px;padding:12px 16px;border-radius:10px;font-size:.82rem;display:none;align-items:center;gap:10px}
.status-box.show{display:flex}
.status-box.info{background:rgba(59,130,246,.1);border:1px solid rgba(59,130,246,.2);color:#93c5fd}
.status-box.success{background:rgba(34,197,94,.1);border:1px solid rgba(34,197,94,.2);color:#86efac}
.status-box.error{background:rgba(239,68,68,.1);border:1px solid rgba(239,68,68,.2);color:#fca5a5}
.folder-btn{margin-top:12px;width:100%;padding:10px;background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1);border-radius:10px;color:rgba(255,255,255,.5);font-size:.8rem;cursor:pointer;transition:all .2s;display:none}
.folder-btn.show{display:block}
.folder-btn:hover{background:rgba(255,255,255,.1);color:#fff}
/* Compare table */
.compare-wrap{margin-top:18px;margin-bottom:4px}
.compare-title{font-size:.72rem;font-weight:600;color:rgba(255,255,255,.4);text-transform:uppercase;letter-spacing:1px;margin-bottom:10px}
.compare-table{width:100%;border-collapse:collapse;font-size:.72rem}
.compare-table th,.compare-table td{padding:8px 6px;text-align:center;border-bottom:1px solid rgba(255,255,255,.05);color:rgba(255,255,255,.45)}
.compare-table th{color:rgba(255,255,255,.3);font-weight:600;font-size:.65rem;text-transform:uppercase;letter-spacing:.5px}
.compare-table td:first-child{text-align:left;color:rgba(255,255,255,.35);padding-left:2px}
.compare-table tr:last-child td{border-bottom:none}
.compare-table .hl{background:rgba(255,0,0,.07);color:#fca5a5!important;font-weight:600;border-left:1px solid rgba(255,0,0,.2);border-right:1px solid rgba(255,0,0,.2)}
.compare-table thead .hl{color:#f87171!important;background:rgba(255,0,0,.1)}
/* dynamic highlight */
.compare-table .col{transition:all .3s}
.compare-table .active-col{background:rgba(255,0,0,.07)!important;color:#fca5a5!important;font-weight:600}
.compare-table thead .active-col{background:rgba(255,0,0,.12)!important;color:#f87171!important}
.pills{display:flex;gap:8px;margin-top:18px;flex-wrap:wrap}
.pill{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);border-radius:999px;color:rgba(255,255,255,.35);font-size:.68rem;padding:4px 12px;display:flex;align-items:center;gap:5px}
.pill span{color:rgba(255,255,255,.6);font-weight:600}
</style>
</head>
<body>
<div class="card">
  <div class="logo-row">
    <div class="yt-icon">
      <svg viewBox="0 0 24 24"><path d="M19.615 3.184c-3.604-.246-11.631-.245-15.23 0-3.897.266-4.356 2.62-4.385 8.816.029 6.185.484 8.549 4.385 8.816 3.6.245 11.626.246 15.23 0 3.897-.266 4.356-2.62 4.385-8.816-.029-6.185-.484-8.549-4.385-8.816zm-10.615 12.816v-8l8 3.993-8 4.007z"/></svg>
    </div>
    <div class="title-group">
      <h1>YT 4K Downloader</h1>
      <p>Paste URL → Click → Done. No CMD needed.</p>
    </div>
    <div class="badge">4K WebM</div>
  </div>

  <label>YouTube URL</label>
  <div class="input-wrap">
    <input type="text" id="urlInput" placeholder="https://www.youtube.com/watch?v=..." />
    <button class="paste-btn" onclick="pasteUrl()">Paste</button>
  </div>

  <label>Quality Select Karo</label>
  <div class="q-grid">
    <button class="q-btn" onclick="setQ(this,'720')"><span class="res">720p</span><span class="tag">Basic HD</span></button>
    <button class="q-btn" onclick="setQ(this,'1080')"><span class="res">1080p</span><span class="tag">Full HD</span></button>
    <button class="q-btn" onclick="setQ(this,'1440')"><span class="res">1440p</span><span class="tag">2K QHD</span></button>
    <button class="q-btn active" onclick="setQ(this,'2160')"><span class="res">2160p</span><span class="tag">4K ★</span></button>
  </div>

  <!-- Comparison Table -->
  <div class="compare-wrap" id="compareWrap">
    <div class="compare-title">📊 Quality Comparison</div>
    <table class="compare-table">
      <thead>
        <tr>
          <th>Feature</th>
          <th class="col q720">720p</th>
          <th class="col q1080">1080p</th>
          <th class="col q1440 hl">1440p ✓</th>
          <th class="col q2160">2160p</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>Sharpness</td>
          <td class="col q720">Average</td>
          <td class="col q1080">Sharp</td>
          <td class="col q1440 hl">Ultra Sharp</td>
          <td class="col q2160">Maximum</td>
        </tr>
        <tr>
          <td>Detail</td>
          <td class="col q720">Kam</td>
          <td class="col q1080">Zyada</td>
          <td class="col q1440 hl">Bahut Zyada</td>
          <td class="col q2160">Maximum</td>
        </tr>
        <tr>
          <td>Bitrate</td>
          <td class="col q720">2–4 Mbps</td>
          <td class="col q1080">5–8 Mbps</td>
          <td class="col q1440 hl">12–16 Mbps</td>
          <td class="col q2160">20–40 Mbps</td>
        </tr>
        <tr>
          <td>10 min size</td>
          <td class="col q720">~150 MB</td>
          <td class="col q1080">~400 MB</td>
          <td class="col q1440 hl">~900 MB</td>
          <td class="col q2160">~2.5 GB</td>
        </tr>
        <tr>
          <td>Best for</td>
          <td class="col q720">Mobile</td>
          <td class="col q1080">Laptop</td>
          <td class="col q1440 hl">Monitor</td>
          <td class="col q2160">TV / Edit</td>
        </tr>
      </tbody>
    </table>
  </div>

  <button class="dl-btn" id="dlBtn" onclick="startDownload()">⬇ Download Video</button>

  <div class="progress-section" id="progSection">
    <div class="prog-header">
      <span class="prog-label" id="progLabel">Initializing…</span>
      <span class="prog-pct" id="progPct">0%</span>
    </div>
    <div class="prog-bg"><div class="prog-fill" id="progFill"></div></div>
    <div class="prog-meta">
      <span>Speed: <b id="progSpeed">—</b></span>
      <span>ETA: <b id="progEta">—</b></span>
      <span>File: <b id="progFile">—</b></span>
    </div>
  </div>

  <div class="status-box" id="statusBox"></div>
  <button class="folder-btn" id="folderBtn" onclick="openFolder()">📂 Open Download Folder</button>

  <div class="pills">
    <div class="pill">Format: <span>WebM</span></div>
    <div class="pill">Codec: <span>VP9</span></div>
    <div class="pill">Audio: <span>Opus</span></div>
    <div class="pill">Saves to: <span>~/Downloads/YT_4K</span></div>
  </div>
</div>

<script>
let selectedQ = '2160', evtSource = null;

function setQ(el, q) {
  document.querySelectorAll('.q-btn').forEach(b => b.classList.remove('active'));
  el.classList.add('active');
  selectedQ = q;
  // highlight matching column in table
  const map = {'720':'q720','1080':'q1080','1440':'q1440','2160':'q2160'};
  document.querySelectorAll('.compare-table .col').forEach(c => c.classList.remove('active-col'));
  if (map[q]) document.querySelectorAll('.compare-table .' + map[q]).forEach(c => c.classList.add('active-col'));
}
// init highlight on load
window.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.compare-table .q2160').forEach(c => c.classList.add('active-col'));
});

async function pasteUrl() {
  try { document.getElementById('urlInput').value = await navigator.clipboard.readText(); }
  catch { document.getElementById('urlInput').focus(); }
}

function showStatus(type, msg) {
  const el = document.getElementById('statusBox');
  const icons = { info: 'ℹ️', success: '✅', error: '❌' };
  el.className = `status-box show ${type}`;
  el.innerHTML = `<span>${icons[type]}</span><span>${msg}</span>`;
}

function setProgress(pct, label, speed, eta, file) {
  document.getElementById('progSection').classList.add('show');
  document.getElementById('progFill').style.width = pct + '%';
  document.getElementById('progPct').textContent = pct + '%';
  document.getElementById('progLabel').textContent = label;
  document.getElementById('progSpeed').textContent = speed || '—';
  document.getElementById('progEta').textContent = eta || '—';
  if (file) document.getElementById('progFile').textContent = file.length > 26 ? file.substring(0, 26) + '…' : file;
}

async function startDownload() {
  const url = document.getElementById('urlInput').value.trim();
  if (!url) { showStatus('error', 'Please enter a YouTube URL!'); return; }

  // reset UI
  document.getElementById('dlBtn').disabled = true;
  document.getElementById('folderBtn').classList.remove('show');
  document.getElementById('statusBox').className = 'status-box';
  setProgress(0, 'Connecting…', '', '', '');
  showStatus('info', 'Sending request to server…');

  try {
    const res  = await fetch('/download', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url, quality: selectedQ })
    });
    const data = await res.json();
    if (!res.ok) {
      showStatus('error', data.error || 'Failed to start download');
      document.getElementById('dlBtn').disabled = false;
      return;
    }
  } catch (err) {
    showStatus('error', 'Cannot reach server: ' + err.message);
    document.getElementById('dlBtn').disabled = false;
    return;
  }

  // close old SSE if any
  if (evtSource) evtSource.close();
  evtSource = new EventSource('/progress');

  evtSource.onmessage = e => {
    const d = JSON.parse(e.data);

    if (d.status === 'starting') {
      setProgress(0, 'Starting download…', '', '', '');
      showStatus('info', 'yt-dlp is initializing…');

    } else if (d.status === 'downloading') {
      setProgress(d.percent, 'Downloading…', d.speed, d.eta, d.filename);
      showStatus('info', `⬇ ${d.percent}%  |  ${d.speed || '…'}  |  ETA: ${d.eta || '…'}`);

    } else if (d.status === 'merging') {
      setProgress(99, 'Merging video + audio…', '', 'almost done…', d.filename);
      showStatus('info', '🔀 Merging streams with FFmpeg…');

    } else if (d.status === 'done') {
      setProgress(100, 'Download complete! 🎉', '', '', '');
      showStatus('success', 'Video saved to Downloads/YT_4K folder!');
      document.getElementById('folderBtn').classList.add('show');
      document.getElementById('dlBtn').disabled = false;
      evtSource.close();

    } else if (d.status === 'error') {
      showStatus('error', 'Error: ' + d.error);
      document.getElementById('dlBtn').disabled = false;
      evtSource.close();
    }
  };

  evtSource.onerror = () => {
    // SSE closed naturally after done/error — ignore
  };
}

function openFolder() { fetch('/open-folder'); }
</script>
</body>
</html>"""


# ── Launch ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Render ke liye port aur host setup
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Server running on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
