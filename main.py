from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn
import logging
import os
from api.config_handler import load_config, add_token, remove_token, update_settings
from api.start import start_bots, stop_bots
from pathlib import Path

app = FastAPI()

# إعدادات CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "public"), name="static")

# خدمة الملفات الثابتة بشكل مباشر
@app.get("/static/{file_path:path}")
async def serve_static(file_path: str):
    static_path = BASE_DIR / "public" / file_path
    if static_path.exists():
        return FileResponse(static_path)
    return Response("File not found", status_code=404)

# خدمة الصفحة الرئيسية
@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    return FileResponse(BASE_DIR / "public" / "index.html")


# بدء البوتات عند التشغيل إذا كان الإعداد auto_start مفعل
@app.on_event("startup")
async def startup_event():
    config = load_config()
    if config and config['settings']['auto_start']:
        start_bots()
        logging.info("تم بدء البوتات تلقائياً")


# واجهة API للتحكم في البوتات
@app.post("/api/start")
async def api_start():
    start_bots()
    return {"status": "started"}

@app.post("/api/stop")
async def api_stop():
    stop_bots()
    return {"status": "stopped"}

@app.get("/api/status")
async def api_status():
    config = load_config()
    return {
        "running": bool(bots_ar or bots_gw),
        "tokens_count": len(config['tokens']) if config else 0,
        "settings": config['settings'] if config else {}
    }

@app.post("/api/tokens")
async def api_add_token(request: Request):
    data = await request.json()
    if add_token(data['token'], data['guild_ids']):
        return {"status": "success"}
    raise HTTPException(status_code=400, detail="فشل في إضافة التوكن")

@app.delete("/api/tokens/{token}")
async def api_remove_token(token: str):
    if remove_token(token):
        return {"status": "success"}
    raise HTTPException(status_code=404, detail="التوكن غير موجود")

@app.put("/api/settings")
async def api_update_settings(request: Request):
    data = await request.json()
    if update_settings(data):
        return {"status": "success"}
    raise HTTPException(status_code=400, detail="فشل في تحديث الإعدادات")


# واجهة المستخدم
@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    with open("public/index.html", "r") as f:
        return HTMLResponse(content=f.read(), status_code=200)

# تشغيل الخادم (للتطوير المحلي)
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
