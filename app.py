import duckdb
import pandas as pd
import streamlit as st

# ─────────────────────────────────────────
# CONFIGURAÇÃO DA PÁGINA
# ─────────────────────────────────────────
st.set_page_config(
    page_title="Bolsa Família — Análise",
    page_icon="🇧🇷",
    layout="wide",
)

st.title("🇧🇷 Bolsa Família — Análise de Dados")
st.caption("Fonte: Ministério do Desenvolvimento e Assistência Social")

# ─────────────────────────────────────────
# CARREGAR DADOS COM DUCKDB
# ─────────────────────────────────────────
# Altere o caminho abaixo para o caminho real do seu arquivo CSV
CAMINHO_CSV = "C:/Users/gusta/Downloads/202601_NovoBolsaFamilia/202601_NovoBolsaFamilia.csv"

@st.cache_resource
def conectar():
    """Cria conexão DuckDB lendo o CSV diretamente (sem carregar na memória)."""
    con = duckdb.connect()
    # DuckDB lê o CSV com lazy loading — não explode a memória
    con.execute(f"""
        CREATE VIEW bolsa AS
        SELECT
            "MÊS COMPETÊNCIA"   AS mes_competencia,
            "MÊS REFERÊNCIA"    AS mes_referencia,
            UF                  AS uf,
            "CÓDIGO MUNICÍPIO SIAFI" AS cod_municipio,
            "NOME MUNICÍPIO"    AS municipio,
            "NIS FAVORECIDO"    AS nis,
            "NOME FAVORECIDO"   AS nome,
            CAST(REPLACE(REPLACE("VALOR PARCELA", '.', ''), ',', '.') AS DOUBLE) AS valor
        FROM read_csv_auto('{CAMINHO_CSV}', delim=';', header=True, encoding='cp1252')
    """)
    return con

con = conectar()

# ─────────────────────────────────────────
# FILTROS NA BARRA LATERAL
# ─────────────────────────────────────────
st.sidebar.header("🔍 Filtros")

# Lista de UFs disponíveis
ufs = con.execute("SELECT DISTINCT uf FROM bolsa ORDER BY uf").df()["uf"].tolist()
uf_sel = st.sidebar.multiselect("Estado (UF)", ufs, default=ufs[:3])

# Filtro de município (carrega só os municípios do estado selecionado)
if uf_sel:
    munis = con.execute(
        f"SELECT DISTINCT municipio FROM bolsa WHERE uf IN ({','.join(repr(u) for u in uf_sel)}) ORDER BY municipio"
    ).df()["municipio"].tolist()
    muni_sel = st.sidebar.multiselect("Município (opcional)", munis)
else:
    muni_sel = []

# ─────────────────────────────────────────
# CONSULTA FILTRADA
# ─────────────────────────────────────────
where = "WHERE 1=1"
if uf_sel:
    ufs_str = ",".join(repr(u) for u in uf_sel)
    where += f" AND uf IN ({ufs_str})"
if muni_sel:
    munis_str = ",".join(repr(m) for m in muni_sel)
    where += f" AND municipio IN ({munis_str})"

resumo = con.execute(f"""
    SELECT
        COUNT(*) AS total_beneficiarios,
        SUM(valor) AS total_repassado,
        AVG(valor) AS media_parcela,
        MAX(valor) AS maior_parcela
    FROM bolsa {where}
""").df()

total_benef  = int(resumo["total_beneficiarios"][0])
total_repass = float(resumo["total_repassado"][0])
media        = float(resumo["media_parcela"][0])
maior        = float(resumo["maior_parcela"][0])

