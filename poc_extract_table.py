import asyncio
from playwright.async_api import async_playwright
import json

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        async def route_handler(route):
            if "querydata" in route.request.url and route.request.method == "POST":
                # Vamos tentar interceptar a requisição que preenche a tabela
                # Se ela for capturada, salvaremos para analisar
                post_data = route.request.post_data
                if post_data and '"dm_licitacao"' in post_data and '"Select"' in post_data:
                    # tenta achar queries com multiplos selects (como uma tabela)
                    data_json = json.loads(post_data)
                    selects = data_json.get('queries', [{}])[0].get('Query', {}).get('Commands', [{}])[0].get('SemanticQueryDataShapeCommand', {}).get('Query', {}).get('Select', [])
                    
                    if len(selects) > 2:
                        print(f"ENCONTRADA QUERY DE TABELA COM {len(selects)} COLUNAS!")
                        with open("pbi_table_request.json", "w") as f:
                            f.write(post_data)
            await route.continue_()

        await page.route("**/*", route_handler)
        
        print("Acessando página...")
        await page.goto("https://www.transparencia.sp.gov.br/Home/ExecutaLicita", wait_until="networkidle")
        
        # Simular clique ou interação se a tabela precisar
        # O PBI carrega os gráficos logo de cara.
        print("Aguardando carregamento de gráficos (15s)...")
        await page.wait_for_timeout(15000)
        
        await browser.close()
        print("Concluído. Verificando se capturamos uma request de Tabela...")

asyncio.run(main())
