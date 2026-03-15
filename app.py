import os, re, requests
from flask import Flask, request, jsonify, render_template_string, Response, stream_with_context
import yt_dlp

app = Flask(__name__)

# إعدادات المحرك
YDL_OPTS = {
    'quiet': True, 'no_warnings': True, 'noplaylist': True, 'format': 'best',
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1',
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
        .card { background: #111; padding: 40px; border-radius: 25px; width: 90%; max-width: 400px; text-align: center; border: 2px solid #fffc00; }
        input { width: 100%; padding: 15px; border-radius: 12px; border: 1px solid #333; background: #222; color: #fff; margin-bottom: 20px; box-sizing: border-box; outline: none; }
        button { background: #fffc00; color: #000; border: none; padding: 15px; width: 100%; border-radius: 12px; font-weight: bold; cursor: pointer; }
        #res { margin-top: 25px; display: none; }
        .dl-btn { background: #fff; color: #000; padding: 15px; text-decoration: none; border-radius: 10px; display: block; margin-top: 15px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="card">
        <h2 style="color: #fffc00;">منظف ومحفظ السناب 👻</h2>
        <input id="url" placeholder="الصق الرابط (حتى لو فيه @)">
        <button onclick="go()" id="btn">استخراج تلقائي</button>
        <div id="res">
            <p>✅ تم التنظيف والاستخراج!</p>
            <a id="dl" class="dl-btn">حفظ الفيديو</a>
        </div>
        <p id="err" style="color: #ff4444; font-size: 12px; margin-top: 20px;"></p>
    </div>
    <script>
    async function go(){
        let u = document.getElementById("url").value;
        let b = document.getElementById("btn");
        let e = document.getElementById("err");
        if(!u) return;
        b.innerText = "جاري التنظيف..."; b.disabled = true; e.innerText = "";
        try {
            let r = await fetch("/api", { method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify({url:u}) });
            let d = await r.json();
            if(d.success){
                document.getElementById("dl").href = "/proxy?v=" + encodeURIComponent(d.url);
                document.getElementById("res").style.display = "block";
            } else { e.innerText = "فشل: " + d.error; }
        } catch { e.innerText = "السيرفر لا يستجيب"; }
        finally { b.innerText = "استخراج تلقائي"; b.disabled = false; }
    }
    </script>
</body>
</html>
"""

def clean_url(u):
    # المحول التلقائي الذكي
    m = re.search(r'spotlight/([A-Za-z0-9_-]+)', u)
    if m:
        return f"https://www.snapchat.com/spotlight/{m.group(1)}"
    return u

@app.route("/")
def home(): return render_template_string(HTML)

@app.route("/api", methods=["POST"])
def api():
    u = clean_url(request.json.get("url")) # هنا نستخدم المنظف
    try:
        with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
            info = ydl.extract_info(u, download=False)
            v_url = info.get('url') or info.get('formats', [{}])[-1].get('url')
            if v_url: return jsonify({"success": True, "url": v_url})
            return jsonify({"success": False, "error": "لم نجد الفيديو"})
    except Exception as ex:
        return jsonify({"success": False, "error": "سناب شات حظر السيرفر أو الرابط خاص"})

@app.route("/proxy")
def proxy():
    v = request.args.get('v')
    r = requests.get(v, stream=True, headers={'User-Agent': 'Mozilla/5.0'})
    return Response(stream_with_context(r.iter_content(chunk_size=1024*10)), 
                    headers={"Content-Disposition": "attachment; filename=snap.mp4", "Content-Type": "video/mp4"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
