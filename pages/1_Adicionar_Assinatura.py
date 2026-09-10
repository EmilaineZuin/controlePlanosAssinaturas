# -- Página principal do Streamlit para adicionar novas assinaturas.

import streamlit as st
import datetime
from google_sheets_connector import open_worksheet_by_url, get_worksheet_data
from config import SHEET_URL, WORKSHEET_NAME, FREQUENCIAS, STATUS_ATIVA, CATEGORIAS, FORMAS_PAGAMENTO

# Configura a página do Streamlit (título e ícone)
st.set_page_config(page_title="Adicionar Assinatura", page_icon="➕")
st.title("Cadastro de Novas Assinaturas ➕")
st.markdown("Preencha os campos abaixo para adicionar uma nova assinatura à sua planilha.")

# Tenta abrir a worksheet na planilha do Google Sheets
# aqui eu peço pro conector me devolver a worksheet, se falhar a variável fica False
worksheet = open_worksheet_by_url(SHEET_URL, WORKSHEET_NAME)

if worksheet:
    # Cria um formulário do Streamlit que limpa os campos ao submeter
    with st.form("new_subscription_form", clear_on_submit=True):
        st.subheader("Detalhes da Assinatura")

        # Campos básicos que eu quero que o usuário preencha
        nome = st.text_input("Nome da Assinatura", placeholder="Ex: Netflix, Spotify")
        valor = st.number_input("Valor (R$)", min_value=0.01, format="%.2f")
        frequencia = st.selectbox("Frequência", FREQUENCIAS)
        forma_pagamento = st.selectbox("Forma de Pagamento", FORMAS_PAGAMENTO)
        proximo_vencimento = st.date_input("Próximo Vencimento", min_value=datetime.date.today())
        data_adesao = st.date_input("Data de Adesão")
        categoria = st.selectbox("Categoria", CATEGORIAS)

        # Botão de submissão do formulário
        submitted = st.form_submit_button("Adicionar Assinatura")

        if submitted:
            # Verifica se o campo nome foi preenchido
            if nome:
                # Prepara a nova linha no formato da planilha
                # transformo datas pra string no formato dia/mês/ano porque a planilha espera assim
                new_row = [
                    nome,
                    valor,
                    frequencia,
                    forma_pagamento,
                    proximo_vencimento.strftime("%d/%m/%Y"),
                    data_adesao.strftime("%d/%m/%Y"),
                    categoria,
                    STATUS_ATIVA,
                ]

                # Adiciona a linha na worksheet e limpa o cache do conector, envia os dados pro Google Sheets
                worksheet.append_row(new_row)
                get_worksheet_data.clear()

                # Feedback para o usuário
                st.success("🎉 Assinatura adicionada com sucesso!")
                st.balloons()
            else:
                # Aviso se o nome não foi preenchido
                st.warning("O campo 'Nome da Assinatura' é obrigatório.")
else:
    # Mensagem de erro se a planilha não foi carregada
    st.error("Não foi possível carregar a planilha. Verifique as configurações.")
