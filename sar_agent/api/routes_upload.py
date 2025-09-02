from fastapi import APIRouter, UploadFile
import os
from sar_agent.core import file_handler

router = APIRouter()

@router.post("/file")
async def upload_file(file: UploadFile):
    file_path = f"temp_{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())

    if file.filename.endswith(".pdf"):
        content = file_handler.extract_text_from_pdf(file_path)
    elif file.filename.endswith(".docx"):
        content = file_handler.extract_text_from_docx(file_path)
    elif file.filename.endswith(".csv"):
        content = file_handler.extract_text_from_csv(file_path)
    elif file.filename.endswith(".xml"):
        content = file_handler.extract_text_from_xml(file_path)
    else:
        return {"error": "Unsupported file format"}

    os.remove(file_path)
    return {"filename": file.filename, "content": content[:1000]}  # preview
