import os
import re
import json
import uuid
import asyncio
import aiofiles
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from pydantic import BaseModel

app = FastAPI()

# --- محرك الاستخراج V7 ---
def get_snap_video_v7(data: dict) -> list:
    urls = set()
    try:
        # مسار Spotlight
        spot = data.get('props', {}).get('pageProps', {}).get('spotlightParams', {}).get('snap', {}).get('mediaUrl')
        if spot: urls.add(spot)
        # مسار القصص
        snaps = data.get('props', {}).get('pageProps', {}).get('story', {}).get('snaps', [])
        for s in snaps:
            m = s.get('media', {}).get('mediaUrl')
            if m: urls.add(m)
    except: pass
    return list(urls)

# --- عرض الواجهة الزجاجية ---
@app.get("/", response_class=HTMLResponse)
async def serve_home():
    # يبحث عن الملف بأي اسم محتمل لتجنب الخطأ
    for filename in ["index.html", "index.html.txt", "indox.html"]:
        if os.path.exists(filename):
            async with aiofiles.open(filename, "r", encoding="utf-8") as f:
                return HTMLResponse(content=await f.read())
    return HTMLResponse(content="<h1>خطأ: لم يتم العثور على ملف index.html في المستودع!</h1>", status_code=404)

# --- معالج التحميل ---
class SnapUrl(BaseModel):
    url: str

@app.post("/api/download")
async def start_download(req: SnapUrl):
    target = req.url.strip()
    headers = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4)"}
    
    async with httpx.AsyncClient(follow_redirects=True, timeout=20.0) as client:
        try:
            resp = await client.get(target, headers=headers)
            match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', resp.text, re.DOTALL)
            if not match: return {"success": False, "error": "فشل المحرك في العثور على بيانات الفيديو."}
            
            data = json.loads(match.group(1))
            urls = get_snap_video_v7(data)
            if not urls: return {"success": False, "error": "لم يتم العثور على روابط خام (RAW)."}
            
            clean_url = urls[0].replace('\\u0026', '&')
            file_name = f"nexus_{uuid.uuid4().hex[:5]}.mp4"
            
            # تحميل فعلي لضمان صلاحية الرابط للمستخدم
            async with client.stream("GET", clean_url) as r:
                async with aiofiles.open(file_name, "wb") as f:
                    async for chunk in r.aiter_bytes():
                        await f.write(chunk)
            
            size = round(os.path.getsize(file_name) / (1024*1024), 2)
            return {"success": True, "video_url": f"/video/{file_name}", "size_mb": size, "method": "V7 Engine"}
        except Exception as e:
            return {"success": False, "error": str(e)}

@app.get("/video/{name}")
async def get_video(name: str):
    if os.path.exists(name): return FileResponse(name, media_type="video/mp4")
    return JSONResponse(status_code=404, content={"error": "File expired"})
