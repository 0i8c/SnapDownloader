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

# --- واجهة NEXUS PRO MAX V7 (دمج مباشر) ---
HTML_CONTENT = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NEXUS PRO MAX - V7</title>
    <style>
        :root { --primary: #3a8dff; --accent: #ffcf40; --bg: #050510; }
        body { background: var(--bg); color: white; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; overflow: hidden; }
        .card { background: rgba(255,255,255,0.05); backdrop-filter: blur(15px); padding: 30px; border-radius: 25px; border: 1px solid rgba(255,255,255,0.1); width: 350px; text-align: center; }
        input { width: 100%; padding: 12px; margin: 15px 0; border-radius: 10px; border: none; background: rgba(255,255,255,0.1); color: white; }
        button { width: 100%; padding: 15px; border-radius: 10px; border: none; background: linear-gradient(90deg, #3a8dff, #8a4fff); color: white; font-weight: bold; cursor: pointer; }
        .status { margin-top: 15px; font-size: 14px; color: var(--accent); }
    </style>
</head>
<body>
    <div class="card">
        <h2>🚀 NEXUS PRO MAX <small style="font-size:10px">V7</small></h2>
        <input type="text" id="snapUrl" placeholder="الصق رابط سناب شات هنا...">
        <button id="downloadBtn">استخراج الفيديو RAW</button>
        <div id="status" class="status"></div>
    </div>
    <script>
        const btn = document.getElementById('downloadBtn');
        const status = document.getElementById('status');
        btn.onclick = async () => {
            const url = document.getElementById('snapUrl').value;
            if(!url) return alert('حط الرابط يا ماهر!');
            btn.disabled = true; status.textContent = 'جاري الاستخراج...';
            try {
                const r = await fetch('/api/download', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({url})
                });
                const d = await r.json();
                if(d.success) {
                    status.innerHTML = `✅ تم الاستخراج بنجاح! <br> الحجم: ${d.size_mb} MB`;
                    window.location.href = d.video_url;
                } else { status.textContent = '❌ خطأ: ' + d.error; }
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
    headers = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4)"}
    async with httpx.AsyncClient(follow_redirects=True, timeout=20.0) as client:
        try:
            resp = await client.get(target, headers=headers)
            resp.raise_for_status()
            match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', resp.text, re.DOTALL)
            if not match: return {"success": False, "error": "المقطع خاص أو غير مدعوم."}
            data = json.loads(match.group(1))
            
            # محرك V7 لاستخراج الميديا
            snap_data = data.get('props', {}).get('pageProps', {}).get('spotlightParams', {}).get('snap', {})
            if not snap_data:
                snap_data = data.get('props', {}).get('pageProps', {}).get('story', {}).get('snaps', [{}])[0]
            
            media_url = snap_data.get('mediaUrl') or snap_data.get('media', {}).get('mediaUrl')
            if not media_url: return {"success": False, "error": "لم يتم العثور على ميديا."}
            
            clean_url = media_url.replace('\\u0026', '&')
            file_name = f"nexus_{uuid.uuid4().hex[:5]}.mp4"
            
            async with client.stream("GET", clean_url) as r:
                r.raise_for_status()
                async with aiofiles.open(file_name, "wb") as f:
                    async for chunk in r.aiter_bytes():
                        await f.write(chunk)
            
            size = round(os.path.getsize(file_name) / (1024*1024), 2)
            return {"success": True, "video_url": f"/video/{file_name}", "size_mb": size}
        except Exception as e:
            return {"success": False, "error": str(e)}

@app.get("/video/{name}")
async def get_video(name: str):
    if os.path.exists(name): return FileResponse(name, media_type="video/mp4")
    return JSONResponse(status_code=404, content={"error": "File expired"})

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
