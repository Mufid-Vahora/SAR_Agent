import asyncio
import httpx
import os
import json
from pathlib import Path


HOST = os.environ.get('SMOKE_HOST', '127.0.0.1')


async def wait_healthy(client: httpx.AsyncClient, url: str, attempts: int = 30, delay: float = 1.0):
    print(f"Waiting for {url} to be healthy...")
    for i in range(attempts):
        try:
            r = await client.get(url)
            if r.status_code == 200:
                print(f"✅ {url} is healthy")
                return
        except Exception as e:
            print(f"⏳ Attempt {i+1}/{attempts}: {url} not ready yet ({e})")
        await asyncio.sleep(delay)
    raise RuntimeError(f'Service not healthy at {url}')


async def main():
    print("🚀 Starting SAR Agent Full Pipeline Test")
    print("=" * 50)
    
    # Read sample XML file
    sample_xml_path = Path("sar_agent/sample_files/str_template.xml")
    if not sample_xml_path.exists():
        print(f"❌ Sample file not found: {sample_xml_path}")
        return
    
    with open(sample_xml_path, 'r') as f:
        sample_xml = f.read()
    
    print(f"📄 Sample XML loaded ({len(sample_xml)} chars):")
    print(sample_xml)
    print()
    
    # Service URLs
    base2 = f'http://{HOST}:8082'  # Template Fetcher
    base3 = f'http://{HOST}:8083'  # RAG
    base4 = f'http://{HOST}:8084'  # LLM Filler
    base5 = f'http://{HOST}:8085'  # Validator
    
    async with httpx.AsyncClient(timeout=60) as client:
        print("🔍 Step 1: Checking service health...")
        await wait_healthy(client, f'{base2}/health')
        await wait_healthy(client, f'{base3}/health')
        await wait_healthy(client, f'{base4}/health')
        await wait_healthy(client, f'{base5}/health')
        print()
        
        print("📥 Step 2: Fetching XSD template...")
        xsd_url = 'https://www.w3.org/2001/XMLSchema.xsd'
        r = await client.post(f'{base2}/fetch', json={'xsd_url': xsd_url, 'cache_key': 'Schema.xsd'})
        print(f"📊 Template fetch result: {r.status_code}")
        if r.status_code == 200:
            result = r.json()
            print(f"   - Cache key: {result.get('cache_key')}")
            print(f"   - Items indexed: {result.get('items_indexed')}")
            print(f"   - XSD path: {result.get('xsd_path')}")
            print(f"   - Index path: {result.get('index_path')}")
        r.raise_for_status()
        print()
        
        print("🔍 Step 3: Querying RAG for relevant schema elements...")
        r = await client.post(f'{base3}/query', json={
            'cache_key': 'Schema.xsd', 
            'query': 'element name and type definition', 
            'k': 5
        })
        print(f"📊 RAG query result: {r.status_code}")
        if r.status_code == 200:
            result = r.json()
            print(f"   - Found {len(result.get('results', []))} relevant elements:")
            for i, item in enumerate(result.get('results', [])[:3]):
                print(f"     {i+1}. {item.get('text', '')[:80]}... (score: {item.get('score', 0):.3f})")
        r.raise_for_status()
        print()
        
        print("🤖 Step 4: Testing LLM with sample XML generation...")
        prompt = f"Generate a valid XML document similar to this structure: {sample_xml}"
        r = await client.post(f'{base4}/fill', json={'prompt': prompt, 'max_new_tokens': 256})
        print(f"📊 LLM generation result: {r.status_code}")
        if r.status_code == 200:
            result = r.json()
            generated_text = result.get('text', '')
            print(f"   - Generated text length: {len(generated_text)} chars")
            print(f"   - Preview: {generated_text[:200]}...")
        r.raise_for_status()
        print()
        
        print("✅ Step 5: Validating sample XML against schema...")
        r = await client.post(f'{base5}/validate', json={
            'xml_string': sample_xml, 
            'cache_key': 'Schema.xsd'
        })
        print(f"📊 Validation result: {r.status_code}")
        if r.status_code == 200:
            result = r.json()
            if result.get('valid'):
                print("   ✅ XML is valid according to schema")
            else:
                print(f"   ❌ XML validation failed: {result.get('error', 'Unknown error')}")
        r.raise_for_status()
        print()
        
        print("🎯 Step 6: Testing with a valid XML Schema document...")
        valid_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="test" type="xs:string"/>
</xs:schema>'''
        r = await client.post(f'{base5}/validate', json={
            'xml_string': valid_xml, 
            'cache_key': 'Schema.xsd'
        })
        print(f"📊 Schema validation result: {r.status_code}")
        if r.status_code == 200:
            result = r.json()
            if result.get('valid'):
                print("   ✅ XML Schema document is valid")
            else:
                print(f"   ❌ Schema validation failed: {result.get('error', 'Unknown error')}")
        r.raise_for_status()
        print()
        
        print("📋 Step 7: Service status summary...")
        for service_name, url in [
            ("Template Fetcher", f'{base2}'),
            ("RAG Service", f'{base3}'),
            ("LLM Filler", f'{base4}'),
            ("Validator", f'{base5}')
        ]:
            try:
                r = await client.get(f'{url}/')
                if r.status_code == 200:
                    print(f"   ✅ {service_name}: {url}")
                else:
                    print(f"   ⚠️  {service_name}: {url} (status: {r.status_code})")
            except Exception as e:
                print(f"   ❌ {service_name}: {url} (error: {e})")
        print()
        
        print("🎉 Full pipeline test completed successfully!")
        print("=" * 50)


if __name__ == '__main__':
    asyncio.run(main())
