import os
import re
import json
import time
import uuid
import asyncio
import logging
import aiofiles
import httpx
from urllib.parse import unquote, urlparse
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from pydantic import BaseModel

# ---------------------------------------------------------
# ⚙️ 1. إعدادات السيرفر الأساسية (FastAPI)
# ---------------------------------------------------------
app = FastAPI(title="NEXUS PRO MAX - V7")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')

CB_STATE = {"failures": 0, "last_fail": 0, "is_open": False}
CB_THRESHOLD = 5
CB_COOLDOWN = 30 
CACHE = {}
CACHE_LOCK = asyncio.Lock()
MAX_CONCURRENT_DOWNLOADS = asyncio.Semaphore(10)

class SnapRequest(BaseModel):
    url: str

# ---------------------------------------------------------
# 🛡️ 2. دوال الحماية والاستخراج (V7 Engine)
# ---------------------------------------------------------
def is_safe_domain(url: str) -> bool:
    try:
        netloc = urlparse(url).netloc.lower()
        return netloc.endswith(('.snapchat.com', 'snapchat.com', '.sc-cdn.net', 'sc-cdn.net'))
    except:
        return False

def get_clean_snap_video(data: dict) -> list:
    """استخراج النسخة الخام (النظيفة) من المسارات الرسمية مباشرة"""
    clean_urls = set()
    try:
        spotlight = data.get('props', {}).get('pageProps', {}).get('spotlightParams', {}).get('snap', {}).get('mediaUrl')
        if spotlight and is_safe_domain(spotlight): clean_urls.add(spotlight)

        snaps = data.get('props', {}).get('pageProps', {}).get('story', {}).get('snaps', [])
        for snap in snaps:
            story_media = snap.get('media', {}).get('mediaUrl')
            if story_media and is_safe_domain(story_media): clean_urls.add(story_media)
    except: pass
    return [u for u in clean_urls if ".mp4" in u or ".m3u8" in u]

def deep_search_safe(data, max_depth=10):
    results = set()
    stack = [(data, 0)]
    junk = re.compile(r'(?i)(thumb|preview|analytics|pixel|sprite|icon|avatar|log)')
    while stack:
        current, depth = stack.pop()
        if depth > max_depth: continue
        if isinstance(current, dict):
            for k, v in current.items():
                if isinstance(v, str) and (".mp4" in v.lower() or ".m3u8" in v.lower()):
                    if not junk.search(v) and is_safe_domain(v): results.add(v)
                elif isinstance(v, (dict, list)): stack.append((v, depth + 1))
        elif isinstance(current, list):
            for item in current: stack.append((item, depth + 1))
    return list(results)

async def verify_real_size(url: str, client: httpx.AsyncClient):
    if ".m3u8" in url: return url, 0
    try:
        resp = await client.head(url, follow_redirects=True, timeout=3.0)
        return url, int(resp.headers.get("content-length", 0))
    except: return url, -1

async def cleanup_stale_files():
    """تنظيف الفيديوهات القديمة لحماية مساحة السيرفر"""
    try:
        now = time.time()
        for f in os.listdir("."):
            if f.startswith("nexus_") and f.endswith(".mp4") and (now - os.path.getmtime(f) > 3600):
                os.remove(f)
    except: pass

# ---------------------------------------------------------
# 🌐 3. مسارات الـ API (الواجهة والتحميل)
# ---------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """عرض واجهة المستخدم الزجاجية (index.html)"""
    try:
        async with aiofiles.open("index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=await f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>خطأ: ملف index.html غير موجود في السيرفر</h1>", status_code=404)

