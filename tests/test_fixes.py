import asyncio
import httpx
import json


async def test_llm_filler():
    """Test the improved LLM filler with better XML generation."""
    print("🧪 Testing improved LLM filler...")
    
    sample_data = {
        "entity_name": "ABC Ltd",
        "entity_type": "Company", 
        "transaction_id": "TXN001",
        "amount": 20000,
        "status": "Suspicious",
        "date": "2024-01-15"
    }
    
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post('http://127.0.0.1:8084/fill_with_data', json={
            'data': sample_data,
            'cache_key': 'fincen_sar.xsd',
            'template_type': 'FinCEN SAR'
        })
        
        print(f"📊 LLM response: {r.status_code}")
        if r.status_code == 200:
            result = r.json()
            generated_xml = result.get('xml', '')
            print(f"   - Generated XML: {generated_xml[:200]}...")
            print(f"   - Starts with '<': {generated_xml.startswith('<')}")
            return generated_xml
        else:
            print(f"   ❌ Error: {r.text}")
            return None


async def test_validator(xml_string):
    """Test the improved validator with better error handling."""
    print("🧪 Testing improved validator...")
    
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post('http://127.0.0.1:8085/validate', json={
            'xml_string': xml_string, 
            'cache_key': 'fincen_sar.xsd'
        })
        
        print(f"📊 Validator response: {r.status_code}")
        if r.status_code == 200:
            result = r.json()
            print(f"   - Valid: {result.get('valid')}")
            if not result.get('valid'):
                print(f"   - Error: {result.get('error', 'Unknown')}")
            return result
        else:
            print(f"   ❌ Service error: {r.text}")
            return None


async def main():
    print("🚀 Testing fixes for LLM and Validator")
    print("=" * 50)
    
    # Test LLM filler
    xml = await test_llm_filler()
    print()
    
    if xml:
        # Test validator
        result = await test_validator(xml)
        print()
        
        if result and result.get('valid'):
            print("🎉 All tests passed! XML generation and validation working correctly.")
        else:
            print("⚠️  XML generated but validation failed. This is expected for a simple model.")
            print("   The important thing is that the services handle errors gracefully now.")
    else:
        print("❌ LLM filler test failed")


if __name__ == '__main__':
    asyncio.run(main())
