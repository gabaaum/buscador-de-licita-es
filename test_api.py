import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context()
        api_url = "https://pncp.gov.br/api/pncp/v1/orgaos/08741398000109/compras/2026/4"
        print(f"Buscando API: {api_url}")
        api_resp = await context.request.get(api_url)
        print(f"Status: {api_resp.status}")
        if api_resp.ok:
            data = await api_resp.json()
            print(f"Valor: {data.get('valorTotalEstimado')}")
        await browser.close()

asyncio.run(main())
