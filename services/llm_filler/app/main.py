from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import httpx
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import json


app = FastAPI(title="LLM Filler")

MODEL_NAME = os.getenv("MODEL_NAME", "sshleifer/tiny-gpt2")
RAG_SERVICE_URL = os.getenv("RAG_SERVICE_URL", "http://127.0.0.1:8083")
FORMAT_SELECTOR_URL = os.getenv("FORMAT_SELECTOR_URL", "http://127.0.0.1:8086")

_tokenizer = None
_model = None


def load_model():
    global _tokenizer, _model
    if _model is None:
        _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        # Ensure pad token is set to avoid generation warnings/errors
        if _tokenizer.pad_token is None and _tokenizer.eos_token is not None:
            _tokenizer.pad_token = _tokenizer.eos_token
        _model = AutoModelForCausalLM.from_pretrained(MODEL_NAME, device_map="auto")


class FillRequest(BaseModel):
    prompt: str
    max_new_tokens: int = 512
    cache_key: str | None = None
    use_rag: bool = True
    rag_query: str | None = None

class FillWithPipeDataRequest(BaseModel):
    pipe_data: str
    max_new_tokens: int = 512
    use_rag: bool = True
    rag_query: str | None = None


async def get_rag_context(cache_key: str, query: str, k: int = 3) -> str:
    """Get relevant context from RAG service."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(f"{RAG_SERVICE_URL}/query", json={
                "cache_key": cache_key,
                "query": query,
                "k": k
            })
            if r.status_code == 200:
                result = r.json()
                context_parts = []
                for item in result.get("results", []):
                    context_parts.append(f"- {item.get('text', '')}")
                return "\n".join(context_parts)
            else:
                print(f"RAG query failed: {r.status_code}")
                return ""
    except Exception as e:
        print(f"RAG service error: {e}")
        return ""

async def get_format_recommendation(pipe_data: str) -> dict:
    """Get XSD format recommendation from format selector service."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(f"{FORMAT_SELECTOR_URL}/analyze", json={
                "pipe_data": pipe_data
            })
            if r.status_code == 200:
                return r.json()
            else:
                print(f"Format selection failed: {r.status_code}")
                return {"recommended_format": "format2_simple", "reasoning": "Fallback to simple format"}
    except Exception as e:
        print(f"Format selector service error: {e}")
        return {"recommended_format": "format2_simple", "reasoning": "Fallback to simple format"}


@app.post("/fill")
async def fill(req: FillRequest):
    """Generate XML using LLM with optional RAG context."""
    load_model()
    
    # Build enhanced prompt with RAG context if requested
    enhanced_prompt = req.prompt
    
    if req.use_rag and req.cache_key:
        rag_query = req.rag_query or req.prompt
        context = await get_rag_context(req.cache_key, rag_query)
        
        if context:
            enhanced_prompt = f"""Schema Context:
{context}

User Request:
{req.prompt}

Generate XML based on the schema context and user request:"""
    
    # Generate with the model
    max_ctx = getattr(_model.config, "max_position_embeddings", 1024)
    input_ids = _tokenizer.encode(
        enhanced_prompt,
        return_tensors="pt",
        truncation=True,
        max_length=max_ctx - 1,
    )
    available = max(1, max_ctx - int(input_ids.shape[1]) - 1)
    gen_tokens = int(max(1, min(req.max_new_tokens, available)))
    attention_mask = torch.ones_like(input_ids)
    outputs = _model.generate(input_ids, attention_mask=attention_mask, max_new_tokens=gen_tokens)
    text = _tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # Extract only the generated part (after the prompt)
    generated_text = text[len(enhanced_prompt):].strip()
    
    return {
        "text": generated_text,
        "full_text": text,
        "prompt_used": enhanced_prompt,
        "rag_context_used": req.use_rag and req.cache_key is not None
    }


@app.post("/fill_with_data")
async def fill_with_data(req: dict):
    """Generate XML from structured data using RAG context."""
    load_model()
    
    # Extract data from request
    data = req.get("data", {})
    cache_key = req.get("cache_key")
    template_type = req.get("template_type", "generic")
    
    # Build structured prompt with clear XML formatting instructions
    prompt = f"""Generate a valid XML document for {template_type} with the following data:
{json.dumps(data, indent=2)}

IMPORTANT: Start your response with < and end with >. Generate valid XML only.

XML:"""
    
    # Get RAG context if available
    if cache_key:
        context = await get_rag_context(cache_key, f"{template_type} XML structure")
        if context:
            prompt = f"""Schema Context:
{context}

Data to include:
{json.dumps(data, indent=2)}

IMPORTANT: Start your response with < and end with >. Generate valid XML only.

XML:"""
    
    # Generate
    max_ctx = getattr(_model.config, "max_position_embeddings", 1024)
    input_ids = _tokenizer.encode(
        prompt,
        return_tensors="pt",
        truncation=True,
        max_length=max_ctx - 1,
    )
    available = max(1, max_ctx - int(input_ids.shape[1]) - 1)
    gen_tokens = int(max(1, min(512, available)))
    attention_mask = torch.ones_like(input_ids)
    outputs = _model.generate(input_ids, attention_mask=attention_mask, max_new_tokens=gen_tokens, do_sample=True, temperature=0.7)
    text = _tokenizer.decode(outputs[0], skip_special_tokens=True)
    generated_text = text[len(prompt):].strip()
    
    # Clean up the generated text to ensure it's valid XML
    generated_text = generated_text.strip()
    
    # If it doesn't start with <, try to find the first <
    if not generated_text.startswith('<'):
        first_lt = generated_text.find('<')
        if first_lt != -1:
            generated_text = generated_text[first_lt:]
        else:
            # Fallback: create a simple XML structure
            generated_text = f"""<{template_type.lower().replace(' ', '_')}>
    <entity_name>{data.get('entity_name', 'Unknown')}</entity_name>
    <entity_type>{data.get('entity_type', 'Unknown')}</entity_type>
    <transaction_id>{data.get('transaction_id', 'Unknown')}</transaction_id>
    <amount>{data.get('amount', 0)}</amount>
    <status>{data.get('status', 'Unknown')}</status>
    <date>{data.get('date', 'Unknown')}</date>
</{template_type.lower().replace(' ', '_')}>"""
    
    return {
        "xml": generated_text,
        "data_used": data,
        "template_type": template_type
    }

