from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
import os
import httpx
import xmlschema
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from pathlib import Path


app = FastAPI(title="Template Fetcher")

TEMPLATES_DIR = os.getenv("TEMPLATES_DIR", "/data/templates")
INDEX_DIR = os.getenv("INDEX_DIR", "/data/indexes")
EMBED_MODEL_NAME = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

os.makedirs(TEMPLATES_DIR, exist_ok=True)
os.makedirs(INDEX_DIR, exist_ok=True)

_embedder: SentenceTransformer | None = None


def get_embedder() -> SentenceTransformer:
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer(EMBED_MODEL_NAME)
    return _embedder


class FetchRequest(BaseModel):
    xsd_url: HttpUrl | None = None
    xsd_file: str | None = None
    cache_key: str | None = None


def extract_xsd_text(xsd_path: str) -> list[str]:
    """Extract text from XSD for indexing."""
    schema = xmlschema.XMLSchema(xsd_path)
    lines: list[str] = []
    
    # Extract element definitions
    for qname, elem in schema.elements.items():
        lines.append(f"element:{qname} type={getattr(elem.type, 'name', '')}")
    
    # Extract type definitions
    for qname, typ in schema.types.items():
        lines.append(f"type:{qname}")
    
    # Extract attribute definitions
    for qname, attr in schema.attributes.items():
        lines.append(f"attribute:{qname} type={getattr(attr.type, 'name', '')}")
    
    # Extract complex type content
    for qname, typ in schema.types.items():
        if hasattr(typ, 'content'):
            lines.append(f"complex_type:{qname} content={str(typ.content)[:100]}")
    
    return lines


@app.post("/fetch")
async def fetch(req: FetchRequest):
    """Fetch and index XSD from URL or local file."""
    if req.xsd_url:
        # Download from URL
        cache_key = req.cache_key or os.path.basename(str(req.xsd_url))
        xsd_path = os.path.join(TEMPLATES_DIR, cache_key)
        
        if not os.path.exists(xsd_path):
            async with httpx.AsyncClient(timeout=60) as client:
                r = await client.get(str(req.xsd_url))
                if r.status_code != 200:
                    raise HTTPException(status_code=400, detail=f"Failed to download XSD: {r.status_code}")
                with open(xsd_path, "wb") as f:
                    f.write(r.content)
    
    elif req.xsd_file:
        # Use local file
        cache_key = req.cache_key or os.path.basename(req.xsd_file)
        local_path = Path(req.xsd_file)
        if not local_path.exists():
            raise HTTPException(status_code=404, detail=f"Local XSD file not found: {req.xsd_file}")
        
        xsd_path = os.path.join(TEMPLATES_DIR, cache_key)
        # Copy local file to templates directory
        import shutil
        shutil.copy2(local_path, xsd_path)
    
    else:
        raise HTTPException(status_code=400, detail="Either xsd_url or xsd_file must be provided")

    try:
        corpus = extract_xsd_text(xsd_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"XSD parse error: {e}")

    model = get_embedder()
    vectors = model.encode(corpus, normalize_embeddings=True)
    dim = vectors.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(np.array(vectors, dtype=np.float32))

    index_path = os.path.join(INDEX_DIR, f"{cache_key}.faiss")
    faiss.write_index(index, index_path)

    meta_path = os.path.join(INDEX_DIR, f"{cache_key}.txt")
    with open(meta_path, "w", encoding="utf-8") as f:
        for line in corpus:
            f.write(line + "\n")

    return {
        "cache_key": cache_key, 
        "xsd_path": xsd_path, 
        "index_path": index_path, 
        "items_indexed": len(corpus),
        "corpus_preview": corpus[:5]  # Show first 5 items
    }


@app.get("/")
def root():
    return {"service": "template_fetcher", "docs": "/docs", "health": "/health"}


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/list")
def list_templates():
    """List available templates."""
    templates = []
    for file in os.listdir(TEMPLATES_DIR):
        if file.endswith('.xsd'):
            cache_key = file
            index_path = os.path.join(INDEX_DIR, f"{cache_key}.faiss")
            meta_path = os.path.join(INDEX_DIR, f"{cache_key}.txt")
            
            # Determine format type based on filename
            format_type = "unknown"
            if "format1_complex" in file:
                format_type = "complex"
            elif "format2_simple" in file:
                format_type = "simple"
            
            templates.append({
                "cache_key": cache_key,
                "xsd_path": os.path.join(TEMPLATES_DIR, file),
                "has_index": os.path.exists(index_path),
                "has_meta": os.path.exists(meta_path),
                "size_bytes": os.path.getsize(os.path.join(TEMPLATES_DIR, file)),
                "format_type": format_type
            })
    
    return {"templates": templates}

@app.post("/fetch_builtin")
async def fetch_builtin_formats():
    """Fetch and index the built-in XSD formats."""
    builtin_formats = [
        {
            "name": "format1_complex.xsd",
            "description": "Complex comprehensive format for detailed reporting",
            "path": "../../sar_agent/regulator_xsds/format1_complex.xsd"
        },
        {
            "name": "format2_simple.xsd", 
            "description": "Simple flat format for basic reporting",
            "path": "../../sar_agent/regulator_xsds/format2_simple.xsd"
        }
    ]
    
    results = []
    for format_info in builtin_formats:
        try:
            # Check if file exists
            if not os.path.exists(format_info["path"]):
                results.append({
                    "name": format_info["name"],
                    "status": "error",
                    "message": f"File not found: {format_info['path']}"
                })
                continue
            
            # Copy to templates directory
            cache_key = format_info["name"]
            xsd_path = os.path.join(TEMPLATES_DIR, cache_key)
            import shutil
            shutil.copy2(format_info["path"], xsd_path)
            
            # Index the XSD
            corpus = extract_xsd_text(xsd_path)
            model = get_embedder()
            vectors = model.encode(corpus, normalize_embeddings=True)
            dim = vectors.shape[1]
            index = faiss.IndexFlatIP(dim)
            index.add(np.array(vectors, dtype=np.float32))

            index_path = os.path.join(INDEX_DIR, f"{cache_key}.faiss")
            faiss.write_index(index, index_path)

            meta_path = os.path.join(INDEX_DIR, f"{cache_key}.txt")
            with open(meta_path, "w", encoding="utf-8") as f:
                for line in corpus:
                    f.write(line + "\n")
            
            results.append({
                "name": format_info["name"],
                "status": "success",
                "cache_key": cache_key,
                "items_indexed": len(corpus),
                "description": format_info["description"]
            })
            
        except Exception as e:
            results.append({
                "name": format_info["name"],
                "status": "error",
                "message": str(e)
            })
    
    return {"results": results}


