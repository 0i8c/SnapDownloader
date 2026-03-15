import os
from flask import Flask, render_template_string, request, jsonify, Response, stream_with_context
import yt_dlp
import requests
import re

app = Flask(__name__)

# إعدادات المحرك الاحترافية
YDL_OPTS = {
    'format': 'best',
    'quiet': True,
    'no_warnings': True,
    'noplaylist': True,
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
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
        body { margin: 0; background: #f0f2f5; font-family: -apple-system, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; }
        .card { background: white; padding: 40px; border-radius: 24px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); width: 90%; max-width: 400px; text-align: center; }
        h1 { color: #1a1a1a; margin-bottom: 25px; font-size: 24px; }
        input { width: 100%; padding: 16px; border: 2px solid #e1e4e8; border-radius: 14px; margin-bottom: 20px; box-sizing: border-box; font-size: 16px; outline: none; }
        input:focus { border-color: #007bff; }
        button { background: #1a1a1a; color: white; border: none; padding: 16px; width: 100%; border-radius: 14px; font-weight: bold; cursor: pointer; font-size: 16px; }
        #res { margin-top: 30px; display: none; border-top: 1px solid #eee; padding-top: 20px; }
        .dl-btn { background: #007bff; color: white; padding: 16px; text-decoration: none; border-radius: 12px; display: block; font-weight: bold; }
    </style>
</head>
<body>
    <div class="card">
        <h1>محفظ الفيديو</h1>
        <input type="text" id="url" placeholder="الصق رابط سناب هنا...">
        <button onclick="start()" id="btn">معالجة الفيديو</button>
        <div id="res">
            <p style="color: #28a745; font-weight: bold;">جاهز للتحميل ✅</p>
            <a id="link" href="#" class="dl-btn">حفظ في التنزيلات</a>
        </div>
    </div>
    <script>
        async function start() {
            const u = document.getElementById('url').value;
            if(!u) return;
            const btn = document.getElementById('btn');
            btn.innerText = 'جاري التنظيف والمعالجة...';
            btn.disabled = true;
            try {
                const r = await fetch('/api/extract', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({url: u})
                });
                const d = await r.json();
                if(d.success) {
                    document.getElementById('link').href = '/download?v=' + encodeURIComponent(d.url);
                    document.getElementById('res').style.display = 'block';
                } else { alert('فشل الاستخراج. تأكد أن الرابط عام.'); }
            } catch { alert('خطأ في الاتصال بالسيرفر'); }
            finally { btn.innerText = 'معالجة الفيديو'; btn.disabled = false; }
        }
    </script>
</body>
</html>
"""

def clean_snap_url(url):
    # تنظيف الرابط من اسم المستخدم ومعلومات التتبع
    # يحول https://www.snapchat.com/@user/spotlight/ID إلى https://www.snapchat.com/spotlight/ID
    match = re.search(r'spotlight/([^?&]+)', url)
    if match:
        video_id = match.group(1)
        return f"https://www.snapchat.com/spotlight/{video_id}"
    return url

@app.route('/')
def home(): return render_template_string(HTML)

@app.route('/api/extract', methods=['POST'])
def extract():
    raw_url = request.json.get('url')
    url = clean_snap_url(raw_url)
    try:
        with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
            info = ydl.extract_info(url, download=False)
            return jsonify({'success': True, 'url': info.get('url')})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'success': False})

@app.route('/download')
def download():
    v = request.args.get('v')
    r = requests.get(v, stream=True)
    return Response(
        stream_with_context(r.iter_content(chunk_size=8192)),
        headers={
            "Content-Disposition": "attachment; filename=snap_video.mp4",
            "Content-Type": "video/mp4"
        }
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
