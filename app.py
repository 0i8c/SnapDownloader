import os, re, requests
from flask import Flask, request, jsonify, render_template_string
import yt_dlp

app = Flask(__name__)

YDL_OPTS = {
    "quiet": True,
    "no_warnings": True,
    "noplaylist": True,
    "format": "best",
    "http_headers": {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.snapchat.com/"
    }
}

HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Snap Downloader</title>
<style>
body{background:#000;color:#fff;font-family:sans-serif;text-align:center;padding:40px}
input{width:90%;padding:15px;border-radius:10px;border:none}
button{padding:15px 25px;background:#fffc00;border:none;border-radius:10px;margin-top:10px}
a{display:block;margin-top:20px;color:#0f0}
video{margin-top:20px;width:90%;border-radius:10px}
</style>
</head>
<body>

<h2>تحميل فيديو سناب</h2>

<input id="url" placeholder="ضع رابط السناب">
<br>
<button onclick="go()">استخراج</button>

<a id="dl"></a>

<video id="player" controls></video>

<script>
async function go(){

let u=document.getElementById("url").value

let r=await fetch("/api",{
method:"POST",
headers:{"Content-Type":"application/json"},
body:JSON.stringify({url:u})
})

let d=await r.json()

if(d.success){

let v=document.getElementById("player")
v.src=d.url

let a=document.getElementById("dl")
a.href=d.url
a.innerText="تحميل الفيديو"

}else{

alert("لم يتم العثور على فيديو")

}

}
</script>

</body>
</html>
"""

def get_spotlight_from_profile(url):

    try:

        html=requests.get(url,headers={"User-Agent":"Mozilla/5.0"}).text

        m=re.search(r"spotlight/([A-Za-z0-9_-]+)",html)

        if m:

            vid=m.group(1)

            return f"https://www.snapchat.com/spotlight/{vid}"

    except:

        return None

    return None


def clean_url(u):

    if "spotlight" in u:
        m=re.search(r"spotlight/([A-Za-z0-9_-]+)",u)
        if m:
            return f"https://www.snapchat.com/spotlight/{m.group(1)}"

    if "@"+"" in u:
        s=get_spotlight_from_profile(u)
        if s:
            return s

    return u


@app.route("/")
def home():
    return render_template_string(HTML)


@app.route("/api",methods=["POST"])
def api():

    url=request.json.get("url")

    url=clean_url(url)

    try:

        with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:

            info=ydl.extract_info(url,download=False)

            video_url=info.get("url")

            if not video_url and "formats" in info:
                video_url=info["formats"][-1]["url"]

            return jsonify({
                "success":True,
                "url":video_url
            })

    except Exception as e:

        return jsonify({
            "success":False,
            "error":str(e)
        })


if __name__=="__main__":

    port=int(os.environ.get("PORT",5000))

    app.run(host="0.0.0.0",port=port)