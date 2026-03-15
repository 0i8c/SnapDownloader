import os, re, requests, random
from flask import Flask, request, jsonify, render_template_string, Response, stream_with_context
import yt_dlp

app = Flask(__name__)

# قائمة "هويات" مختلفة عشان نخدع السناب
USER_AGENTS = [
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36'
]

HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>S-DL Final Boss</title>
    <style>
        body { margin: 0; background: #000; font-family: -apple-system, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; color: #fff; }
        .card { background: #111; padding: 40px; border-radius: 30px; width: 90%; max-width: 400px; text-align: center; border: 2px solid #fffc00; box-shadow: 0 0 20px rgba(255,252,0,0.2); }
        input { width: 100%; padding: 16px; border-radius: 15px; border: 1px solid #333; background: #222; color: #fff; margin-bottom: 20px; box-sizing: border-box; font-size: 16px; outline: none; }
        button { background: #fffc00; color: #000; border: none; padding: 16px; width: 100%; border-radius: 15px; font-weight: 900; cursor: pointer; font-size: 16px; }
        #res { margin-top: 30px; display: none; }
        .dl-btn { background: #fff; color: #000; padding: 15px; text-decoration: none; border-radius: 12px; display: block; margin-top: 15px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="card">
        <h1 style="color: #fffc00; font-size: 24px;">محفظ السناب 👻</h1>
        <p style="font-size: 12px; color: #888;">إذا فشل، كرر المحاولة 3 مرات</p>
        <input id="url" placeholder="الصق الرابط هنا...">
        <button onclick="go()" id="btn">استخراج الفيديو</button>
        <div id="res">
            <p>✅ نجح الاختراق!</p>
            <a id="dl" class="dl-btn">حفظ في الآيفون</a>
        </div>
        <p id="err" style="color: #ff4444; font-size: 12px; margin-top: 20px;"></p>
    </div>
    <script>
    async function go(){
        let u = document.getElementById("url").value;
        let b = document.getElementById("btn");
        let e = document.getElementById("err");
        if(!u) return;
        b.innerText = "جاري المحاولة..."; b.disabled = true; e.innerText = "";
        try {
            let r = await fetch("/api", { method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify({url:u}) });
            let d = await r.json();
            if(d.success){
                document.getElementById("dl").href = "/proxy?v=" + encodeURIComponent(d.url);
                document.getElementById("res").style.display = "block";
            } else { e.innerText = d.error; }
        } catch { e.innerText = "السيرفر مضغوط.. حاول مرة ثانية"; }
        finally { b.innerText = "استخراج الفيديو"; b.disabled = false; }
    }
    </script>
</body>
</html>
"""

def clean_u(u):
    m = re.search(r'spotlight/([A-Za-z0-9_-]+)', u)
    return f"https://www.snapchat.com/spotlight/{m.group(1)}" if m else u

@app.route("/")
def home(): return render_template_string(HTML)

@app.route("/api", methods=["POST"])
def api():
    u = clean_u(request.json.get("url"))
    # نختار هوية عشوائية في كل طلب
    agent = random.choice(USER_AGENTS)
    opts = {
        'quiet': True, 'format': 'best',
        'http_headers': {'User-Agent': agent, 'Referer': 'https://www.snapchat.com/'}
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(u, download=False)
            v = info.get('url') or info.get('formats', [{}])[-1].get('url')
            if v: return jsonify({"success": True, "url": v})
            return jsonify({"success": False, "error": "سناب شات رفض الطلب. جرب مرة ثانية."})
    except Exception as ex:
        if "403" in str(ex):
            return jsonify({"success": False, "error": "آي بي السيرفر محظور حالياً (403)"})
        return jsonify({"success": False, "error": "رابط غير مدعوم"})

@app.route("/proxy")
def proxy():
    v = request.args.get('v')
    r = requests.get(v, stream=True, headers={'User-Agent': random.choice(USER_AGENTS)})
    return Response(stream_with_context(r.iter_content(chunk_size=1024*10)), 
                    headers={"Content-Disposition": "attachment; filename=snap.mp4", "Content-Type": "video/mp4"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))