from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from sar_agent.api import routes_upload, routes_report, routes_llm

app = FastAPI(title="SAR/STR Reporting Agent")

# Mount static files for frontend
app.mount("/static", StaticFiles(directory="sar_agent/static"), name="static")

@app.get("/")
async def root():
    return FileResponse("sar_agent/static/index.html")

# Include APIs
app.include_router(routes_upload.router, prefix="/upload", tags=["Upload"])
app.include_router(routes_report.router, prefix="/report", tags=["Report"])
app.include_router(routes_llm.router, prefix="/llm", tags=["LLM"])
