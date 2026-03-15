import os, re, requests
from flask import Flask, render_template_string, request, jsonify, Response, stream_with_context
import yt_dlp

app = Flask(__name__)

# المحرك الآن سيقرأ الإعدادات من ملف yt-dlp.conf تلقائياً
def get_ydl_opts():
    opts = {
        'quiet': True,
        'no_warnings': True,
        # إذا قررت مستقبلاً ترفع ملف cookies.txt بيقرأه هنا
        'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None,
    }
    return opts

HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>محفظ الفيديو Pro</title>
    <style>
        body { margin: 0; background: #000; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; }
        .card { background: #111; padding: 40px; border-radius: 25px; width: 90%; max-width: 400px; text-align: center; border: 2px solid #fffc00; }
        input { width: 100%; padding: 15px; border-radius: 12px; border: 1px solid #333; background: #222; color: #fff; margin-bottom: 20px; box-sizing: border-box; outline: none; }
        button { background: #fffc00; color: #000; border: none; padding: 15px; width: 100%; border-radius: 12px; font-weight: bold; cursor: pointer; }
        #res { margin-top: 25px; display: none; }
        .dl-btn { background: #fff; color: #000; padding: 15px; text-decoration: none; border-radius: 10px; display: block; font-weight: bold; }
    </style>
</head>
<body>
    <div class="card">
        <h2 style="color: #fffc00;">محفظ الفيديو 👻</h2>
        <input type="text" id="url" placeholder="الصق الرابط هنا...">
        <button onclick="start()" id="btn">استخراج الفيديو</button>
        <div id="res">
            <p style="color: #fff;">تم التجهيز بنجاح! ✅</p>
            <a id="link" href="#" class="dl-btn">حفظ في الجهاز</a>
        </div>
        <p id="err" style="color: #ff4444; font-size: 11px; margin-top: 15px;"></p>
    </div>
    <script>
        async function start() {
            const u = document.getElementById('url').value;
            const b = document.getElementById('btn');
            if(!u) return;
            b.innerText = 'جاري المعالجة...'; b.disabled = true;
            try {
                const r = await fetch('/api/extract', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({url: u}) });
                const d = await r.json();
                if(d.success) {
                    document.getElementById('link').href = '/download?v=' + encodeURIComponent(d.url);
                    document.getElementById('res').style.display = 'block';
                } else { document.getElementById('err').innerText = 'فشل: ' + d.error; }
            } catch { document.getElementById('err').innerText = 'السيرفر لا يستجيب'; }
            finally { b.innerText = 'استخراج الفيديو'; b.disabled = false; }
        }
    </script>
</body>
</html>
"""

def clean_u(u):
    m = re.search(r'spotlight/([A-Za-z0-9_-]+)', u)
    return f"https://www.snapchat.com/spotlight/{m.group(1)}" if m else u

@app.route('/')
def home(): return render_template_string(HTML)

@app.route('/api/extract', methods=['POST'])
def extract():
    u = clean_u(request.json.get('url'))
    try:
        with yt_dlp.YoutubeDL(get_ydl_opts()) as ydl:
            info = ydl.extract_info(u, download=False)
            return jsonify({'success': True, 'url': info.get('url')})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)[:60]})

@app.route('/download')
def download():
    v = request.args.get('v')
    r = requests.get(v, stream=True, headers={'User-Agent': 'Mozilla/5.0'})
    return Response(stream_with_context(r.iter_content(chunk_size=1024*10)), 
                    headers={"Content-Disposition": "attachment; filename=snap_video.mp4", "Content-Type": "video/mp4"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))