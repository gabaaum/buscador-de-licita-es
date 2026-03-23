from playwright.async_api import async_playwright
import asyncio
import re

class LicitacoesPagasScraper:
    def __init__(self, headless=True):
        self.headless = headless

    async def scrape(self, data_inicial, data_final, orgao, municipio, cnpj):
        results = []
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=self.headless)
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                page = await context.new_page()
                
                # Navigate to the portal
                print("Acessando Portal da Transparência...")

                base_url = "https://portaldatransparencia.gov.br/licitacoes/consulta?paginacaoSimples=true&tamanhoPagina=50&offset=0&direcaoOrdenacao=desc&colunaOrdenacao=dataPublicacao&colunasSelecionadas=linkDetalhamento%2CnumeroLicitacao%2CdataPublicacao%2CorgaoSuperior%2Corgao%2Cobjeto%2Cmodalidade%2Csituacao%2CvalorEstimadoLicitacao"
                
                query_params = []
                
                if data_inicial:
                    parts = data_inicial.split('-')
                    if len(parts) == 3:
                        data_ini_br = f"{parts[2]}%2F{parts[1]}%2F{parts[0]}"
                        query_params.append(f"dataAberturaDe={data_ini_br}")
                if data_final:
                    parts = data_final.split('-')
                    if len(parts) == 3:
                        data_fim_br = f"{parts[2]}%2F{parts[1]}%2F{parts[0]}"
                        query_params.append(f"dataAberturaAte={data_fim_br}")
                
                if orgao:
                    query_params.append(f"orgao={orgao}")
                
                search_url = base_url
                if query_params:
                    search_url += "&" + "&".join(query_params)
                
                print(f"Buscando URL: {search_url}")
                await page.goto(search_url, timeout=60000)
                await page.wait_for_timeout(5000)
                # Try to extract data correctly. The table might have multiple thead/tbody or structure.
                html = await page.evaluate("() => document.body.innerHTML")
                with open('debug_pt.html', 'w') as f:
                    f.write(html)
                
                rows = await page.locator("table tbody tr").all()
                print(f"Encontrou {len(rows)} linhas")
                for row in rows:
                    cells = await row.locator("td").all_inner_texts()
                    if not cells:
                        continue
                        
                    orgao_nome = cells[0].strip() if len(cells) > 0 else ""
                    
                    if "Nenhum registro encontrado" in orgao_nome or "No data available in table" in orgao_nome:
                        continue
                        
                    situacao = cells[1].strip() if len(cells) > 1 else ""
                    modalidade = cells[2].strip() if len(cells) > 2 else ""
                    numero = cells[3].strip() if len(cells) > 3 else ""
                    objeto = cells[4].strip() if len(cells) > 4 else ""
                    data_pub = "Detalhes via portal"
                    valor = "Detalhes via portal"
                    
                    results.append({
                        "numero": numero,
                        "data_publicacao": data_pub,
                        "orgao": orgao_nome,
                        "objeto": objeto,
                        "modalidade": modalidade,
                        "situacao": situacao,
                        "valor_homologado": valor
                    })
                
                await browser.close()
                return results
        except Exception as e:
            print(f"Erro no scraper das Licitações Pagas: {e}")
            return []

if __name__ == "__main__":
    scraper = LicitacoesPagasScraper(headless=True)
    res = asyncio.run(scraper.scrape("2024-01-01", "2024-01-31", "", "", ""))
    for r in res:
        print(r)
