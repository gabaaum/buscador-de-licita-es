# Plano de Extração e Decodificação - PowerBI SP

O processo de reversão da API oculta do PowerBI baseia-se na extração e interpretação da rota `querydata`.

## 1. O Endpoint e a Requisição
**URL:** `https://wabi-brazil-south-b-primary-api.analysis.windows.net/public/reports/querydata?synchronous=true`

**Payload:** O POST payload contém uma estrutura DAX (SemanticQueryDataShapeCommand).
O PowerBI usa aliases para as tabelas (ex: `f` = `ft_transparencia_licitacao`, `d` = `dm_licitacao`).

Precisamos montar uma query customizada selecionando os campos:
- `Numero da Licitacao`
- `Orgao`
- `Modalidade`
- `Data Publicacao`
- `Situacao`
- `Valor Homologado` / `Valor Empenhado`
- `CNPJ`

## 2. A Estrutura da Resposta (Response JSON)
A resposta do `querydata` é um JSON altamente compactado, conhecido como **Data Shapes**. O nó mais importante é:
`results[0].result.data.dsr.DS[0].PH[0].DM0` (ou similar, dependendo da hierarquia).

O objeto de dados contém tipicamente:
- **`ValueDicts`**: Dicionários de strings. Como os dados textuais repetem muito, o PowerBI armazena textos em listas indexadas aqui.
- **`C` (Columns)**: Uma lista de colunas, onde cada valor pode ser o dado real (se for numérico) ou um **índice** numérico apontando para o `ValueDicts` (se for texto).
- **`R` (Rows)**: Em matrizes mais complexas, especifica a hierarquia ou agrupamento.

### Como Decodificar (Algoritmo):
1. **Identificar as Colunas:** Mapear o índice de cada campo no `Select` da query com sua posição na resposta.
2. **Localizar ValueDicts:** Extrair a lista de strings únicas para cada coluna do tipo texto.
3. **Iterar nas Linhas (`C` arrays):**
   - Para cada array em `C` (que representa um registro ou conjunto de dados compactado):
   - Verificar se o campo correspondente usa `ValueDicts`.
   - Se sim, usar o valor inteiro de `C[index]` para buscar a string em `ValueDicts[index]`.
   - Se for um valor com flag de repetição (`R`), herdar o valor da linha anterior.
   - Extrair o valor empenhado / CNPJ mapeado.

## 3. Próximos Passos (Scraper)
1. Construir uma query `SemanticQueryDataShapeCommand` mínima contendo as tabelas do Portal de Licitações de SP.
2. Obter o `X-PowerBI-ResourceKey` no portal (do embed report).
3. Fazer o POST para `querydata`.
4. Processar o JSON resultante desdobrando `C` e `ValueDicts`.
5. Retornar os dados na mesma estrutura que o sistema do Hub espera.