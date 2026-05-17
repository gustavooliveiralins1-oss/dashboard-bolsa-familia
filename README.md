# Dashboard Bolsa Família 🇧🇷

Dashboard interativo para análise dos dados públicos do Programa Bolsa Família.

## Tecnologias
- Python
- DuckDB
- Streamlit
- Pandas

## Como rodar

1. Baixe o arquivo CSV em: https://www.portaltransparencia.gov.br
2. Instale as dependências:
pip install duckdb streamlit pandas
3. Rode o dashboard:
streamlit run app.py

## Funcionalidades
- Filtros por estado e município
- Métricas de beneficiários e valores repassados
- Perspectivas: hospitais, escolas, casas populares
- Ranking por estado
- Pesquisa por nome de beneficiário
- Planilha completa paginada
