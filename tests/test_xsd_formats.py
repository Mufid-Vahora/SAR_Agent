import asyncio
import httpx
import os
import pytest

HOST = os.environ.get('TEST_HOST', '127.0.0.1')

class TestXSDFormats:
    """Test the XSD format selection and XML generation functionality."""
    
    @pytest.fixture
    async def client(self):
        async with httpx.AsyncClient(timeout=60) as client:
            yield client
    
    async def test_format_selector_service(self, client):
        """Test the format selector service."""
        base_url = f'http://{HOST}:8086'
        
        # Test simple data (should select simple format)
        simple_data = """EntityName|Test Corp|Type:Company|Structure:LLC
TransactionID|TXN-001|Type:Wire|Status:Completed|Amount:50000.00"""
        
        r = await client.post(f'{base_url}/analyze', json={'pipe_data': simple_data})
        assert r.status_code == 200
        result = r.json()
        assert result['recommended_format'] == 'format2_simple'
        assert 'reasoning' in result
        assert 'complexity_metrics' in result
        
        # Test complex data (should select complex format)
        complex_data = """EntityName|TechCorp Solutions LLC|Type:Company|Structure:LLC
RelatedEntity1|TechCorp Holdings Inc|Type:Parent Company|Relationship:100% Ownership
RelatedEntity2|TechCorp International Ltd|Type:Subsidiary|Relationship:Majority Control
TransactionID1|TXN-001|Type:Wire|Status:Completed|Amount:50000.00
TransactionID2|TXN-002|Type:ACH|Status:Suspicious|Amount:75000.00
RiskFactors|Unusual Transaction Pattern|Severity:High|Confidence:85%|Source:AI Analysis
Document1|Corporate Registration|Type:Legal|Date:2020-03-15|Status:Valid
Note1|Initial review indicates potential structuring activity."""
        
        r = await client.post(f'{base_url}/analyze', json={'pipe_data': complex_data})
        assert r.status_code == 200
        result = r.json()
        assert result['recommended_format'] == 'format1_complex'
        assert result['complexity_metrics']['overall_score'] > 5.0
        
        # Test validation endpoint
        r = await client.post(f'{base_url}/validate', json={'pipe_data': simple_data})
        assert r.status_code == 200
        result = r.json()
        assert 'valid' in result
        assert 'issues' in result
        
        # Test formats listing
        r = await client.get(f'{base_url}/formats')
        assert r.status_code == 200
        result = r.json()
        assert 'format1_complex' in result['formats']
        assert 'format2_simple' in result['formats']
        
        # Test specific format info
        r = await client.get(f'{base_url}/format/format1_complex')
        assert r.status_code == 200
        result = r.json()
        assert result['format_type'] == 'format1_complex'
        assert 'info' in result
    
    async def test_llm_filler_with_formats(self, client):
        """Test the LLM filler service with format selection."""
        base_url = f'http://{HOST}:8084'
        
        # Test with pipe data
        pipe_data = """EntityName|Test Corp|Type:Company|Structure:LLC
TransactionID|TXN-001|Type:Wire|Status:Completed|Amount:50000.00
RiskLevel|High|Score:8.5|Threshold:7.0"""
        
        r = await client.post(f'{base_url}/fill_with_pipe_data', json={
            'pipe_data': pipe_data,
            'use_rag': False,
            'max_new_tokens': 512
        })
        assert r.status_code == 200
        result = r.json()
        assert 'xml' in result
        assert 'recommended_format' in result
        assert 'format_reasoning' in result
        assert 'complexity_metrics' in result
        assert result['xml'].strip().startswith('<')
        assert result['xml'].strip().endswith('>')
    
    async def test_validator_with_formats(self, client):
        """Test the validator service with different formats."""
        base_url = f'http://{HOST}:8085'
        
        # Test simple format validation
        simple_xml = """<SimpleReport xmlns:simple="http://www.regulator.gov/simple">
    <simple:ReportID>SAR-2024-001</simple:ReportID>
    <simple:EntityName>Test Corp</simple:EntityName>
    <simple:TransactionID>TXN-001</simple:TransactionID>
</SimpleReport>"""
        
        r = await client.post(f'{base_url}/validate_with_format', json={
            'xml_string': simple_xml,
            'format_type': 'format2_simple'
        })
        assert r.status_code == 200
        result = r.json()
        assert 'valid' in result
        assert 'format_type' in result
        assert result['format_type'] == 'format2_simple'
        
        # Test complex format validation
        complex_xml = """<ComplexReport xmlns:complex="http://www.regulator.gov/complex" reportId="SAR-2024-001" version="1.0">
    <complex:ReportHeader>
        <complex:FilingDate>2024-12-15T10:30:00Z</complex:FilingDate>
        <complex:ReportType>Initial</complex:ReportType>
    </complex:ReportHeader>
    <complex:Entities>
        <complex:PrimaryEntity>
            <complex:Name>Test Corp</complex:Name>
            <complex:Type>Company</complex:Type>
        </complex:PrimaryEntity>
    </complex:Entities>
</ComplexReport>"""
        
        r = await client.post(f'{base_url}/validate_with_format', json={
            'xml_string': complex_xml,
            'format_type': 'format1_complex'
        })
        assert r.status_code == 200
        result = r.json()
        assert 'valid' in result
        assert 'format_type' in result
        assert result['format_type'] == 'format1_complex'
    
    async def test_orchestrator_pipeline(self, client):
        """Test the complete orchestrator pipeline."""
        base_url = f'http://{HOST}:8087'
        
        # Test with simple data
        simple_data = """EntityName|Test Corp|Type:Company|Structure:LLC
TransactionID|TXN-001|Type:Wire|Status:Completed|Amount:50000.00"""
        
        r = await client.post(f'{base_url}/pipeline', json={
            'pipe_data': simple_data,
            'validate_output': True,
            'use_rag': True
        })
        assert r.status_code == 200
        result = r.json()
        assert result['success'] == True
        assert 'recommended_format' in result
        assert 'generated_xml' in result
        assert 'validation_result' in result
        assert 'complexity_metrics' in result
        assert 'pipeline_steps' in result
        assert len(result['pipeline_steps']) > 0
        
        # Test with complex data
        complex_data = """EntityName|TechCorp Solutions LLC|Type:Company|Structure:LLC
RelatedEntity1|TechCorp Holdings Inc|Type:Parent Company|Relationship:100% Ownership
TransactionID1|TXN-001|Type:Wire|Status:Completed|Amount:50000.00
TransactionID2|TXN-002|Type:ACH|Status:Suspicious|Amount:75000.00
RiskFactors|Unusual Transaction Pattern|Severity:High|Confidence:85%"""
        
        r = await client.post(f'{base_url}/pipeline', json={
            'pipe_data': complex_data,
            'validate_output': True,
            'use_rag': True
        })
        assert r.status_code == 200
        result = r.json()
        assert result['success'] == True
        assert result['recommended_format'] == 'format1_complex'
        
        # Test health endpoint
        r = await client.get(f'{base_url}/health')
        assert r.status_code == 200
        result = r.json()
        assert result['orchestrator'] == True
        assert 'dependent_services' in result
    
    async def test_template_fetcher_builtin_formats(self, client):
        """Test the template fetcher service with builtin formats."""
        base_url = f'http://{HOST}:8082'
        
        # Test fetching builtin formats
        r = await client.post(f'{base_url}/fetch_builtin')
        assert r.status_code == 200
        result = r.json()
        assert 'results' in result
        
        # Check that both formats are available
        format_names = [r['name'] for r in result['results']]
        assert 'format1_complex.xsd' in format_names
        assert 'format2_simple.xsd' in format_names
        
        # Test listing templates
        r = await client.get(f'{base_url}/list')
        assert r.status_code == 200
        result = r.json()
        assert 'templates' in result
        
        # Check that templates have format type information
        templates = result['templates']
        format_types = [t.get('format_type') for t in templates if 'format_type' in t]
        assert 'complex' in format_types
        assert 'simple' in format_types

async def main():
    """Run the tests."""
    print("Testing XSD Format Functionality...")
    
    async with httpx.AsyncClient(timeout=60) as client:
        test_instance = TestXSDFormats()
        
        # Test format selector
        print("Testing Format Selector Service...")
        await test_instance.test_format_selector_service(client)
        print("✓ Format Selector Service tests passed")
        
        # Test LLM filler with formats
        print("Testing LLM Filler with Formats...")
        await test_instance.test_llm_filler_with_formats(client)
        print("✓ LLM Filler with Formats tests passed")
        
        # Test validator with formats
        print("Testing Validator with Formats...")
        await test_instance.test_validator_with_formats(client)
        print("✓ Validator with Formats tests passed")
        
        # Test orchestrator pipeline
        print("Testing Orchestrator Pipeline...")
        await test_instance.test_orchestrator_pipeline(client)
        print("✓ Orchestrator Pipeline tests passed")
        
        # Test template fetcher builtin formats
        print("Testing Template Fetcher Builtin Formats...")
        await test_instance.test_template_fetcher_builtin_formats(client)
        print("✓ Template Fetcher Builtin Formats tests passed")
    
    print("\n🎉 All XSD Format tests passed successfully!")

if __name__ == '__main__':
    asyncio.run(main())
