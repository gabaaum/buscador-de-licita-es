import asyncio
import json
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        async def handle_response(response):
            if "querydata" in response.url and response.request.method == "POST":
                print(f"URL: {response.url}")
                try:
                    req_post_data = response.request.post_data
                    if req_post_data:
                        print("REQUEST PAYLOAD:")
                        print(req_post_data[:500] + "...")
                        with open("pbi_request.json", "w") as f:
                            f.write(req_post_data)
                            
                    text = await response.text()
                    print(f"RESPONSE LENGTH: {len(text)}")
                    with open("pbi_response.json", "w") as f:
                        f.write(text)
                    print("Salvo pbi_response.json e pbi_request.json")
                except Exception as e:
                    print(f"Erro lendo resposta: {e}")

        page.on("response", handle_response)
        
        print("Acessando página...")
        await page.goto("https://www.transparencia.sp.gov.br/Home/ExecutaLicita", wait_until="networkidle")
        print("Página carregada, aguardando 10 segundos adicionais...")
        await page.wait_for_timeout(10000)
        
        await browser.close()

asyncio.run(main())
