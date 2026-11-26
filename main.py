import streamlit as st
import pandas as pd
import datetime
from google_sheets_connector import get_worksheet_data
from config import SHEET_URL, WORKSHEET_NAME, DIAS_ALERTA_CRITICO, DIAS_ALERTA_AVISO, STATUS_ATIVA
from subscription_utils import calcular_gasto_mensal_equivalente
from orcamento_ui import render_orcamento_sidebar, render_orcamento_card

st.set_page_config(
    page_title="Gerenciador de Assinaturas",
    page_icon="💳",
    layout="wide"
)

st.title("Seu Painel de Controle de Assinaturas 💳")
st.sidebar.success("Selecione uma opção acima.")
orcamento_atual = render_orcamento_sidebar()
st.write("---")

records = get_worksheet_data(SHEET_URL, WORKSHEET_NAME)

if records is not None:
    df = pd.DataFrame(records)

    if not df.empty:
        df_ativas = df[df['Status'] == STATUS_ATIVA].copy()

        if not df_ativas.empty:
            df_ativas['ProximoVencimento'] = pd.to_datetime(df_ativas['ProximoVencimento'], format='%d/%m/%Y')
            df_ativas['DataDeAdesao'] = pd.to_datetime(df_ativas['DataDeAdesao'], format='%d/%m/%Y')
            hoje = pd.to_datetime(datetime.date.today())

            # --- ALERTAS DE VENCIMENTO PRÓXIMO ---
            df_ativas['DiasRestantes'] = (df_ativas['ProximoVencimento'] - hoje).dt.days
            vencendo_critico = df_ativas[df_ativas['DiasRestantes'].between(0, DIAS_ALERTA_CRITICO - 1)]
            vencendo_aviso = df_ativas[df_ativas['DiasRestantes'].between(DIAS_ALERTA_CRITICO, DIAS_ALERTA_AVISO - 1)]

            if not vencendo_critico.empty:
                for _, row in vencendo_critico.iterrows():
                    dias = int(row['DiasRestantes'])
                    label = "hoje" if dias == 0 else f"em {dias} dia(s)"
                    st.error(
                        f"🚨 **{row['NomeDaAssinatura']}** vence **{label}** "
                        f"— R$ {float(row['Valor']):.2f} "
                        f"({row['ProximoVencimento'].strftime('%d/%m/%Y')})"
                    )

            if not vencendo_aviso.empty:
                for _, row in vencendo_aviso.iterrows():
                    st.warning(
                        f"⚠️ **{row['NomeDaAssinatura']}** vence em {int(row['DiasRestantes'])} dias "
                        f"— R$ {float(row['Valor']):.2f} "
                        f"({row['ProximoVencimento'].strftime('%d/%m/%Y')})"
                    )

            # --- PRÓXIMA ASSINATURA A VENCER ---
            df_futuras = df_ativas[df_ativas['ProximoVencimento'] >= hoje].sort_values(by="ProximoVencimento")

            st.subheader("🚨 Próxima Assinatura a Vencer")

            if not df_futuras.empty:
                proxima = df_futuras.iloc[0]
                dias_restantes = int((proxima['ProximoVencimento'] - hoje).days)

                col1, col2, col3 = st.columns(3)
                col1.metric("Assinatura", proxima['NomeDaAssinatura'])
                col2.metric("Valor", f"R$ {float(proxima['Valor']):.2f}")

                if dias_restantes <= DIAS_ALERTA_CRITICO:
                    col3.metric(
                        "Vence em",
                        f"{dias_restantes} dias",
                        delta=f"Vence em {proxima['ProximoVencimento'].strftime('%d/%m')}",
                        delta_color="inverse"
                    )
                elif dias_restantes <= DIAS_ALERTA_AVISO:
                    col3.metric(
                        "Vence em",
                        f"{dias_restantes} dias",
                        delta=f"Vence em {proxima['ProximoVencimento'].strftime('%d/%m')}",
                        delta_color="off"
                    )
                else:
                    col3.metric("Vence em", f"{dias_restantes} dias")
            else:
                st.info("Nenhuma assinatura com vencimento futuro encontrada.")

            st.write("---")

            # --- CARDS DE DESTAQUE ---
            st.subheader("Destaques Gerais")
            col1, col2, col3, col4 = st.columns(4)

            df_pagas = df_ativas[df_ativas['ProximoVencimento'] < hoje].sort_values(by="ProximoVencimento", ascending=False)
            if not df_pagas.empty:
                ultima_paga = df_pagas.iloc[0]
                col1.metric("Última Assinatura Paga", ultima_paga['NomeDaAssinatura'],
                            help=f"Venceu em: {ultima_paga['ProximoVencimento'].strftime('%d/%m/%Y')}")
            else:
                col1.metric("Última Assinatura Paga", "Nenhuma")

            mais_cara = df_ativas.loc[df_ativas['Valor'].idxmax()]
            col2.metric("Assinatura Mais Cara", mais_cara['NomeDaAssinatura'],
                        f"R$ {float(mais_cara['Valor']):.2f}")

            mais_nova = df_ativas.loc[df_ativas['DataDeAdesao'].idxmax()]
            col3.metric("Assinatura Mais Nova", mais_nova['NomeDaAssinatura'],
                        help=f"Adesão em: {mais_nova['DataDeAdesao'].strftime('%d/%m/%Y')}")

            mais_antiga = df_ativas.loc[df_ativas['DataDeAdesao'].idxmin()]
            col4.metric("Assinatura Mais Antiga", mais_antiga['NomeDaAssinatura'],
                        help=f"Adesão em: {mais_antiga['DataDeAdesao'].strftime('%d/%m/%Y')}")

            st.write("---")

            # --- ORÇAMENTO PLANEJADO ---
            gasto_mensal_equivalente = calcular_gasto_mensal_equivalente(df_ativas)
            render_orcamento_card(gasto_mensal_equivalente, orcamento_atual)

        else:
            st.info("Você não possui assinaturas ativas cadastradas.")
    else:
        st.info("Comece cadastrando sua primeira assinatura na página 'Adicionar Assinatura'!")
else:
    st.error("Falha ao carregar dados da planilha. Verifique a conexão e as configurações.")

st.write("---")

st.markdown("""
    ### Sobre o Projeto
    Este aplicativo ajuda você a organizar e gerenciar suas assinaturas ativas.
    - **Adicione:** Registre novas assinaturas.
    - **Visualize:** Tenha uma visão completa dos seus gastos recorrentes.
    - **Edite:** Atualize dados de qualquer assinatura.
    - **Calendário:** Veja os vencimentos em formato de calendário mensal.
    - **Relatórios:** Exporte seus dados em CSV ou PDF.
""")
