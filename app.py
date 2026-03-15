import os, re, requests
from flask import Flask, render_template_string, request, jsonify, Response, stream_with_context
import yt_dlp

app = Flask(__name__)

# إعدادات "الشبح" لتخطي حظر سناب شات
YDL_OPTS = {
    'format': 'best',
    'quiet': True,
    'no_warnings': True,
    'noplaylist': True,
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1',
        'Accept': '*/*',
        'Referer': 'https://www.snapchat.com/',
    }
}

HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>محفظ الفيديو النهائي</title>
    <style>
        body { margin: 0; background: #000; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; color: #fff; }
        .card { background: #111; padding: 30px; border-radius: 20px; width: 90%; max-width: 400px; text-align: center; border: 1px solid #333; }
        input { width: 100%; padding: 15px; border-radius: 10px; border: 1px solid #444; background: #222; color: #fff; margin-bottom: 20px; box-sizing: border-box; }
        button { background: #fffc00; color: #000; border: none; padding: 15px; width: 100%; border-radius: 10px; font-weight: bold; cursor: pointer; }
        #res { margin-top: 20px; display: none; }
        .dl-btn { background: #fff; color: #000; padding: 12px; text-decoration: none; border-radius: 8px; display: block; margin-top: 10px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="card">
        <h2 style="color: #fffc00;">محفظ الفيديو 👻</h2>
        <input type="text" id="url" placeholder="الصق رابط سناب هنا...">
        <button onclick="start()" id="btn">جلب الفيديو</button>
        <div id="res">
            <span id="msg">✅ تم استخراج الفيديو</span>
            <a id="link" href="#" class="dl-btn">تنزيل الآن</a>
        </div>
        <p id="err" style="color: #ff4444; font-size: 12px; margin-top: 15px;"></p>
    </div>
    <script>
        async function start() {
            const u = document.getElementById('url').value;
            if(!u) return;
            document.getElementById('btn').innerText = 'جاري كسر الحماية...';
            document.getElementById('err').innerText = '';
            try {
                const r = await fetch('/api/extract', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({url: u}) });
                const d = await r.json();
                if(d.success) {
                    document.getElementById('link').href = '/download?v=' + encodeURIComponent(d.url);
                    document.getElementById('res').style.display = 'block';
                } else { document.getElementById('err').innerText = 'فشل: ' + d.error; }
            } catch { document.getElementById('err').innerText = 'السيرفر لا يستجيب'; }
            finally { document.getElementById('btn').innerText = 'جلب الفيديو'; }
        }
    </script>
</body>
</html>
"""

def force_clean(u):
    # محاولة استخراج الـ ID بأي شكل كان
    m = re.search(r'spotlight/([A-Za-z0-9_-]+)', u)
    if m: return f"https://www.snapchat.com/spotlight/{m.group(1)}"
    return u

@app.route('/')
def home(): return render_template_string(HTML)

@app.route('/api/extract', methods=['POST'])
def extract():
    u = force_clean(request.json.get('url'))
    # المحاولة الأولى: باستخدام yt-dlp
    try:
        with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
            info = ydl.extract_info(u, download=False)
            return jsonify({'success': True, 'url': info.get('url')})
    except Exception as e:
        # المحاولة الثانية: لو فشل المحرك، نطلع نص الخطأ عشان نعرف إيش صاير
        return jsonify({'success': False, 'error': str(e)[:100]})

@app.route('/download')
def download():
    v = request.args.get('v')
    r = requests.get(v, stream=True, headers={'User-Agent': 'Mozilla/5.0'})
    return Response(stream_with_context(r.iter_content(chunk_size=1024*10)), 
                    headers={"Content-Disposition": "attachment; filename=snap.mp4", "Content-Type": "video/mp4"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))