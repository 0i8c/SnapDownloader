import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import httpx

app = FastAPI()

# التأكد من وجود ملف index.html وقراءته
@app.get("/", response_class=HTMLResponse)
async def read_index():
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"<h1>خطأ في قراءة ملف index.html: {str(e)}</h1>"

# مسار تجريبي للتأكد أن السيرفر يستجيب
@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "NEXUS IS ALIVE"}

# مسار التحميل (API)
@app.post("/api/download")
async def download_video(request: Request):
    try:
        data = await request.json()
        url = data.get("url")
        # هنا المحرك يشتغل.. للآن بنرجع استجابة تجريبية للتأكد من الربط
        return {"success": True, "video_url": "#", "size_mb": "0.0", "method": "Connected"}
    except Exception as e:
        return {"success": False, "error": str(e)}
