import asyncio
import json
from playwright.async_api import async_playwright
import urllib.parse
from datetime import datetime
import os

class LicitacoesPagasScraperSP:
    def __init__(self, headless=True):
        self.headless = headless

    async def scrape(self, data_inicial, data_final, orgao, municipio, cnpj):
        results = []
        try:
            print(f"Acessando portal da Transparência SP para extrair métricas do PowerBI. Periodo: {data_inicial} a {data_final}")
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=self.headless)
                page = await browser.new_page()

                pbi_context = {"auth": None, "resourceKey": None, "url": None}
                
                async def handle_request(request):
                    if "querydata" in request.url and request.method == "POST":
                        headers = request.headers
                        if "x-powerbi-resourcekey" in headers:
                            pbi_context["resourceKey"] = headers["x-powerbi-resourcekey"]
                        if "authorization" in headers:
                            pbi_context["auth"] = headers["authorization"]
                        pbi_context["url"] = request.url

                page.on("request", handle_request)
                
                await page.goto("https://www.transparencia.sp.gov.br/Home/ExecutaLicita", wait_until="networkidle")
                
                print("Aguardando carregamento do PowerBI...")
                await page.wait_for_timeout(8000)
                
                await browser.close()
                
                if not pbi_context["resourceKey"] or not pbi_context["url"]:
                    print("Não foi possível capturar o ResourceKey do PowerBI. Utilizando fallback PNCP para evitar falha total.")
                    return self._fallback_pncp(data_inicial, data_final, orgao, municipio, cnpj)
                    
                print("Conectado ao PowerBI SP. Executando query customizada com filtros de data...")
                
                custom_query = self._build_pbi_query(data_inicial, data_final)
                
                import requests
                headers = {
                    "Content-Type": "application/json",
                    "X-PowerBI-ResourceKey": pbi_context["resourceKey"]
                }
                if pbi_context["auth"]:
                    headers["Authorization"] = pbi_context["auth"]
                
                response = requests.post(
                    pbi_context["url"],
                    headers=headers,
                    json=custom_query,
                    verify=False
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = self._parse_pbi_response(data)
                else:
                    print(f"Erro ao consultar o PBI diretamente: {response.status_code}")
                    return self._fallback_pncp(data_inicial, data_final, orgao, municipio, cnpj)
                    
                if not results:
                     results.append({
                        "numero": "-",
                        "data_publicacao": "-",
                        "orgao": "Transparência SP",
                        "objeto": "Nenhum resultado de empenho pago encontrado no PowerBI no período selecionado.",
                        "modalidade": "-",
                        "situacao": "-",
                        "valor_homologado": "-"
                     })
                     
                return results

        except Exception as e:
            print(f"Erro no scraper de SP via PBI: {e}")
            return []

    def _build_pbi_query(self, data_ini, data_fim):
        payload_file = 'pbi_table_request_500.json'
        if not os.path.exists(payload_file):
            payload_file = 'pbi_table_request.json'
            
        with open(payload_file, 'r') as f:
            payload = json.load(f)
            
        try:
            for cmd in payload.get('queries', [{}])[0].get('Query', {}).get('Commands', []):
                if 'SemanticQueryDataShapeCommand' in cmd:
                    query_obj = cmd['SemanticQueryDataShapeCommand'].setdefault('Query', {})
                    
                    # 1. Injetar limite de 500 linhas
                    binding = cmd['SemanticQueryDataShapeCommand'].setdefault('Binding', {})
                    reduction = binding.setdefault('DataReduction', {})
                    reduction['DataVolume'] = 4
                    primary = reduction.setdefault('Primary', {})
                    window = primary.setdefault('Window', {})
                    window['Count'] = 500

                    # 2. Injetar filtro de Data (Between)
                    if data_ini and data_fim:
                        try:
                            # Converte string ISO (YY-MM-DD) para Timestamp Unix com milisegundos 
                            # que é o padrão PowerBI para datetime, ou DateLiteral
                            d_ini = datetime.strptime(data_ini, "%Y-%m-%d").strftime("%Y-%m-%dT00:00:00.000Z")
                            d_fim = datetime.strptime(data_fim, "%Y-%m-%d").strftime("%Y-%m-%dT23:59:59.000Z")
                            
                            where_clause = query_obj.setdefault('Where', [])
                            
                            # Filtro DAX para a tabela ft_transparencia_licitacao ou dm_licitacao
                            # Assume "d" ou "f" como source, baseando-se no select existente. 
                            # Adicionando um Between generico na Data Atualização / Emissao:
                            
                            date_filter = {
                                "Condition": {
                                    "Between": {
                                        "Expression": {
                                            "Column": {
                                                "Expression": {
                                                    "SourceRef": {"Source": "f"} # Tabela Fato
                                                },
                                                "Property": "Data Carga" # Campo de Data mais comum no PBI de SP
                                            }
                                        },
                                        "LowerBound": {
                                            "Literal": {
                                                "Value": f"datetime'{d_ini}'"
                                            }
                                        },
                                        "UpperBound": {
                                            "Literal": {
                                                "Value": f"datetime'{d_fim}'"
                                            }
                                        }
                                    }
                                }
                            }
                            
                            # Se Where já possui elementos, mesclar ou sobrescrever (vamos adicionar)
                            where_clause.append(date_filter)
                        except Exception as dt_err:
                            print(f"Erro ao converter datas para filtro PBI: {dt_err}")
                            
        except Exception as e:
            print("Aviso: Falha ao injetar filtros dinâmicos na query PBI", e)
            
        return payload

    def _parse_pbi_response(self, data):
        results = []
        try:
            res_list = data.get("results", [])
            if not res_list: return results
            
            ds = res_list[0].get("result", {}).get("data", {}).get("dsr", {}).get("DS", [])
            if not ds: return results
            
            first_ds = ds[0]
            value_dicts = first_ds.get("ValueDicts", {})
            ph = first_ds.get("PH", [])
            
            if not ph: return results
            dm0 = ph[0].get("DM0", [])
            
            dict_keys = list(value_dicts.keys())
            
            last_row_state = [None] * 4
            
            for item in dm0:
                c_array = item.get("C", [])
                r_flag = item.get("R")
                
                current_row = list(last_row_state)
                
                if r_flag is not None:
                    c_idx = 0
                    for i in range(4):
                        if r_flag & (1 << i):
                            pass
                        else:
                            if c_idx < len(c_array):
                                current_row[i] = c_array[c_idx]
                                c_idx += 1
                else:
                    for i in range(min(4, len(c_array))):
                        current_row[i] = c_array[i]

                last_row_state = list(current_row)
                
                val_num = current_row[0]
                val_org = current_row[1]
                val_mod = current_row[2]
                val_valor = current_row[3]
                
                if isinstance(val_num, int) and dict_keys and len(dict_keys) > 0:
                    try: val_num = value_dicts[dict_keys[0]][val_num]
                    except: pass
                    
                if isinstance(val_org, int) and len(dict_keys) > 1:
                    try: val_org = value_dicts[dict_keys[1]][val_org]
                    except: pass

                if isinstance(val_mod, int) and len(dict_keys) > 2:
                    try: val_mod = value_dicts[dict_keys[2]][val_mod]
                    except: pass

                results.append({
                    "numero": str(val_num),
                    "data_publicacao": "-", # TODO: pegar data real do array
                    "orgao": str(val_org),
                    "objeto": "Informação de empenho via PBI. Detalhes no Portal.",
                    "modalidade": str(val_mod),
                    "situacao": "Empenhado/Pago",
                    "valor_homologado": f"R$ {val_valor}" if val_valor is not None else "Não informado"
                })
        except Exception as e:
            print(f"Erro no parse JSON PBI: {e}")
            
        return results

    def _fallback_pncp(self, data_inicial, data_final, orgao, municipio, cnpj):
        import requests
        results = []
        try:
            print("Executando fallback para o PNCP...")
            query = "SP"
            if orgao: query += f" {orgao}"
            url = f"https://pncp.gov.br/api/search/?q={query}&tipos_documento=edital&ordenacao=-data&pagina=1&tamanhoPagina=10"
            response = requests.get(url, verify=False)
            if response.status_code == 200:
                data = response.json()
                items = data.get('items', [])
                for item in items:
                    results.append({
                        "numero": item.get('numero_controle_pncp', 'N/A'),
                        "data_publicacao": str(item.get('data_publicacao_pncp', '')).split('T')[0],
                        "orgao": item.get('orgao_nome', 'Governo de SP'),
                        "objeto": item.get('description', 'N/A'),
                        "modalidade": item.get('modalidade_licitacao_nome', 'N/A'),
                        "situacao": item.get('situacao_nome', 'N/A'),
                        "valor_homologado": f"R$ {item.get('valor_global', 'Não informado')}" if item.get('valor_global') else "Detalhes via portal"
                    })
        except: pass
        return results

if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings()
    scraper = LicitacoesPagasScraperSP(headless=True)
    res = asyncio.run(scraper.scrape("2024-01-01", "2024-01-31", "", "", ""))
    for r in res[:15]:
        print(r)
    print(f"Total: {len(res)}")
