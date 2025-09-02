from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import sys

# Add the sar_agent core to the path
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../sar_agent/core"))
from xsd_format_selector import XSDFormatSelector, FormatType

app = FastAPI(title="XSD Format Selector")

# Initialize the format selector
selector = XSDFormatSelector()

class AnalyzeRequest(BaseModel):
    pipe_data: str

class ValidateRequest(BaseModel):
    pipe_data: str

class FormatInfoRequest(BaseModel):
    format_type: str

@app.post("/analyze")
async def analyze_pipe_data(request: AnalyzeRequest):
    """Analyze pipe-formatted data and recommend XSD format"""
    try:
        format_type, reasoning, metrics = selector.get_format_recommendation(request.pipe_data)
        
        return {
            "recommended_format": format_type.value,
            "format_name": selector.get_format_info(format_type).get("name", "Unknown"),
            "reasoning": reasoning,
            "complexity_metrics": {
                "entities": metrics.entity_count,
                "transactions": metrics.transaction_count,
                "relationships": metrics.relationship_count,
                "documents": metrics.document_count,
                "notes": metrics.note_count,
                "custom_fields": metrics.custom_field_count,
                "geographic_coordinates": metrics.geographic_coordinates,
                "intermediaries": metrics.intermediary_count,
                "beneficial_owners": metrics.beneficial_owner_count,
                "risk_factors": metrics.risk_factors_count,
                "overall_score": metrics.total_complexity_score
            },
            "format_characteristics": selector.get_format_info(format_type).get("characteristics", {}),
            "best_for": selector.get_format_info(format_type).get("best_for", []),
            "data_requirements": selector.get_format_info(format_type).get("data_requirements", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/validate")
async def validate_pipe_data(request: ValidateRequest):
    """Validate pipe-formatted data for common issues"""
    try:
        issues = selector.validate_pipe_data(request.pipe_data)
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "issue_count": len(issues)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")

@app.get("/formats")
async def list_formats():
    """List available XSD formats with their characteristics"""
    try:
        formats = {}
        for format_type in [FormatType.COMPLEX, FormatType.SIMPLE]:
            format_info = selector.get_format_info(format_type)
            formats[format_type.value] = {
                "name": format_info.get("name", "Unknown"),
                "description": format_info.get("description", ""),
                "characteristics": format_info.get("characteristics", {}),
                "best_for": format_info.get("best_for", []),
                "data_requirements": format_info.get("data_requirements", []),
                "example_use_cases": format_info.get("example_use_cases", [])
            }
        return {"formats": formats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list formats: {str(e)}")

@app.get("/format/{format_type}")
async def get_format_info(format_type: str):
    """Get detailed information about a specific format"""
    try:
        if format_type == "format1_complex":
            format_enum = FormatType.COMPLEX
        elif format_type == "format2_simple":
            format_enum = FormatType.SIMPLE
        else:
            raise HTTPException(status_code=400, detail="Invalid format type")
        
        format_info = selector.get_format_info(format_enum)
        return {
            "format_type": format_type,
            "info": format_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get format info: {str(e)}")

@app.get("/")
def root():
    return {"service": "format_selector", "docs": "/docs", "health": "/health"}

@app.get("/health")
def health():
    return {"ok": True}
