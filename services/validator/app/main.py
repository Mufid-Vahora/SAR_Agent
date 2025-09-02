from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import xmlschema
from lxml import etree


app = FastAPI(title="XML Validator")

TEMPLATES_DIR = os.getenv("TEMPLATES_DIR", "/data/templates")


class ValidateRequest(BaseModel):
    xml_string: str
    cache_key: str

class ValidateWithFormatRequest(BaseModel):
    xml_string: str
    format_type: str  # "format1_complex" or "format2_simple"


@app.post("/validate")
def validate(req: ValidateRequest):
    xsd_path = os.path.join(TEMPLATES_DIR, req.cache_key)
    if not os.path.exists(xsd_path):
        raise HTTPException(status_code=404, detail="XSD not found")
    
    try:
        schema = xmlschema.XMLSchema(xsd_path)
        
        # First, try to parse the XML string
        try:
            xml_doc = etree.fromstring(req.xml_string.encode("utf-8"))
        except etree.XMLSyntaxError as e:
            return {"valid": False, "error": f"XML parsing error: {str(e)}"}
        except Exception as e:
            return {"valid": False, "error": f"XML parsing failed: {str(e)}"}
        
        # Now validate against schema
        try:
            schema.validate(xml_doc)
            return {"valid": True, "message": "XML is valid according to schema"}
        except xmlschema.validators.exceptions.XMLSchemaValidationError as e:
            return {"valid": False, "error": f"Schema validation failed: {str(e)}"}
        except Exception as e:
            return {"valid": False, "error": f"Schema validation error: {str(e)}"}
            
    except Exception as e:
        return {"valid": False, "error": f"Validation process failed: {str(e)}"}


@app.post("/validate_with_format")
def validate_with_format(req: ValidateWithFormatRequest):
    """Validate XML against a specific XSD format."""
    # Map format types to XSD files
    format_mapping = {
        "format1_complex": "format1_complex.xsd",
        "format2_simple": "format2_simple.xsd"
    }
    
    if req.format_type not in format_mapping:
        raise HTTPException(status_code=400, detail="Invalid format type")
    
    xsd_file = format_mapping[req.format_type]
    xsd_path = os.path.join(TEMPLATES_DIR, xsd_file)
    
    if not os.path.exists(xsd_path):
        raise HTTPException(status_code=404, detail=f"XSD file not found: {xsd_file}")
    
    try:
        schema = xmlschema.XMLSchema(xsd_path)
        
        # First, try to parse the XML string
        try:
            xml_doc = etree.fromstring(req.xml_string.encode("utf-8"))
        except etree.XMLSyntaxError as e:
            return {
                "valid": False, 
                "error": f"XML parsing error: {str(e)}",
                "format_type": req.format_type
            }
        except Exception as e:
            return {
                "valid": False, 
                "error": f"XML parsing error: {str(e)}",
                "format_type": req.format_type
            }
        
        # Now validate against schema
        try:
            schema.validate(xml_doc)
            return {
                "valid": True, 
                "message": f"XML is valid according to {req.format_type} schema",
                "format_type": req.format_type
            }
        except xmlschema.validators.exceptions.XMLSchemaValidationError as e:
            return {
                "valid": False, 
                "error": f"Schema validation failed: {str(e)}",
                "format_type": req.format_type
            }
        except Exception as e:
            return {
                "valid": False, 
                "error": f"Schema validation error: {str(e)}",
                "format_type": req.format_type
            }
            
    except Exception as e:
        return {
            "valid": False, 
            "error": f"Validation process failed: {str(e)}",
            "format_type": req.format_type
        }


@app.get("/")
def root():
    return {"service": "validator", "docs": "/docs", "health": "/health"}


@app.get("/health")
def health():
    return {"ok": True}


