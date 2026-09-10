# Tela do orçamento — componentes para sidebar e cartão de orçamento.

import streamlit as st
from config import (
    SHEET_URL,
    CONFIG_WORKSHEET_NAME,
    CONFIG_KEY_ORCAMENTO_MENSAL,
    ORCAMENTO_ALERTA_AMARELO,
    ORCAMENTO_ALERTA_VERMELHO,
)
from google_sheets_connector import get_config_value, set_config_value
from subscription_utils import parse_valor_orcamento, classificar_faixa_orcamento


def render_orcamento_sidebar() -> float:
    # Mostra o campo de orçamento mensal na sidebar e retorna o valor atualmente salvo.

    # Busca o valor salvo nas configurações (padrão "0" se não existir)
    valor_salvo = parse_valor_orcamento(
        get_config_value(SHEET_URL, CONFIG_WORKSHEET_NAME, CONFIG_KEY_ORCAMENTO_MENSAL, "0")
    )

    # Campo na sidebar para mostrar/editar o orçamento
    st.sidebar.subheader("Orçamento Mensal")
    novo_valor = st.sidebar.number_input(
        "Valor planejado (R$)", min_value=0.0, value=valor_salvo, format="%.2f", key="orcamento_input"
    )

    # Botão que salva o novo valor na planilha de configuração
    if st.sidebar.button("Salvar orçamento"):
        set_config_value(SHEET_URL, CONFIG_WORKSHEET_NAME, CONFIG_KEY_ORCAMENTO_MENSAL, novo_valor)
        st.sidebar.success("Orçamento salvo!")
        st.rerun()

    # Retorna o valor original salvo para usos posteriores na UI
    return valor_salvo


def render_orcamento_card(gasto_mensal_equivalente: float, orcamento: float) -> None:
    """Mostra um card colorido comparando o gasto mensal equivalente com o orçamento planejado.

    (estudante: uso a função de classificação pra decidir se mostro verde, amarelo ou vermelho.)
    """
    faixa = classificar_faixa_orcamento(
        gasto_mensal_equivalente, orcamento, ORCAMENTO_ALERTA_AMARELO, ORCAMENTO_ALERTA_VERMELHO
    )

    st.subheader("Orçamento Planejado")

    # Se não há orçamento definido, instrui o usuário a definir na sidebar
    if faixa == "sem_orcamento":
        st.info("Defina um orçamento mensal na barra lateral para acompanhar seus gastos.")
        return

    # Calcula percentual consumido do orçamento
    percentual = (gasto_mensal_equivalente / orcamento) * 100

    # Monta o texto com valores formatados. Nota: escapamos R$ para evitar interpretação.
    texto = (
        f"Gasto mensal equivalente: R\\$ {gasto_mensal_equivalente:.2f} "
        f"de R\\$ {orcamento:.2f} planejado ({percentual:.0f}%)"
    )

    # Mostra o card com a cor apropriada
    if faixa == "verde":
        st.success(f"🟢 {texto}")
    elif faixa == "amarelo":
        st.warning(f"🟡 {texto}")
    else:
        st.error(f"🔴 {texto}")
