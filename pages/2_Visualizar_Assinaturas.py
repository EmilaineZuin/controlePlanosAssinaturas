# --Página de visualização das assinaturas com comentários em tom de estudante.

import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
from google_sheets_connector import get_worksheet_data, open_worksheet_by_url
from config import SHEET_URL, WORKSHEET_NAME, STATUS_ATIVA, STATUS_CANCELADA
from subscription_utils import calcular_novo_vencimento, calcular_gasto_mensal_equivalente
from orcamento_ui import render_orcamento_sidebar, render_orcamento_card

# Configuração básica da página (título, ícone e layout)
st.set_page_config(page_title="Minhas Assinaturas", page_icon="📊", layout="wide")

# CSS simples para estilizar métricas (opcional, só pra ficar mais bonito)
st.markdown("""
<style>
[data-testid="stMetric"] {
    background-color: #4062f7;
    border: 1px solid #C3E6CB;
    padding: 15px;
    border-radius: 10px;
    color: rgb(38, 39, 48);
}
</style>
""", unsafe_allow_html=True)

st.title("Análise de Assinaturas 📊")

# Renderiza sidebar com informações do orçamento atual
orcamento_atual = render_orcamento_sidebar()

# Busca os registros da planilha (cache gerenciado pelo conector)
records = get_worksheet_data(SHEET_URL, WORKSHEET_NAME)

