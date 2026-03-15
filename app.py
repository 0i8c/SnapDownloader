import os, re, requests, logging
from flask import Flask, render_template_string, request, jsonify, Response, stream_with_context
import yt_dlp

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

# إعدادات قصوى لمحاكاة بشري حقيقي وتجاوز الحظر
YDL_OPTS = {
    'format': 'best',
    'quiet': False,
    'no_warnings': False,
    'noplaylist': True,
    'headers': {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-us',
        'Referer': 'https://www.snapchat.com/',
    }
}

HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>S-DL PRO</title>
    <style>
        body { margin: 0; background: #0f172a; font-family: system-ui, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; color: #fff; }
        .card { background: #1e293b; padding: 40px; border-radius: 24px; width: 90%; max-width: 400px; text-align: center; border: 1px solid #334155; }
        input { width: 100%; padding: 16px; border-radius: 12px; border: 1px solid #334155; background: #0f172a; color: #fff; margin-bottom: 20px; box-sizing: border-box; }
        button { background: #3b82f6; color: #fff; border: none; padding: 16px; width: 100%; border-radius: 12px; font-weight: 700; cursor: pointer; }
        #res { margin-top: 30px; display: none; padding: 20px; background: #064e3b; border-radius: 12px; }
        .dl-btn { background: #10b981; color: white; padding: 14px; text-decoration: none; border-radius: 10px; display: block; margin-top: 10px; font-weight: 700; }
    </style>
</head>
<body>
    <div class="card">
        <h2>محفظ الفيديو Pro</h2>
        <input type="text" id="url" placeholder="الصق الرابط هنا...">
        <button onclick="start()" id="btn">استخراج الآن</button>
        <div id="res">
            <span>جاهز للتحميل ✅</span>
            <a id="link" href="#" class="dl-btn">حفظ الفيديو</a>
        </div>
        <p id="err" style="color: #ef4444; margin-top: 20px; font-size: 13px; display: none;"></p>
    </div>
    <script>
        async function start() {
            const u = document.getElementById('url').value;
            const b = document.getElementById('btn');
            const e = document.getElementById('err');
            if(!u) return;
            b.innerText = 'جاري كسر الحماية...'; b.disabled = true; e.style.display = 'none';
            try {
                const r = await fetch('/api/extract', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({url: u}) });
                const d = await r.json();
                if(d.success) {
                    document.getElementById('link').href = '/download?v=' + encodeURIComponent(d.url);
                    document.getElementById('res').style.display = 'block';
                } else { e.innerText = 'السبب: ' + d.error; e.style.display = 'block'; }
            } catch { e.innerText = 'فشل الاتصال بالسيرفر'; e.style.display = 'block'; }
            finally { b.innerText = 'استخراج الآن'; b.disabled = false; }
        }
    </script>
</body>
</html>
"""

def clean_url(u):
    # تنظيف فائق للرابط لاستخراج المعرف فقط
    match = re.search(r'spotlight/([^?&/]+)', u)
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
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)[:100]})

@app.route('/download')
def download():
    v = request.args.get('v')
    r = requests.get(v, stream=True, headers={'User-Agent': 'Mozilla/5.0'})
    return Response(stream_with_context(r.iter_content(chunk_size=1024*10)), 
                    headers={"Content-Disposition": "attachment; filename=video.mp4", "Content-Type": "video/mp4"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))