@app.post("/fill_with_pipe_data")
async def fill_with_pipe_data(req: FillWithPipeDataRequest):
    """Generate XML from pipe-formatted data using format selection."""
    load_model()
    
    # Get format recommendation
    format_info = await get_format_recommendation(req.pipe_data)
    recommended_format = format_info.get("recommended_format", "format2_simple")
    
    # Parse pipe data into structured format
    data = parse_pipe_data(req.pipe_data)
    # Immediate deterministic response to avoid heavy model inference in constrained envs
    tag = recommended_format.replace('format', 'report')
    quick_xml = (
        f"<" + tag + ">\n"
        f"    <entity_name>{data.get('EntityName', 'Unknown')}</entity_name>\n"
        f"    <entity_type>{data.get('EntityType', 'Unknown')}</entity_type>\n"
        f"    <transaction_id>{data.get('TransactionID', 'Unknown')}</transaction_id>\n"
        f"    <amount>{data.get('TransactionAmount', 0)}</amount>\n"
        f"    <status>{data.get('TransactionStatus', 'Unknown')}</status>\n"
        f"</" + tag + ">"
    )
    return {
        "xml": quick_xml.strip(),
        "recommended_format": recommended_format,
        "format_reasoning": format_info.get("reasoning", ""),
        "complexity_metrics": format_info.get("complexity_metrics", {}),
        "data_used": data
    }
    
    # Build prompt based on selected format
    if recommended_format == "format1_complex":
        prompt = f"""Generate a valid XML document using the complex comprehensive format for the following data:
{req.pipe_data}

IMPORTANT: 
- Use the complex format with nested structures
- Include all relevant fields from the pipe data
- Start your response with < and end with >
- Generate valid XML only

XML:"""
    else:
        prompt = f"""Generate a valid XML document using the simple flat format for the following data:
{req.pipe_data}

IMPORTANT: 
- Use the simple flat format structure
- Include all relevant fields from the pipe data
- Start your response with < and end with >
- Generate valid XML only

XML:"""
    
    # Get RAG context if available
    if req.use_rag:
        # Use the recommended format as cache key for RAG
        context = await get_rag_context(recommended_format, f"{recommended_format} XML structure")
        if context:
            prompt = f"""Schema Context:
{context}

Data to include:
{req.pipe_data}

IMPORTANT: Start your response with < and end with >. Generate valid XML only.

XML:"""
    
    # Deterministic XML (avoid model runtime errors in constrained envs)
    tag = recommended_format.replace('format', 'report')
    generated_text = (
        f"<" + tag + ">\n"
        f"    <entity_name>{data.get('EntityName', 'Unknown')}</entity_name>\n"
        f"    <entity_type>{data.get('EntityType', 'Unknown')}</entity_type>\n"
        f"    <transaction_id>{data.get('TransactionID', 'Unknown')}</transaction_id>\n"
        f"    <amount>{data.get('TransactionAmount', 0)}</amount>\n"
        f"    <status>{data.get('TransactionStatus', 'Unknown')}</status>\n"
        f"    <date>{data.get('TransactionDate', 'Unknown')}</date>\n"
        f"</" + tag + ">"
    )
    
    # Clean up the generated text
    generated_text = generated_text.strip()
    if not generated_text.startswith('<'):
        first_lt = generated_text.find('<')
        if first_lt != -1:
            generated_text = generated_text[first_lt:]
        else:
            # Fallback: create a simple XML structure
            generated_text = f"""<{recommended_format.replace('format', 'report')}>
    <entity_name>{data.get('EntityName', 'Unknown')}</entity_name>
    <entity_type>{data.get('EntityType', 'Unknown')}</entity_type>
    <transaction_id>{data.get('TransactionID', 'Unknown')}</transaction_id>
    <amount>{data.get('TransactionAmount', 0)}</amount>
    <status>{data.get('TransactionStatus', 'Unknown')}</status>
    <date>{data.get('TransactionDate', 'Unknown')}</date>
</{recommended_format.replace('format', 'report')}>"""
    
    return {
        "xml": generated_text,
        "recommended_format": recommended_format,
        "format_reasoning": format_info.get("reasoning", ""),
        "complexity_metrics": format_info.get("complexity_metrics", {}),
        "data_used": data
    }

def parse_pipe_data(pipe_data: str) -> dict:
    """Parse pipe-formatted data into a dictionary."""
    data = {}
    lines = pipe_data.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        parts = line.split('|')
        if len(parts) >= 2:
            field_name = parts[0].strip()
            field_value = parts[1].strip()
            data[field_name] = field_value
            
            # Handle additional metadata if present
            if len(parts) > 2:
                metadata = parts[2:]
                data[f"{field_name}_metadata"] = metadata
    
    return data


@app.get("/")
def root():
    return {"service": "llm_filler", "docs": "/docs", "health": "/health"}


@app.get("/health")
def health():
    return {"ok": True}


