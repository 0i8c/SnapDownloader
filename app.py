import os, re, requests
from flask import Flask, render_template_string, request, jsonify, Response, stream_with_context
import yt_dlp

app = Flask(__name__)

# إعدادات قوية جداً لمحاكاة متصفح حقيقي
YDL_OPTS = {
    'format': 'best',
    'quiet': True,
    'no_warnings': True,
    'noplaylist': True,
    'extract_flat': False,
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': '*/*',
        'Referer': 'https://www.snapchat.com/',
    }
}

HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>محفظ الفيديو Pro</title>
    <style>
        :root { --p: #1e293b; --a: #3b82f6; }
        body { margin: 0; background: #f8fafc; font-family: -apple-system, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; }
        .card { background: #fff; padding: 40px; border-radius: 24px; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1); width: 90%; max-width: 400px; text-align: center; }
        h1 { color: var(--p); font-size: 24px; margin-bottom: 30px; }
        input { width: 100%; padding: 16px; border: 2px solid #e2e8f0; border-radius: 12px; margin-bottom: 20px; box-sizing: border-box; font-size: 16px; outline: none; }
        button { background: var(--p); color: #fff; border: none; padding: 16px; width: 100%; border-radius: 12px; font-weight: bold; cursor: pointer; font-size: 16px; transition: 0.3s; }
        button:disabled { background: #94a3b8; }
        #res { margin-top: 30px; display: none; }
        .dl-btn { background: var(--a); color: white; padding: 16px; text-decoration: none; border-radius: 12px; display: block; font-weight: bold; }
    </style>
</head>
<body>
    <div class="card">
        <h1>محفظ الفيديو</h1>
        <input type="text" id="url" placeholder="الصق الرابط هنا..." autocomplete="off">
        <button onclick="start()" id="btn">معالجة الفيديو</button>
        <div id="res">
            <p style="color: #059669; font-weight: 600; margin-bottom: 15px;">تم التجهيز بنجاح! ✅</p>
            <a id="link" href="#" class="dl-btn">حفظ في الجهاز</a>
        </div>
    </div>
    <script>
        async function start() {
            const u = document.getElementById('url').value;
            if(!u) return;
            const b = document.getElementById('btn');
            b.innerText = 'جاري كسر التشفير...'; b.disabled = true;
            document.getElementById('res').style.display = 'none';
            try {
                const r = await fetch('/api/extract', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({url: u}) });
                const d = await r.json();
                if(d.success) {
                    document.getElementById('link').href = '/download?v=' + encodeURIComponent(d.url);
                    document.getElementById('res').style.display = 'block';
                } else { alert('فشل الاستخراج. تأكد أن الرابط عام.'); }
            } catch { alert('خطأ فني في السيرفر'); }
            finally { b.innerText = 'معالجة الفيديو'; b.disabled = false; }
        }
    </script>
</body>
</html>
"""

def clean_url(u):
    # محرك البحث عن المعرف الفريد للفيديو (Spotlight ID)
    match = re.search(r'spotlight/([A-Za-z0-9_-]+)', u)
    if match:
        return f"https://www.snapchat.com/spotlight/{match.group(1)}"
    return u

@app.route('/')
def home(): return render_template_string(HTML)

@app.route('/api/extract', methods=['POST'])
def extract():
    u = clean_url(request.json.get('url'))
    try:
        with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
            info = ydl.extract_info(u, download=False)
            return jsonify({'success': True, 'url': info.get('url')})
    except: return jsonify({'success': False})

@app.route('/download')
def download():
    v = request.args.get('v')
    r = requests.get(v, stream=True)
    return Response(stream_with_context(r.iter_content(chunk_size=1024*10)), 
                    headers={"Content-Disposition": "attachment; filename=snap_video.mp4", "Content-Type": "video/mp4"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
