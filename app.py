import os, re, requests
from flask import Flask, render_template_string, request, jsonify, Response, stream_with_context
import yt_dlp

app = Flask(__name__)

# إعدادات المحرك القصوى
YDL_OPTS = {
    'format': 'best',
    'quiet': True,
    'no_warnings': True,
    'noplaylist': True,
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    }
}

HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>محفظ الفيديو Pro</title>
    <style>
        body { margin: 0; background: #0f172a; font-family: system-ui, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; color: #fff; }
        .card { background: #1e293b; padding: 40px; border-radius: 24px; width: 90%; max-width: 400px; text-align: center; border: 1px solid #334155; }
        input { width: 100%; padding: 16px; border-radius: 12px; border: 1px solid #334155; background: #0f172a; color: #fff; margin-bottom: 20px; box-sizing: border-box; outline: none; }
        button { background: #3b82f6; color: #fff; border: none; padding: 16px; width: 100%; border-radius: 12px; font-weight: 700; cursor: pointer; }
        #res { margin-top: 30px; display: none; background: #064e3b; padding: 20px; border-radius: 12px; border: 1px solid #059669; }
        .dl-btn { background: #10b981; color: white; padding: 14px; text-decoration: none; border-radius: 10px; display: block; margin-top: 15px; font-weight: 700; }
        .loader { display: none; margin: 20px auto; border: 3px solid #334155; border-top: 3px solid #3b82f6; border-radius: 50%; width: 24px; height: 24px; animation: spin 1s linear infinite; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div class="card">
        <h2>محفظ الفيديو Pro</h2>
        <input type="text" id="url" placeholder="الصق رابط سناب هنا...">
        <button onclick="start()" id="btn">استخراج الآن</button>
        <div class="loader" id="ldr"></div>
        <div id="res">
            <span style="font-weight: 600;">الملف جاهز للتحميل ✅</span>
            <a id="link" href="#" class="dl-btn">حفظ في الجهاز</a>
        </div>
        <p id="err" style="color: #ef4444; margin-top: 20px; font-size: 13px; display: none;"></p>
    </div>
    <script>
        async function start() {
            const u = document.getElementById('url').value;
            const b = document.getElementById('btn');
            const l = document.getElementById('ldr');
            const r_div = document.getElementById('res');
            const e = document.getElementById('err');
            if(!u) return;
            b.style.display = 'none'; l.style.display = 'block'; r_div.style.display = 'none'; e.style.display = 'none';
            try {
                const r = await fetch('/api/extract', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({url: u}) });
                const d = await r.json();
                if(d.success) {
                    document.getElementById('link').href = '/download?v=' + encodeURIComponent(d.url);
                    r_div.style.display = 'block';
                } else { e.innerText = 'خطأ: ' + d.error; e.style.display = 'block'; b.style.display = 'block'; }
            } catch { e.innerText = 'فشل في الاتصال بالسيرفر'; e.style.display = 'block'; b.style.display = 'block'; }
            finally { l.style.display = 'none'; }
        }
    </script>
</body>
</html>
"""

def clean_snap_url(u):
    # الفلتر الذكي: يسحب المعرف فقط من الرابط مهما كان فيه @ أو غيره
    match = re.search(r'spotlight/([A-Za-z0-9_-]+)', u)
    if match:
        video_id = match.group(1)
        # بناء رابط "نظيف" يقبله yt-dlp غصباً عنه
        return f"https://www.snapchat.com/spotlight/{video_id}"
    return u

@app.route('/')
def home(): return render_template_string(HTML)

@app.route('/api/extract', methods=['POST'])
def extract():
    raw_url = request.json.get('url')
    clean_url = clean_snap_url(raw_url)
    try:
        with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
            info = ydl.extract_info(clean_url, download=False)
            return jsonify({'success': True, 'url': info.get('url')})
    except Exception as e:
        return jsonify({'success': False, 'error': "Unsupported URL or Private Content"})

@app.route('/download')
def download():
    v = request.args.get('v')
    r = requests.get(v, stream=True)
    return Response(stream_with_context(r.iter_content(chunk_size=1024*10)), 
                    headers={"Content-Disposition": "attachment; filename=snap_video.mp4", "Content-Type": "video/mp4"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))