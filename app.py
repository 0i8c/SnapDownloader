import os
from flask import Flask, render_template_string, request, jsonify
import yt_dlp

app = Flask(__name__)

# إعدادات احترافية لتخطى الحماية
YDL_OPTIONS = {
    'format': 'best',
    'quiet': True,
    'no_warnings': True,
    'noplaylist': True,
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
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
        body { margin: 0; background: #f8fafc; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; }
        .card { background: #fff; padding: 40px; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); width: 90%; max-width: 400px; text-align: center; border-top: 5px solid #1e293b; }
        h1 { color: #1e293b; font-size: 24px; margin-bottom: 25px; }
        input { width: 100%; padding: 15px; border: 1px solid #e2e8f0; border-radius: 10px; margin-bottom: 20px; box-sizing: border-box; font-size: 16px; }
        button { background: #1e293b; color: #fff; border: none; padding: 15px; width: 100%; border-radius: 10px; font-weight: bold; cursor: pointer; }
        .loader { display: none; margin: 20px auto; border: 3px solid #f3f3f3; border-top: 3px solid #3b82f6; border-radius: 50%; width: 25px; height: 25px; animation: spin 1s linear infinite; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        #res { margin-top: 25px; display: none; }
        .btn-dl { background: #3b82f6; color: white; padding: 12px 20px; text-decoration: none; border-radius: 8px; display: inline-block; font-weight: bold; }
    </style>
</head>
<body>
    <div class="card">
        <h1>محفظ الفيديو</h1>
        <input type="text" id="url" placeholder="الصق الرابط هنا..." autocomplete="off">
        <button onclick="start()" id="btn">معالجة</button>
        <div class="loader" id="ldr"></div>
        <div id="res">
            <p style="color: #059669;">جاهز للتحميل ✅</p>
            <a id="link" href="#" target="_blank" class="btn-dl">فتح الملف مباشر</a>
        </div>
    </div>
    <script>
        async function start() {
            const u = document.getElementById('url').value;
            if(!u) return;
            document.getElementById('btn').style.display = 'none';
            document.getElementById('ldr').style.display = 'block';
            document.getElementById('res').style.display = 'none';
            try {
                const r = await fetch('/api/extract', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({url: u}) });
                const d = await r.json();
                if(d.success) { document.getElementById('link').href = d.url; document.getElementById('res').style.display = 'block'; }
                else { alert('فشل المعالجة، تأكد من صحة الرابط'); document.getElementById('btn').style.display = 'block'; }
            } catch { alert('خطأ فني'); document.getElementById('btn').style.display = 'block'; }
            finally { document.getElementById('ldr').style.display = 'none'; }
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

if __name__ == '__main__': app.run(host='0.0.0.0', port=5000)
