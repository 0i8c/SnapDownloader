import os
import base64
from flask import Flask, render_template_string, request, jsonify
import yt_dlp

app = Flask(__name__)

# إعدادات المحرك الاحترافي
YDL_OPTIONS = {
    'format': 'bestvideo+bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'noplaylist': True,
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
}

# كود الواجهة مشفر جزئياً لحمايته
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>S-DL Pro | محمل الأضواء</title>
    <style>
        :root { --main: #FFFC00; --dark: #000000; }
        body { margin: 0; background: var(--main); font-family: 'Inter', sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; }
        .app-container { background: #fff; padding: 40px; border-radius: 30px; box-shadow: 0 20px 40px rgba(0,0,0,0.2); width: 90%; max-width: 450px; position: relative; overflow: hidden; }
        .app-container::before { content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 5px; background: linear-gradient(90deg, #000, #444); }
        h1 { font-size: 28px; margin-bottom: 10px; color: var(--dark); }
        p { color: #666; font-size: 14px; margin-bottom: 30px; }
        .input-group { position: relative; margin-bottom: 20px; }
        input { width: 100%; padding: 15px; border: 2px solid #f0f0f0; border-radius: 15px; outline: none; transition: 0.3s; box-sizing: border-box; font-size: 16px; }
        input:focus { border-color: var(--dark); }
        button { background: var(--dark); color: #fff; border: none; padding: 15px; width: 100%; border-radius: 15px; font-weight: 700; cursor: pointer; transition: 0.3s; font-size: 16px; }
        button:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
        .loader { display: none; margin: 20px auto; border: 3px solid #f3f3f3; border-top: 3px solid #000; border-radius: 50%; width: 30px; height: 30px; animation: spin 1s linear infinite; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        #result { margin-top: 25px; display: none; animation: fadeIn 0.5s; }
        .download-btn { background: #28a745; display: inline-block; padding: 12px 25px; color: white; text-decoration: none; border-radius: 10px; font-weight: bold; margin-top: 10px; }
        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
    </style>
</head>
<body>
    <div class="app-container">
        <h1>تحميل ذكي 👻</h1>
        <p>استخرج فيديو الأضواء بجودة كاملة وبدون علامة</p>
        <div class="input-group">
            <input type="text" id="snapUrl" placeholder="الصق رابط سناب شات هنا..." autocomplete="off">
        </div>
        <button onclick="processLink()" id="mainBtn">معالجة الرابط الآن</button>
        <div class="loader" id="loader"></div>
        <div id="result">
            <div style="padding: 15px; background: #f8f9fa; border-radius: 12px;">
                <span style="font-size: 14px; color: #333;">جاهز للتحميل!</span><br>
                <a id="finalLink" href="#" target="_blank" class="download-btn">حفظ الفيديو مباشر</a>
            </div>
        </div>
    </div>

    <script>
        async function processLink() {
            const url = document.getElementById('snapUrl').value;
            const btn = document.getElementById('mainBtn');
            const loader = document.getElementById('loader');
            const result = document.getElementById('result');

            if(!url) return alert('يرجى وضع رابط!');

            btn.style.display = 'none';
            loader.style.display = 'block';
            result.style.display = 'none';

            try {
                const response = await fetch('/api/extract', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({url: url})
                });
                const data = await response.json();
                
                if(data.success) {
                    document.getElementById('finalLink').href = data.download_url;
                    result.style.display = 'block';
                } else {
                    alert('فشل الاستخراج، تأكد من صحة الرابط');
                    btn.style.display = 'block';
                }
            } catch (e) {
                alert('حدث خطأ فني');
                btn.style.display = 'block';
            } finally {
                loader.style.display = 'none';
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/extract', methods=['POST'])
def extract():
    data = request.json
    url = data.get('url')
    try:
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(url, download=False)
            # استخراج الرابط الحقيقي المباشر
            raw_url = info.get('url')
            return jsonify({'success': True, 'download_url': raw_url})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
