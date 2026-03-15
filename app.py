import os, re, requests
from flask import Flask, render_template_string, request, jsonify, Response, stream_with_context
import yt_dlp

app = Flask(__name__)

# إعدادات تخطي الحظر لعام 2026
YDL_OPTS = {
    'format': 'best',
    'quiet': True,
    'no_warnings': True,
    'noplaylist': True,
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1',
        'Referer': 'https://www.snapchat.com/',
    }
}

HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>S-DL Ultimate</title>
    <style>
        body { margin: 0; background: #000; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; color: #fff; }
        .card { background: #111; padding: 40px; border-radius: 24px; width: 90%; max-width: 400px; text-align: center; border: 2px solid #fffc00; }
        input { width: 100%; padding: 16px; border-radius: 12px; border: 1px solid #333; background: #000; color: #fff; margin-bottom: 20px; box-sizing: border-box; }
        button { background: #fffc00; color: #000; border: none; padding: 16px; width: 100%; border-radius: 12px; font-weight: bold; cursor: pointer; font-size: 16px; }
        #res { margin-top: 30px; display: none; background: #1a1a1a; padding: 20px; border-radius: 12px; }
        .dl-btn { background: #fff; color: #000; padding: 14px; text-decoration: none; border-radius: 10px; display: block; margin-top: 15px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="card">
        <h2 style="color: #fffc00;">محفظ الفيديو 👻</h2>
        <input type="text" id="url" placeholder="الصق الرابط هنا..." autocomplete="off">
        <button onclick="start()" id="btn">معالجة فورية</button>
        <div id="res">
            <p>✅ الرابط جاهز للتحميل</p>
            <a id="link" href="#" class="dl-btn">حفظ في الجهاز</a>
        </div>
        <p id="err" style="color: #ff4444; font-size: 11px; margin-top: 20px;"></p>
    </div>
    <script>
        async function start() {
            const u = document.getElementById('url').value;
            const b = document.getElementById('btn');
            const e = document.getElementById('err');
            if(!u) return;
            b.innerText = 'جاري تصفية الرابط...'; b.disabled = true;
            document.getElementById('res').style.display = 'none'; e.innerText = '';
            try {
                const r = await fetch('/api/extract', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({url: u}) });
                const d = await r.json();
                if(d.success) {
                    document.getElementById('link').href = '/download?v=' + encodeURIComponent(d.url);
                    document.getElementById('res').style.display = 'block';
                } else { e.innerText = 'فشل: ' + d.error; }
            } catch { e.innerText = 'السيرفر معلق.. حدث الصفحة'; }
            finally { b.innerText = 'معالجة فورية'; b.disabled = false; }
        }
    </script>
</body>
</html>
"""

def clean_snap_url(u):
    # محرك البحث عن "كود الفيديو" وتجاهل اسم المستخدم (@)
    # يبحث عن أي شيء بعد كلمة spotlight/
    match = re.search(r'spotlight/([A-Za-z0-9_-]+)', u)
    if match:
        video_id = match.group(1)
        # إعادة بناء الرابط "النظيف" اللي يقبله السيرفر
        return f"https://www.snapchat.com/spotlight/{video_id}"
    return u

@app.route('/')
def home(): return render_template_string(HTML)

@app.route('/api/extract', methods=['POST'])
def extract():
    raw_url = request.json.get('url')
    # الفلترة الحقيقية هنا
    u = clean_snap_url(raw_url)
    try:
        with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
            info = ydl.extract_info(u, download=False)
            return jsonify({'success': True, 'url': info.get('url')})
    except Exception as e:
        return jsonify({'success': False, 'error': "Unsupported URL or Server Blocked"})

@app.route('/download')
def download():
    v = request.args.get('v')
    r = requests.get(v, stream=True, headers={'User-Agent': 'Mozilla/5.0'})
    return Response(stream_with_context(r.iter_content(chunk_size=1024*10)), 
                    headers={"Content-Disposition": "attachment; filename=snap.mp4", "Content-Type": "video/mp4"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))