if records is not None:
    # Converte os registros para DataFrame do pandas pra facilitar manipulação
    # pandas facilita muito filtrar, agrupar e transformar dados
    df = pd.DataFrame(records)

    if not df.empty:
        # --- FILTROS ---
        # aqui eu crio filtros na sidebar pra o usuário escolher o que quer ver
        st.sidebar.header("Filtros")
        status_list = ["Todas"] + list(df['Status'].unique())
        selected_status = st.sidebar.selectbox("Filtrar por Status", status_list)

        category_list = ["Todas"] + list(df['Categoria'].unique())
        selected_category = st.sidebar.selectbox("Filtrar por Categoria", category_list)

        df_filtered = df.copy()
        if selected_status != "Todas":
            df_filtered = df_filtered[df_filtered['Status'] == selected_status]
        if selected_category != "Todas":
            df_filtered = df_filtered[df_filtered['Categoria'] == selected_category]

        # Converte a coluna de próximo vencimento para datetime para ordenar corretamente
        df_filtered['ProximoVencimento'] = pd.to_datetime(df_filtered['ProximoVencimento'], format='%d/%m/%Y')
        df_filtered_sorted = df_filtered.sort_values(by="ProximoVencimento")

        st.subheader("Suas Assinaturas")
        st.dataframe(df_filtered_sorted, use_container_width=True, hide_index=True)

        # --- EXPORTAR CSV ---
        # disponibilizo um download da tabela filtrada para análise externa
        csv = df_filtered_sorted.copy()
        csv['ProximoVencimento'] = csv['ProximoVencimento'].dt.strftime('%d/%m/%Y')
        st.download_button(
            label="⬇️ Exportar tabela como CSV",
            data=csv.to_csv(index=False, sep=';', encoding='utf-8-sig'),
            file_name="assinaturas.csv",
            mime="text/csv",
        )

        st.write("---")

        # --- RESUMO E GRÁFICO ---
        # esse bloco calcula gastos e mostra um gráfico por categoria
        df_ativas_filtradas = df_filtered[df_filtered['Status'] == STATUS_ATIVA]

        if not df_ativas_filtradas.empty:
            col1, col2 = st.columns([0.6, 0.4])

            with col1:
                st.subheader("Resumo dos Gastos (Baseado nos Filtros)")
                # Soma dos valores por frequência para estimar gasto anual
                gasto_mensal = df_ativas_filtradas[df_ativas_filtradas['Frequencia'] == 'Mensal']['Valor'].sum()
                gasto_anual_de_anuais = df_ativas_filtradas[df_ativas_filtradas['Frequencia'] == 'Anual']['Valor'].sum()
                gasto_trimestral = df_ativas_filtradas[df_ativas_filtradas['Frequencia'] == 'Trimestral']['Valor'].sum()
                gasto_semestral = df_ativas_filtradas[df_ativas_filtradas['Frequencia'] == 'Semestral']['Valor'].sum()
                gasto_anual_total = (gasto_mensal * 12) + gasto_anual_de_anuais + (gasto_trimestral * 4) + (gasto_semestral * 2)

                sub_col1, sub_col2 = st.columns(2)
                sub_col1.metric("Gasto Mensal Recorrente", f"R$ {gasto_mensal:.2f}")
                sub_col2.metric("Gasto Anual Estimado", f"R$ {gasto_anual_total:.2f}")

                # Calcula gasto mensal equivalente usando função auxiliar
                gasto_mensal_equivalente = calcular_gasto_mensal_equivalente(df_ativas_filtradas)
                render_orcamento_card(gasto_mensal_equivalente, orcamento_atual)

            with col2:
                st.subheader("Gastos por Categoria")
                # Agrupa por categoria e plota um gráfico de pizza
                gastos_por_categoria = df_ativas_filtradas.groupby('Categoria')['Valor'].sum().reset_index()
                fig = px.pie(
                    gastos_por_categoria, values='Valor', names='Categoria',
                    title='Distribuição de Gastos por Categoria',
                    color_discrete_sequence=px.colors.sequential.Greens_r
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Nenhuma assinatura ativa encontrada com os filtros selecionados.")

        # --- RENOVAR ASSINATURA ---
        # o usuário pode avançar o próximo vencimento em 1 período
        st.write("---")
        st.subheader("Renovar Assinatura")
        st.caption("Avança o próximo vencimento em 1 período, de acordo com a frequência.")

        ativas_para_renovar = df[df['Status'] == STATUS_ATIVA]['NomeDaAssinatura'].tolist()

        if ativas_para_renovar:
            col_sel_r, col_btn_r = st.columns([3, 1])
            assinatura_renovar = col_sel_r.selectbox(
                "Selecione a assinatura para renovar:", ativas_para_renovar, key="renovar_sel"
            )

            if col_btn_r.button("Renovar", type="primary", use_container_width=True):
                try:
                    # Recarrega todos os dados da planilha para localizar a linha correta
                    all_df = pd.DataFrame(get_worksheet_data(SHEET_URL, WORKSHEET_NAME))
                    linha = all_df[all_df['NomeDaAssinatura'] == assinatura_renovar].iloc[0]
                    idx = all_df[all_df['NomeDaAssinatura'] == assinatura_renovar].index[0]
                    row_num = idx + 2  # +1 header, +1 índice base-1

                    vencimento_atual = datetime.datetime.strptime(
                        linha['ProximoVencimento'], '%d/%m/%Y'
                    ).date()
                    novo_vencimento = calcular_novo_vencimento(vencimento_atual, linha['Frequencia'])

                    worksheet = open_worksheet_by_url(SHEET_URL, WORKSHEET_NAME)
                    worksheet.update_cell(row_num, 5, novo_vencimento.strftime('%d/%m/%Y'))
                    get_worksheet_data.clear()
                    st.success(
                        f"Assinatura '{assinatura_renovar}' renovada! "
                        f"Novo vencimento: {novo_vencimento.strftime('%d/%m/%Y')}"
                    )
                    st.rerun()
                except Exception as e:
                    # Mostrar o erro caso algo dê errado (ex: problema de conexão)
                    st.error(f"Erro ao renovar: {e}")
        else:
            st.info("Nenhuma assinatura ativa para renovar.")

        # --- CANCELAR ASSINATURA ---
        # cancelar não apaga a assinatura, só altera o status pra preservar histórico
        st.write("---")
        st.subheader("Cancelar Assinatura")
        st.caption("O histórico da assinatura é preservado com status 'Cancelada'.")

        ativas_para_cancelar = df[df['Status'] == STATUS_ATIVA]['NomeDaAssinatura'].tolist()

        if ativas_para_cancelar:
            col_sel, col_btn = st.columns([3, 1])
            assinatura_selecionada = col_sel.selectbox(
                "Selecione a assinatura para cancelar:", ativas_para_cancelar, key="cancelar_sel"
            )

            if col_btn.button("Cancelar", type="primary", use_container_width=True):
                try:
                    worksheet = open_worksheet_by_url(SHEET_URL, WORKSHEET_NAME)
                    all_df = pd.DataFrame(worksheet.get_all_records())
                    idx = all_df[all_df['NomeDaAssinatura'] == assinatura_selecionada].index[0]
                    row_num = idx + 2  # +1 header, +1 índice base-1
                    # Coluna 8 = Status
                    worksheet.update_cell(row_num, 8, STATUS_CANCELADA)
                    get_worksheet_data.clear()
                    st.success(f"Assinatura '{assinatura_selecionada}' cancelada. Histórico preservado.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao cancelar: {e}")
        else:
            st.info("Nenhuma assinatura ativa para cancelar.")

    else:
        st.info("Nenhuma assinatura cadastrada ainda. Adicione uma na página 'Adicionar Assinatura'.")
else:
    # Mensagem de erro se não for possível carregar os dados da planilha
    st.error("Não foi possível carregar a planilha. Verifique as configurações.")
