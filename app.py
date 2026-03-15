import os, re, requests
from flask import Flask, render_template_string, request, jsonify, Response, stream_with_context
import yt_dlp

app = Flask(__name__)

# إعدادات المحرك لعام 2026 - محاكاة متصفح آيفون حديث جداً
YDL_OPTS = {
    'format': 'best',
    'quiet': True,
    'no_warnings': True,
    'noplaylist': True,
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Mobile/15E148 Safari/604.1',
        'Referer': 'https://www.snapchat.com/',
    }
}

HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>محفظ الفيديو Pro</title>
    <style>
        body { margin: 0; background: #000; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; color: #fff; }
        .card { background: #111; padding: 40px; border-radius: 25px; width: 90%; max-width: 400px; text-align: center; border: 1px solid #fffc00; box-shadow: 0 0 20px rgba(255, 252, 0, 0.2); }
        h2 { color: #fffc00; margin-bottom: 25px; }
        input { width: 100%; padding: 16px; border-radius: 15px; border: 1px solid #333; background: #222; color: #fff; margin-bottom: 20px; box-sizing: border-box; font-size: 16px; outline: none; }
        button { background: #fffc00; color: #000; border: none; padding: 16px; width: 100%; border-radius: 15px; font-weight: bold; cursor: pointer; font-size: 16px; }
        #res { margin-top: 30px; display: none; }
        .dl-btn { background: #fff; color: #000; padding: 15px; text-decoration: none; border-radius: 12px; display: block; margin-top: 15px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="card">
        <h2>محفظ السناب 👻</h2>
        <input type="text" id="url" placeholder="الصق الرابط هنا..." autocomplete="off">
        <button onclick="start()" id="btn">معالجة فورية</button>
        <div id="res">
            <p>✅ تم كسر الحماية بنجاح</p>
            <a id="link" href="#" class="dl-btn">حفظ في التنزيلات</a>
        </div>
        <p id="err" style="color: #ff4444; font-size: 12px; margin-top: 20px;"></p>
    </div>
    <script>
        async function start() {
            const u = document.getElementById('url').value;
            const b = document.getElementById('btn');
            const e = document.getElementById('err');
            if(!u) return;
            b.innerText = 'جاري التنظيف...'; b.disabled = true; e.innerText = '';
            try {
                const r = await fetch('/api/extract', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({url: u}) });
                const d = await r.json();
                if(d.success) {
                    document.getElementById('link').href = '/download?v=' + encodeURIComponent(d.url);
                    document.getElementById('res').style.display = 'block';
                } else { e.innerText = 'الخطأ: ' + d.error; }
            } catch { e.innerText = 'تعذر الاتصال بالسيرفر'; }
            finally { b.innerText = 'معالجة فورية'; b.disabled = false; }
        }
    </script>
</body>
</html>
"""

def clean_url(url):
    # محرك البحث عن كود الفيديو فقط وتجاهل اسم المستخدم
    # هذا السطر هو "المشرط" الذي سيحل مشكلة @t_00511
    match = re.search(r'spotlight/([A-Za-z0-9_-]+)', url)
    if match:
        video_id = match.group(1)
        # إعادة بناء الرابط بالشكل الذي يعشقه yt-dlp
        return f"https://www.snapchat.com/spotlight/{video_id}"
    return url

@app.route('/')
def home(): return render_template_string(HTML)

@app.route('/api/extract', methods=['POST'])
def extract():
    raw_url = request.json.get('url')
    # تنظيف الرابط قبل إرساله للمحرك
    u = clean_url(raw_url)
    try:
        with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
            info = ydl.extract_info(u, download=False)
            return jsonify({'success': True, 'url': info.get('url')})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)[:50]})

@app.route('/download')
def download():
    v = request.args.get('v')
    r = requests.get(v, stream=True, headers={'User-Agent': 'Mozilla/5.0'})
    return Response(stream_with_context(r.iter_content(chunk_size=1024*10)), 
                    headers={"Content-Disposition": "attachment; filename=snap_video.mp4", "Content-Type": "video/mp4"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))