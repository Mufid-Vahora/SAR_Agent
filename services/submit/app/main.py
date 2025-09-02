from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI(title="Submit Service")


class SubmitRequest(BaseModel):
    xml_string: str
    destination: str = "mock"


@app.post("/submit")
def submit(req: SubmitRequest):
    # TODO: implement real regulator API integrations; for now, just echo
    return {"status": "queued", "destination": req.destination}


