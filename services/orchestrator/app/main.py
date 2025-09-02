from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import httpx
import json

app = FastAPI(title="SAR Agent Orchestrator")

# Service URLs
FORMAT_SELECTOR_URL = os.getenv("FORMAT_SELECTOR_URL", "http://127.0.0.1:8086")
LLM_FILLER_URL = os.getenv("LLM_FILLER_URL", "http://127.0.0.1:8084")
VALIDATOR_URL = os.getenv("VALIDATOR_URL", "http://127.0.0.1:8085")
TEMPLATE_FETCHER_URL = os.getenv("TEMPLATE_FETCHER_URL", "http://127.0.0.1:8082")

class PipelineRequest(BaseModel):
    pipe_data: str
    validate_output: bool = True
    use_rag: bool = True

class PipelineResponse(BaseModel):
    success: bool
    recommended_format: str
    format_reasoning: str
    generated_xml: str
    validation_result: dict
    complexity_metrics: dict
    pipeline_steps: list

@app.post("/pipeline")
async def run_complete_pipeline(request: PipelineRequest):
    """Run the complete pipeline: format selection -> XML generation -> validation"""
    pipeline_steps = []
    
    try:
        # Step 1: Analyze pipe data and select format
        pipeline_steps.append("Format selection started")
        format_info = await call_format_selector(request.pipe_data)
        recommended_format = format_info.get("recommended_format", "format2_simple")
        pipeline_steps.append(f"Format selected: {recommended_format}")
        
        # Step 2: Generate XML using the selected format
        pipeline_steps.append("XML generation started")
        xml_result = await call_llm_filler(request.pipe_data, request.use_rag)
        generated_xml = xml_result.get("xml", "")
        pipeline_steps.append("XML generated successfully")
        
        # Step 3: Validate the generated XML
        validation_result = {"valid": False, "error": "Validation skipped"}
        if request.validate_output and generated_xml:
            pipeline_steps.append("XML validation started")
            validation_result = await call_validator(generated_xml, recommended_format)
            pipeline_steps.append(f"XML validation completed: {validation_result.get('valid', False)}")
        
        # Step 4: Ensure XSD templates are available
        pipeline_steps.append("Template availability check started")
        await ensure_templates_available()
        pipeline_steps.append("Templates verified")
        
        return PipelineResponse(
            success=True,
            recommended_format=recommended_format,
            format_reasoning=format_info.get("reasoning", ""),
            generated_xml=generated_xml,
            validation_result=validation_result,
            complexity_metrics=format_info.get("complexity_metrics", {}),
            pipeline_steps=pipeline_steps
        )
        
    except Exception as e:
        pipeline_steps.append(f"Pipeline failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Pipeline execution failed: {str(e)}")

async def call_format_selector(pipe_data: str) -> dict:
    """Call the format selector service."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(f"{FORMAT_SELECTOR_URL}/analyze", json={
                "pipe_data": pipe_data
            })
            r.raise_for_status()
            return r.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Format selector service error: {str(e)}")

async def call_llm_filler(pipe_data: str, use_rag: bool) -> dict:
    """Call the LLM filler service."""
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(f"{LLM_FILLER_URL}/fill_with_pipe_data", json={
                "pipe_data": pipe_data,
                "use_rag": False,
                "max_new_tokens": 128
            })
            r.raise_for_status()
            return r.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM filler service error: {str(e)}")

async def call_validator(xml_string: str, format_type: str) -> dict:
    """Call the validator service."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(f"{VALIDATOR_URL}/validate_with_format", json={
                "xml_string": xml_string,
                "format_type": format_type
            })
            r.raise_for_status()
            return r.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validator service error: {str(e)}")

async def ensure_templates_available():
    """Ensure that the required XSD templates are available."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            # Check if templates are already available
            r = await client.get(f"{TEMPLATE_FETCHER_URL}/list")
            if r.status_code == 200:
                templates = r.json().get("templates", [])
                template_names = [t["cache_key"] for t in templates]
                
                # If both formats are available, we're good
                if "format1_complex.xsd" in template_names and "format2_simple.xsd" in template_names:
                    return
                
                # Otherwise, fetch the builtin formats
                r = await client.post(f"{TEMPLATE_FETCHER_URL}/fetch_builtin")
                if r.status_code != 200:
                    print(f"Warning: Failed to fetch builtin formats: {r.status_code}")
                    
    except Exception as e:
        print(f"Warning: Template availability check failed: {str(e)}")

@app.get("/health")
async def health():
    """Health check for the orchestrator service."""
    try:
        # Check all dependent services
        services = {
            "format_selector": FORMAT_SELECTOR_URL,
            "llm_filler": LLM_FILLER_URL,
            "validator": VALIDATOR_URL,
            "template_fetcher": TEMPLATE_FETCHER_URL
        }
        
        health_status = {}
        async with httpx.AsyncClient(timeout=10) as client:
            for service_name, url in services.items():
                try:
                    r = await client.get(f"{url}/health")
                    health_status[service_name] = r.status_code == 200
                except:
                    health_status[service_name] = False
        
        return {
            "orchestrator": True,
            "dependent_services": health_status,
            "all_healthy": all(health_status.values())
        }
    except Exception as e:
        return {
            "orchestrator": True,
            "dependent_services": {},
            "all_healthy": False,
            "error": str(e)
        }

@app.get("/")
def root():
    return {"service": "orchestrator", "docs": "/docs", "health": "/health"}


