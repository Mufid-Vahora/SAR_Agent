import asyncio
import httpx
import os


HOST = os.environ.get('SMOKE_HOST', '127.0.0.1')


async def wait_healthy(client: httpx.AsyncClient, url: str, attempts: int = 30, delay: float = 1.0):
    for _ in range(attempts):
        try:
            r = await client.get(url)
            if r.status_code == 200:
                return
        except Exception:
            pass
        await asyncio.sleep(delay)
    raise RuntimeError(f'Service not healthy at {url}')


async def main():
    xsd_url = 'https://www.w3.org/2001/XMLSchema.xsd'
    base2 = f'http://{HOST}:8082'
    base3 = f'http://{HOST}:8083'
    base4 = f'http://{HOST}:8084'
    base5 = f'http://{HOST}:8085'
    base6 = f'http://{HOST}:8086'
    base7 = f'http://{HOST}:8087'

    async with httpx.AsyncClient(timeout=60) as client:
        # Wait for services to be ready
        await wait_healthy(client, f'{base2}/health')
        await wait_healthy(client, f'{base3}/health')
        await wait_healthy(client, f'{base4}/health')
        await wait_healthy(client, f'{base5}/health')
        await wait_healthy(client, f'{base6}/health')
        await wait_healthy(client, f'{base7}/health')

        r = await client.post(f'{base2}/fetch', json={'xsd_url': xsd_url, 'cache_key': 'Schema.xsd'})
        print('fetch:', r.status_code, r.text[:200])
        r.raise_for_status()

        r = await client.post(f'{base3}/query', json={'cache_key': 'Schema.xsd', 'query': 'element name and type', 'k': 3})
        print('rag:', r.status_code, r.text[:200])
        r.raise_for_status()

        r = await client.post(f'{base4}/fill', json={'prompt': 'Return XML <note><to>A</to><from>B</from><body>Hi</body></note>'})
        print('llm:', r.status_code)
        r.raise_for_status()

        # Use a valid XML that matches the XML Schema definition
        xml = '''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="test" type="xs:string"/>
</xs:schema>'''
        r = await client.post(f'{base5}/validate', json={'xml_string': xml, 'cache_key': 'Schema.xsd'})
        print('validate:', r.status_code, r.text)
        r.raise_for_status()

        # Test format selector service
        pipe_data = "EntityName|Test Corp|Type:Company|Structure:LLC\nTransactionID|TXN-001|Type:Wire|Status:Completed|Amount:50000.00"
        r = await client.post(f'{base6}/analyze', json={'pipe_data': pipe_data})
        print('format_selector:', r.status_code, r.text[:200])
        r.raise_for_status()

        # Test orchestrator service
        r = await client.post(f'{base7}/pipeline', json={'pipe_data': pipe_data, 'validate_output': True, 'use_rag': True})
        print('orchestrator:', r.status_code, r.text[:200])
        r.raise_for_status()


if __name__ == '__main__':
    asyncio.run(main())


