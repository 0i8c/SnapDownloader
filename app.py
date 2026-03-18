import os
import re
import json
import uuid
import aiofiles
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from pydantic import BaseModel

app = FastAPI()

# --- إعدادات المنافذ ---
PORT = int(os.environ.get("PORT", 8000))

# --- الواجهة الزجاجية المطورة ---
HTML_CONTENT = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NEXUS V7 - NO WATERMARK</title>
    <style>
        :root { --primary: #fffc00; --bg: #000000; }
        body { background: var(--bg); color: white; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .card { background: rgba(255,255,255,0.03); backdrop-filter: blur(25px); padding: 40px; border-radius: 35px; border: 1px solid rgba(255,252,0,0.2); width: 90%; max-width: 420px; text-align: center; box-shadow: 0 15px 35px rgba(0,0,0,0.7); }
        h2 { color: var(--primary); letter-spacing: 2px; margin-bottom: 5px; }
        input { width: 100%; padding: 16px; margin: 25px 0; border-radius: 15px; border: 1px solid rgba(255,255,255,0.1); background: rgba(255,255,255,0.05); color: white; text-align: center; font-size: 15px; transition: 0.3s; outline: none; }
        input:focus { border-color: var(--primary); background: rgba(255,255,255,0.1); }
        button { width: 100%; padding: 16px; border-radius: 15px; border: none; background: var(--primary); color: black; font-weight: 800; cursor: pointer; font-size: 17px; transition: 0.4s; box-shadow: 0 5px 15px rgba(255,252,0,0.2); }
        button:hover { transform: translateY(-3px); box-shadow: 0 8px 20px rgba(255,252,0,0.4); }
        button:disabled { opacity: 0.4; transform: none; }
        .status { margin-top: 25px; font-size: 14px; color: #aaa; line-height: 1.6; }
    </style>
</head>
<body>
    <div class="card">
        <h2>NEXUS V7</h2>
        <p style="color:#666; font-size:12px;">تحميل فيديو الأضواء الأصلي (بدون علامة مائية)</p>
        <input type="text" id="snapUrl" placeholder="ضع رابط Spotlight هنا...">
        <button id="downloadBtn">استخراج الفيديو الأصلي ✨</button>
        <div id="status" class="status"></div>
    </div>
    <script>
        const btn = document.getElementById('downloadBtn');
        const status = document.getElementById('status');
        btn.onclick = async () => {
            const url = document.getElementById('snapUrl').value.trim();
            if(!url) return;
            btn.disabled = true; status.innerHTML = '⏳ جاري اختراق التشفير واستخراج النسخة الأصلية...';
            try {
                const r = await fetch('/api/download', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({url})
                });
                const d = await r.json();
                if(d.success) {
                    status.innerHTML = `<b style="color:#fffc00">✅ تم القنص بنجاح!</b><br>جاري التحميل بأعلى جودة...`;
                    window.location.href = d.video_url;
                } else { status.innerHTML = '❌ فشل: ' + d.error; }
            } catch(e) { status.textContent = '❌ تعذر الاتصال بالسيرفر'; }
            btn.disabled = false;
        };
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def serve_home():
    return HTML_CONTENT

class SnapUrl(BaseModel):
    url: str

@app.post("/api/download")
async def start_download(req: SnapUrl):
    target = req.url.strip()
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9"
    }
    
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        try:
            resp = await client.get(target, headers=headers)
            match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', resp.text, re.DOTALL)
            if not match: return {"success": False, "error": "الصفحة لا تحتوي على بيانات فيديو."}
            
            data = json.loads(match.group(1))
            
            # محرك البحث عن "النسخة الأصلية المرفوعة"
            # نبحث أولاً في ملفات الـ Assets المسبقة التحميل لأنها غالباً تحتوي على النسخة الصافية
            video_url = None
            
            # محاولة 1: البحث في Spotlight Params (الخيار الأول)
            video_url = data.get('props', {}).get('pageProps', {}).get('spotlightParams', {}).get('snap', {}).get('mediaUrl')
            
            # محاولة 2: البحث في قائمة الـ Assets (أقوى مكان للنسخ الأصلية)
            if not video_url:
                assets = data.get('props', {}).get('pageProps', {}).get('preloadedAssets', [])
                for asset in assets:
                    if isinstance(asset, str) and ('.mp4' in asset or 'media-video' in asset):
                        video_url = asset
                        break
            
            # محاولة 3: البحث في مسار الـ Story التقليدي
            if not video_url:
                snaps = data.get('props', {}).get('pageProps', {}).get('story', {}).get('snaps', [])
                if snaps:
                    video_url = snaps[0].get('media', {}).get('mediaUrl')

            if not video_url:
                return {"success": False, "error": "لم نجد نسخة أصلية متاحة لهذا المقطع."}
            
            clean_url = video_url.replace('\\u0026', '&')
            file_name = f"nexus_original_{uuid.uuid4().hex[:5]}.mp4"
            
            async with client.stream("GET", clean_url) as r:
                r.raise_for_status()
                async with aiofiles.open(file_name, "wb") as f:
                    async for chunk in r.aiter_bytes():
                        await f.write(chunk)
            
            size = round(os.path.getsize(file_name) / (1024*1024), 2)
            return {"success": True, "video_url": f"/video/{file_name}", "size_mb": size}
            
        except Exception as e:
            return {"success": False, "error": "المحرك تعثر في سحب المقطع."}

@app.get("/video/{name}")
async def get_video(name: str):
    if os.path.exists(name): return FileResponse(name, media_type="video/mp4")
    return JSONResponse(status_code=404, content={"error": "انتهت الجلسة"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
