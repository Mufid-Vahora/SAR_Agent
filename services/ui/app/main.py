from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse
from jinja2 import Template
import httpx


app = FastAPI(title="HITL UI")


INDEX_HTML = Template(
    """
    <html>
    <body>
      <h1>SAR Agent UI</h1>
      <form action="/upload" method="post" enctype="multipart/form-data">
        <input type="file" name="file" />
        <button type="submit">Upload & Start</button>
      </form>
      <div id="result"></div>
    </body>
    </html>
    """
)


@app.get("/", response_class=HTMLResponse)
async def index():
    return INDEX_HTML.render()


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    async with httpx.AsyncClient() as client:
        files = {"file": (file.filename, await file.read(), file.content_type)}
        r = await client.post("http://orchestrator:8080/api/jobs/upload", files=files)
        r.raise_for_status()
        job = r.json()
        await client.post(f"http://orchestrator:8080/api/jobs/{job['job_id']}/start", json={})
    return {"job_id": job["job_id"]}


