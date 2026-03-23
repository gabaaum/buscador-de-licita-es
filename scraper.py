import requests
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

class ComprasScraper:
    def __init__(self, headless=True):
        self.headless = headless

    def _fetch_valor(self, cnpj, ano, sequencial):
        if not cnpj or not ano or not sequencial:
            return None
        try:
            url = f"https://pncp.gov.br/api/consulta/v1/orgaos/{cnpj}/compras/{ano}/{sequencial}"
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                return data.get('valorTotalEstimado')
        except:
            pass
        return None

    async def scrape(self, search_term: str, data_inicial: str = None, data_final: str = None):
        try:
            url = "https://pncp.gov.br/api/search/"
            
            # Ajuste de datas para o filtro manual (de formato BR ou ISO para ISO)
            filter_data_inicial = None
            filter_data_final = None
            if data_inicial and data_final:
                # Se for YYYY-MM-DD
                if "-" in data_inicial:
                    filter_data_inicial = data_inicial
                    filter_data_final = data_final
                else:
                    # Se vier outro formato, a gente tenta converter (ex: DD/MM/YYYY)
                    parts_i = data_inicial.split("/")
                    filter_data_inicial = f"{parts_i[2]}-{parts_i[1]}-{parts_i[0]}"
                    parts_f = data_final.split("/")
                    filter_data_final = f"{parts_f[2]}-{parts_f[1]}-{parts_f[0]}"
            
            params = {
                'q': search_term,
                'tipos_documento': 'edital',
                'ordenacao': '-data',
                'tam_pagina': '50',
                'status': 'todos'
            }
            
            print(f"Buscando na API PNCP | Termo: {search_term} | Periodo: {filter_data_inicial} a {filter_data_final}")
            
            results = []
            max_paginas = 200 # Aumentado para suportar períodos maiores (até 10.000 resultados lidos)
            stop_search = False
            
            for pagina in range(1, max_paginas + 1):
                if stop_search: break
                
                params['pagina'] = str(pagina)
                response = requests.get(url, params=params, timeout=15)
                
                if response.status_code != 200:
                    break
                    
                data = response.json()
                items = data.get('items', [])
                if not items:
                    break
                    
                # Checa se todos os itens da página são mais antigos que a data inicial
                # Para evitar parar a busca prematuramente devido a inconsistências de ordenação
                if filter_data_inicial:
                    all_older = True
                    for item in items:
                        d_pub = item.get('data_publicacao_pncp', '')
                        i_date = d_pub.split("T")[0] if d_pub else ""
                        if not i_date or i_date >= filter_data_inicial:
                            all_older = False
                            break
                    if all_older:
                        stop_search = True
                        break
                    
                for item in items:
                    data_pub_raw = item.get('data_publicacao_pncp', '')
                    item_date_str = data_pub_raw.split("T")[0] if data_pub_raw else ""
                    
                    # Filtro de data na unha!
                    if filter_data_inicial and filter_data_final and item_date_str:
                        # Se a data do item for mais recente que a final, pula
                        if item_date_str > filter_data_final:
                            continue
                        # Se a data do item for mais antiga que a inicial, pula
                        if item_date_str < filter_data_inicial:
                            continue
                            
                    # Se passou no filtro (ou se nao tem filtro), adiciona!
                    
                    valor_global = item.get('valor_global')
                    if valor_global is None:
                        # Fallback for when valor_global is not in search API
                        cnpj = item.get('orgao_cnpj')
                        ano = item.get('ano')
                        seq = item.get('numero_sequencial')
                        # We will fetch this later in parallel to avoid slowing down the main loop too much
                        item['_fetch_args'] = (cnpj, ano, seq)
                    
                    if valor_global is not None:
                        valor_formatado = f"R$ {valor_global:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                    else:
                        valor_formatado = "Não informado"
                    
                    data_formatada = "Data não disponível"
                    if item_date_str:
                        try:
                            parts = item_date_str.split("-")
                            data_formatada = f"{parts[2]}/{parts[1]}/{parts[0]}"
                        except:
                            data_formatada = data_pub_raw
                    
                    situacao = item.get('situacao_nome', 'Não informado')
                    if "Divulgada" in situacao:
                        situacao = "Recebendo Propostas"
                        
                    objeto = item.get('description', 'Sem objeto')
                    if not objeto: objeto = 'Sem objeto'
                    
                    orgao_nome = item.get('orgao_nome', 'Não informado')
                    link = item.get('item_url', '')
                    if link:
                        if link.startswith('/compras/'):
                            link = link.replace('/compras/', 'https://pncp.gov.br/app/editais/')
                        elif link.startswith('/'):
                            link = 'https://pncp.gov.br' + link

                    numero = item.get('title', 'S/N')
                    if not numero or numero == "S/N":
                        numero = f"{item.get('numero', item.get('numero_sequencial', 'S/N'))}/{item.get('ano', '')}"

                    results.append({
                        "numero": numero,
                        "orgao": orgao_nome,
                        "objeto": objeto,
                        "abertura": data_formatada,
                        "valor": valor_formatado,
                        "status": situacao,
                        "link": link,
                        "_fetch_args": item.get('_fetch_args')
                    })
                
            missing_vals = [r for r in results if r['valor'] == "Não informado" and r.get('_fetch_args')]
            if missing_vals:
                def fetch_and_set(r):
                    args = r.get('_fetch_args')
                    if args:
                        val = self._fetch_valor(*args)
                        if val is not None:
                            r['valor'] = f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                    r.pop('_fetch_args', None)

                with ThreadPoolExecutor(max_workers=20) as executor:
                    futures = [executor.submit(fetch_and_set, r) for r in missing_vals]
                    for _ in as_completed(futures):
                        pass

            for r in results:
                r.pop('_fetch_args', None)

            return results
            
        except Exception as e:
            print(f"Erro geral no scraping com API: {e}")
            return []

if __name__ == "__main__":
    import asyncio
    scraper = ComprasScraper(headless=True)
    results = asyncio.run(scraper.scrape("obras", "2026-01-01", "2026-03-22"))
    for r in results:
        print(r)