# ─────────────────────────────────────────
# MÉTRICAS PRINCIPAIS
# ─────────────────────────────────────────
st.subheader("📊 Resumo da seleção")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Beneficiários", f"{total_benef:,.0f}".replace(",", "."))
c2.metric("Total repassado", f"R$ {total_repass:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
c3.metric("Média por parcela", f"R$ {media:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
c4.metric("Maior parcela", f"R$ {maior:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

st.divider()

# ─────────────────────────────────────────
# PERSPECTIVAS — VALOR EM CONTEXTO
# ─────────────────────────────────────────
st.subheader("🏗️ O que dá para construir com esse valor?")
st.caption("Estimativas aproximadas com base em valores médios de obras públicas no Brasil.")

# Referências de custo (valores médios BRL)
CUSTO_HOSPITAL_MEDIO   = 50_000_000    # R$ 50 mi — hospital médio porte
CUSTO_ESCOLA_PUBLICA   = 2_500_000     # R$ 2,5 mi — escola estadual padrão
CUSTO_UBS              = 800_000       # R$ 800 mil — Unidade Básica de Saúde
CUSTO_CASA_POPULAR     = 120_000       # R$ 120 mil — casa popular
CUSTO_KM_ESTRADA       = 1_200_000     # R$ 1,2 mi por km — estrada pavimentada

p1, p2, p3, p4, p5 = st.columns(5)
p1.metric("🏥 Hospitais",      f"{total_repass / CUSTO_HOSPITAL_MEDIO:,.1f}")
p2.metric("🏫 Escolas",        f"{total_repass / CUSTO_ESCOLA_PUBLICA:,.0f}".replace(",", "."))
p3.metric("🩺 Postos de saúde",f"{total_repass / CUSTO_UBS:,.0f}".replace(",", "."))
p4.metric("🏠 Casas populares",f"{total_repass / CUSTO_CASA_POPULAR:,.0f}".replace(",", "."))
p5.metric("🛣️ Km de estrada",   f"{total_repass / CUSTO_KM_ESTRADA:,.0f}".replace(",", "."))

st.divider()

# ─────────────────────────────────────────
# RANKING POR ESTADO
# ─────────────────────────────────────────
st.subheader("📍 Ranking por Estado")

df_uf = con.execute(f"""
    SELECT
        uf,
        COUNT(*) AS beneficiarios,
        SUM(valor) AS total
    FROM bolsa {where}
    GROUP BY uf
    ORDER BY total DESC
""").df()

col_a, col_b = st.columns(2)

with col_a:
    st.markdown("**Total repassado por UF**")
    st.bar_chart(df_uf.set_index("uf")["total"])

with col_b:
    st.markdown("**Número de beneficiários por UF**")
    st.bar_chart(df_uf.set_index("uf")["beneficiarios"])

st.divider()

# ─────────────────────────────────────────
# TOP 10 MUNICÍPIOS
# ─────────────────────────────────────────
st.subheader("🏙️ Top 10 Municípios por valor repassado")

df_muni = con.execute(f"""
    SELECT
        municipio,
        uf,
        COUNT(*) AS beneficiarios,
        SUM(valor) AS total,
        AVG(valor) AS media
    FROM bolsa {where}
    GROUP BY municipio, uf
    ORDER BY total DESC
    LIMIT 10
""").df()

df_muni["total_fmt"] = df_muni["total"].apply(lambda x: f"R$ {x:,.2f}")
df_muni["media_fmt"] = df_muni["media"].apply(lambda x: f"R$ {x:,.2f}")

st.dataframe(
    df_muni[["municipio", "uf", "beneficiarios", "total_fmt", "media_fmt"]].rename(columns={
        "municipio": "Município",
        "uf": "UF",
        "beneficiarios": "Beneficiários",
        "total_fmt": "Total repassado",
        "media_fmt": "Média por parcela",
    }),
    use_container_width=True,
    hide_index=True,
)

st.divider()

# ─────────────────────────────────────────
# BUSCA POR NOME (opcional)
# ─────────────────────────────────────────
st.subheader("🔎 Pesquisar por nome do favorecido")
busca = st.text_input("Digite parte do nome:")

if busca and len(busca) >= 3:
    df_busca = con.execute(f"""
        SELECT nome, uf, municipio, valor
        FROM bolsa
        WHERE nome ILIKE '%{busca.upper()}%'
        LIMIT 100
    """).df()
    st.write(f"{len(df_busca)} resultado(s) encontrado(s) (máx. 100)")
    st.dataframe(df_busca, use_container_width=True, hide_index=True)
elif busca:
    st.info("Digite ao menos 3 letras para pesquisar.")

st.caption("Projeto acadêmico — dados públicos do Portal da Transparência.")