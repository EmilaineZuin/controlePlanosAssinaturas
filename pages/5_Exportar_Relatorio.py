# -- Página para exportar relatórios das assinaturas.

import streamlit as st
import pandas as pd
import datetime
from io import BytesIO
from google_sheets_connector import get_worksheet_data
from config import SHEET_URL, WORKSHEET_NAME, STATUS_ATIVA, MULTIPLICADOR_ANUAL

# Configuração da página do Streamlit
st.set_page_config(page_title="Exportar Relatório", page_icon="📄", layout="wide")
st.title("Exportar Relatório 📄")
st.markdown("Baixe seus dados em CSV ou em um relatório PDF formatado.")

# Carrega registros da planilha via conector
records = get_worksheet_data(SHEET_URL, WORKSHEET_NAME)

if records is None:
    st.error("Não foi possível carregar a planilha.")
    st.stop()

# Converte pra DataFrame pra manipular os dados com pandas
df = pd.DataFrame(records)

if df.empty:
    st.info("Nenhuma assinatura cadastrada.")
    st.stop()

# Converte colunas de data para datetime para uso posterior
df['ProximoVencimento'] = pd.to_datetime(df['ProximoVencimento'], format='%d/%m/%Y')
df['DataDeAdesao'] = pd.to_datetime(df['DataDeAdesao'], format='%d/%m/%Y')
# Filtra apenas as ativas por padrão, mas o usuário pode incluir canceladas
df_ativas = df[df['Status'] == STATUS_ATIVA].copy()

# --- OPÇÕES DE FILTRO ---
st.subheader("Opções do Relatório")
col1, col2 = st.columns(2)

with col1:
    incluir_canceladas = st.checkbox("Incluir assinaturas canceladas", value=False)
with col2:
    ordenar_por = st.selectbox("Ordenar por", ["Próximo Vencimento", "Nome", "Valor", "Categoria"])

# Escolhe o dataframe para exportar com base na opção do usuário
df_export = df.copy() if incluir_canceladas else df_ativas.copy()

ordem_map = {
    "Próximo Vencimento": "ProximoVencimento",
    "Nome": "NomeDaAssinatura",
    "Valor": "Valor",
    "Categoria": "Categoria",
}
# Ordena o dataframe de acordo com a escolha
df_export = df_export.sort_values(by=ordem_map[ordenar_por])

# --- PRÉ-VISUALIZAÇÃO ---
st.write("---")
st.subheader("Pré-visualização")

df_preview = df_export.copy()
df_preview['ProximoVencimento'] = df_preview['ProximoVencimento'].dt.strftime('%d/%m/%Y')
df_preview['DataDeAdesao'] = df_preview['DataDeAdesao'].dt.strftime('%d/%m/%Y')
st.dataframe(df_preview, use_container_width=True, hide_index=True)

# --- EXPORT CSV ---
st.write("---")
st.subheader("Exportar CSV")
csv_bytes = df_preview.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
st.download_button(
    label="⬇️ Baixar CSV",
    data=csv_bytes,
    file_name=f"assinaturas_{datetime.date.today().strftime('%Y%m%d')}.csv",
    mime="text/csv",
)

# --- EXPORT PDF ---
st.write("---")
st.subheader("Exportar PDF")

def gerar_pdf(df_data: pd.DataFrame, incluir_canceladas: bool) -> bytes:
    """Gera um PDF com resumo e tabela de assinaturas.

    Retorna bytes do PDF ou None se a biblioteca fpdf não estiver disponível.
    (estudante: tento importar fpdf dentro da função pra não exigir a lib em tempo de importação)
    """
    try:
        from fpdf import FPDF
    except ImportError:
        return None

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Título e data de geração
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 12, "Relatorio de Assinaturas", ln=True, align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Gerado em: {datetime.date.today().strftime('%d/%m/%Y')}", ln=True, align="C")
    pdf.ln(4)

    # Resumo dos gastos
    df_at = df_data[df_data['Status'] == STATUS_ATIVA] if 'Status' in df_data.columns else df_data
    total_mensal = 0.0
    total_anual = 0.0
    for _, row in df_at.iterrows():
        freq = row.get('Frequencia', 'Mensal')
        val = float(row.get('Valor', 0))
        mult = MULTIPLICADOR_ANUAL.get(freq, 12)
        total_anual += val * mult
        if freq == 'Mensal':
            total_mensal += val

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Resumo", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(95, 6, f"Total de assinaturas ativas: {len(df_at)}", border=1)
    pdf.cell(95, 6, f"Gasto mensal recorrente: R$ {total_mensal:.2f}", border=1, ln=True)
    pdf.cell(95, 6, f"Gasto anual estimado: R$ {total_anual:.2f}", border=1)
    pdf.cell(95, 6, f"Inclui canceladas: {'Sim' if incluir_canceladas else 'Nao'}", border=1, ln=True)
    pdf.ln(6)

    # Tabela de assinaturas
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "Assinaturas", ln=True)

    # Cabeçalho da tabela
    colunas = ["Nome", "Valor (R$)", "Frequencia", "Vencimento", "Categoria", "Status"]
    larguras = [50, 25, 25, 25, 35, 25]
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(64, 98, 247)
    pdf.set_text_color(255, 255, 255)
    for col, larg in zip(colunas, larguras):
        pdf.cell(larg, 7, col, border=1, fill=True)
    pdf.ln()

    # Linhas de dados
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(0, 0, 0)
    fill = False
    for _, row in df_data.iterrows():
        pdf.set_fill_color(240, 240, 240) if fill else pdf.set_fill_color(255, 255, 255)
        venc = row['ProximoVencimento']
        if hasattr(venc, 'strftime'):
            venc_str = venc.strftime('%d/%m/%Y')
        else:
            venc_str = str(venc)

        valores_linha = [
            str(row.get('NomeDaAssinatura', ''))[:28],
            f"{float(row.get('Valor', 0)):.2f}",
            str(row.get('Frequencia', '')),
            venc_str,
            str(row.get('Categoria', ''))[:20],
            str(row.get('Status', '')),
        ]
        for val, larg in zip(valores_linha, larguras):
            pdf.cell(larg, 6, val, border=1, fill=fill)
        pdf.ln()
        fill = not fill

    # Retorna os bytes do PDF gerado
    return bytes(pdf.output())


# Botão que gera o PDF e disponibiliza para download
if st.button("Gerar PDF e Baixar", type="primary"):
    with st.spinner("Gerando PDF..."):
        pdf_bytes = gerar_pdf(df_export, incluir_canceladas)

    if pdf_bytes is None:
        st.error(
            "A biblioteca **fpdf2** não está instalada. "
            "Execute `pip install fpdf2` e reinicie o app."
        )
    else:
        st.download_button(
            label="⬇️ Baixar PDF",
            data=pdf_bytes,
            file_name=f"relatorio_assinaturas_{datetime.date.today().strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
        )
        st.success("PDF gerado com sucesso!")
