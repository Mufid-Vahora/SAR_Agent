from fastapi import APIRouter
from pydantic import BaseModel
from sar_agent.core.llm_engine import LLMEngine

router = APIRouter()
llm = LLMEngine()

class PromptRequest(BaseModel):
    prompt: str

@router.post("/generate")
async def generate_text(request: PromptRequest):
    response = llm.generate(request.prompt)
    return {"response": response}