@app.post("/api/download")
async def api_download(req: SnapRequest, bg_tasks: BackgroundTasks):
    """المسار الذي يستقبل الرابط من الواجهة ويبدأ التحميل"""
    url = req.url.strip()
    global CB_STATE

    if CB_STATE["is_open"]:
        if time.time() - CB_STATE["last_fail"] > CB_COOLDOWN:
            CB_STATE["is_open"] = False
            CB_STATE["failures"] = 0
        else:
            return {"success": False, "error": "النظام متوقف مؤقتاً بسبب ضغط السيرفرات."}

    if not is_safe_domain(url):
        return {"success": False, "error": "الرابط غير مصرح به أمنياً أو ليس من سناب شات."}

    async with CACHE_LOCK:
        if url in CACHE and os.path.exists(CACHE[url]):
            size_mb = round(os.path.getsize(CACHE[url]) / (1024 * 1024), 2)
            return {"success": True, "video_url": f"/video/{CACHE[url]}", "size_mb": size_mb, "method": "Cache Hit"}

    bg_tasks.add_task(cleanup_stale_files)
    timeout_config = httpx.Timeout(connect=5.0, read=15.0, write=30.0, pool=10.0)
    
    async with MAX_CONCURRENT_DOWNLOADS:
        try:
            async with httpx.AsyncClient(verify=True, timeout=timeout_config) as client:
                client.headers.update({"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4)"})
                page_resp = await client.get(url, follow_redirects=True)
                page_resp.raise_for_status()
                content = page_resp.text

                candidates = []
                method = ""

                json_match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', content, re.DOTALL)
                if json_match:
                    try:
                        data = json.loads(json_match.group(1))
                        candidates = get_clean_snap_video(data)
                        if candidates: method = "Targeted Path (RAW)"
                        else:
                            candidates = deep_search_safe(data)
                            method = "Deep Search (Fallback)"
                    except: pass

                if not candidates:
                    return {"success": False, "error": "لم يتم العثور على أي فيديو قابل للتحليل."}

                candidates = list(set(candidates))
                def heuristic(u): return ("orig" in u.lower())*3 + ("1080" in u)*2
                top_3 = sorted(candidates, key=heuristic, reverse=True)[:3]

                size_checks = await asyncio.gather(*(verify_real_size(u, client) for u in top_3))
                best_url = max(size_checks, key=lambda x: x[1])[0]
                best_url = unquote(best_url).replace('\\u0026', '&')

                if ".m3u8" in best_url:
                    return {"success": False, "error": "الفيديو بصيغة بث مباشر (m3u8) ولا يمكن تحميله كـ MP4 مباشرة."}

                file_id = f"nexus_{int(time.time())}_{uuid.uuid4().hex[:6]}"
                temp_path = f"{file_id}.part"
                final_path = f"{file_id}.mp4"
                downloaded_bytes = 0

                try:
                    async with client.stream("GET", best_url, follow_redirects=True) as stream_resp:
                        stream_resp.raise_for_status()
                        if "video" not in stream_resp.headers.get("content-type", "").lower():
                            return {"success": False, "error": "الرابط المستخرج ليس فيديو صالح."}

                        async with aiofiles.open(temp_path, "wb") as f:
                            async for chunk in stream_resp.aiter_bytes(chunk_size=65536):
                                if chunk:
                                    downloaded_bytes += len(chunk)
                                    if downloaded_bytes > 150 * 1024 * 1024:
                                        raise ValueError("Exceeds 150MB limit")
                                    await f.write(chunk)
                                    
                    os.rename(temp_path, final_path)
                    async with CACHE_LOCK: CACHE[url] = final_path
                    CB_STATE["failures"] = max(0, CB_STATE["failures"] - 1)
                    
                    size_mb = round(downloaded_bytes / (1024 * 1024), 2)
                    return {"success": True, "video_url": f"/video/{final_path}", "size_mb": size_mb, "method": method}

                except Exception as e:
                    if os.path.exists(temp_path): os.remove(temp_path)
                    raise e

        except Exception as e:
            CB_STATE["failures"] += 1
            if CB_STATE["failures"] >= CB_THRESHOLD:
                CB_STATE["is_open"] = True
                CB_STATE["last_fail"] = time.time()
            return {"success": False, "error": f"فشل الاتصال: {str(e)}"}

@app.get("/video/{filename}")
async def serve_video(filename: str):
    """تقديم ملف الفيديو النهائي للمتصفح"""
    if os.path.exists(filename) and filename.endswith(".mp4"):
        return FileResponse(filename, media_type="video/mp4", headers={"Content-Disposition": f"attachment; filename={filename}"})
    return JSONResponse(status_code=404, content={"error": "الفيديو غير موجود أو انتهت صلاحيته."})
