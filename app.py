import os
from flask import Flask, render_template_string, request, jsonify, Response, stream_with_context
import yt_dlp
import requests

app = Flask(__name__)

# إعدادات المحرك لتخطي الحماية
YDL_OPTIONS = {
    'format': 'best',
    'quiet': True,
    'no_warnings': True,
    'noplaylist': True,
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1',
    }
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>محفظ الفيديو Pro</title>
    <style>
        body { margin: 0; background: #f8fafc; font-family: -apple-system, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; }
        .card { background: #fff; padding: 40px; border-radius: 24px; box-shadow: 0 10px 30px rgba(0,0,0,0.08); width: 90%; max-width: 400px; text-align: center; }
        h1 { color: #1e293b; font-size: 24px; margin-bottom: 25px; font-weight: 800; }
        input { width: 100%; padding: 16px; border: 2px solid #e2e8f0; border-radius: 12px; margin-bottom: 20px; box-sizing: border-box; font-size: 16px; outline: none; transition: 0.3s; }
        input:focus { border-color: #3b82f6; }
        button { background: #1e293b; color: #fff; border: none; padding: 16px; width: 100%; border-radius: 12px; font-weight: bold; cursor: pointer; font-size: 16px; }
        .loader { display: none; margin: 20px auto; border: 4px solid #f3f3f3; border-top: 4px solid #3b82f6; border-radius: 50%; width: 30px; height: 30px; animation: spin 1s linear infinite; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        #res { margin-top: 30px; display: none; }
        .btn-dl { background: #2563eb; color: white; padding: 15px 30px; text-decoration: none; border-radius: 12px; display: inline-block; font-weight: bold; width: 100%; box-sizing: border-box; }
    </style>
</head>
<body>
    <div class="card">
        <h1>محفظ الفيديو</h1>
        <input type="text" id="url" placeholder="الصق رابط الفيديو هنا..." autocomplete="off">
        <button onclick="process()" id="btn">معالجة الفيديو</button>
        <div class="loader" id="ldr"></div>
        <div id="res">
            <p style="color: #059669; font-weight: 600; margin-bottom: 15px;">تم تجهيز الفيديو بنجاح!</p>
            <a id="link" href="#" class="btn-dl">اضغط هنا للتحميل الآن</a>
        </div>
    </div>
    <script>
        async function process() {
            const u = document.getElementById('url').value;
            if(!u) return;
            document.getElementById('btn').style.display = 'none';
            document.getElementById('ldr').style.display = 'block';
            document.getElementById('res').style.display = 'none';
            try {
                const r = await fetch('/api/extract', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({url: u}) });
                const d = await r.json();
                if(d.success) {
                    // نربط الزر بمسار التحميل الإجباري في السيرفر
                    document.getElementById('link').href = '/download?video_url=' + encodeURIComponent(d.url);
                    document.getElementById('res').style.display = 'block';
                } else {
                    alert('فشل استخراج الفيديو، تأكد من أن الحساب عام وليس خاصاً.');
                    document.getElementById('btn').style.display = 'block';
                }
            } catch {
                alert('خطأ في الاتصال');
                document.getElementById('btn').style.display = 'block';
            } finally {
                document.getElementById('ldr').style.display = 'none';
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home(): return render_template_string(HTML_TEMPLATE)

@app.route('/api/extract', methods=['POST'])
def extract():
    u = request.json.get('url')
    try:
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(u, download=False)
            return jsonify({'success': True, 'url': info.get('url')})
    except: return jsonify({'success': False})

@app.route('/download')
def download():
    video_url = request.args.get('video_url')
    # إجبار المتصفح على تحميل الملف بدلاً من تشغيله عبر headers خاصة
    req = requests.get(video_url, stream=True)
    def generate():
        for chunk in req.iter_content(chunk_size=4096):
            yield chunk
    
    return Response(
        stream_with_context(generate()),
        headers={
            "Content-Disposition": "attachment; filename=video.mp4",
            "Content-Type": "video/mp4"
        }
    )

if __name__ == '__main__': app.run(host='0.0.0.0', port=5000)
