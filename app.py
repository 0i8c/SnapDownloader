import os
import re
import json
import uuid
import aiofiles
import httpx
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from pydantic import BaseModel

app = FastAPI()

# 1. حل مشكلة تشغيل السيرفر (نقطة 1 و 2 في تحليلك)
# Railway يستخدم المتغير $PORT تلقائياً، وحنا بنثبته هنا
PORT = int(os.environ.get("PORT", 8000))

@app.get("/", response_class=HTMLResponse)
async def serve_home():
    # بحث عن الملف (نقطة 3 في تحليلك)
    file_path = "index.html"
    if os.path.exists(file_path):
        async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=await f.read())
    return HTMLResponse(content="<h1>Error: index.html not found</h1>", status_code=404)

class SnapUrl(BaseModel):
    url: str

@app.post("/api/download")
async def start_download(req: SnapUrl):
    target = req.url.strip()
    headers = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4)"}
    
    async with httpx.AsyncClient(follow_redirects=True, timeout=20.0) as client:
        try:
            # نقطة 4 و 5: الحماية من الروابط السيئة و JSON الغلط
            resp = await client.get(target, headers=headers)
            resp.raise_for_status()
            
            match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', resp.text, re.DOTALL)
            if not match: return {"success": False, "error": "المقطع خاص أو الرابط غير مدعوم."}
            
            data = json.loads(match.group(1))
            
            # استخراج الروابط (V7 Engine)
            urls = []
            try:
                # محاولة استخراج الرابط من أكثر من مكان في JSON
                snap_data = data.get('props', {}).get('pageProps', {}).get('spotlightParams', {}).get('snap', {})
                if not snap_data:
                    snap_data = data.get('props', {}).get('pageProps', {}).get('story', {}).get('snaps', [{}])[0]
                
                media_url = snap_data.get('mediaUrl') or snap_data.get('media', {}).get('mediaUrl')
                if media_url: urls.append(media_url)
            except: pass

            if not urls: return {"success": False, "error": "لم يتم العثور على فيديو خام."}
            
            clean_url = urls[0].replace('\\u0026', '&')
            
            # نقطة 6 و 7: التحقق من نوع الملف وصلاحية الكتابة
            file_name = f"nexus_{uuid.uuid4().hex[:5]}.mp4"
            
            async with client.stream("GET", clean_url) as r:
                r.raise_for_status()
                # التأكد أنه فيديو فعلاً
                if "video" not in r.headers.get("content-type", "").lower():
                    return {"success": False, "error": "الرابط المستخرج ليس فيديو."}
                
                async with aiofiles.open(file_name, "wb") as f:
                    async for chunk in r.aiter_bytes():
                        await f.write(chunk)
            
            size = round(os.path.getsize(file_name) / (1024*1024), 2)
            return {"success": True, "video_url": f"/video/{file_name}", "size_mb": size, "method": "V7 PRO"}
            
        except Exception as e:
            return {"success": False, "error": f"حدث خطأ: {str(e)}"}

@app.get("/video/{name}")
async def get_video(name: str):
    if os.path.exists(name): return FileResponse(name, media_type="video/mp4")
    return JSONResponse(status_code=404, content={"error": "File expired"})

# تشغيل السيرفر يدوياً لضمان العمل على أي منصة
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
