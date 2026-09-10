# --Página para editar uma assinatura existente.

import streamlit as st
import pandas as pd
import datetime
from google_sheets_connector import get_worksheet_data, open_worksheet_by_url
from config import SHEET_URL, WORKSHEET_NAME, FREQUENCIAS, STATUS_ATIVA, STATUS_CANCELADA, CATEGORIAS, FORMAS_PAGAMENTO
from subscription_utils import montar_opcoes_selectbox

# Configura a página do Streamlit
st.set_page_config(page_title="Editar Assinatura", page_icon="✏️")
st.title("Editar Assinatura ✏️")
st.markdown("Selecione uma assinatura para atualizar seus dados.")

# Carrega os registros da planilha via conector
records = get_worksheet_data(SHEET_URL, WORKSHEET_NAME)

if records is None:
    st.error("Não foi possível carregar a planilha. Verifique as configurações.")
    st.stop()

# Converte pra DataFrame pra facilitar manipulação
df = pd.DataFrame(records)

if df.empty:
    st.info("Nenhuma assinatura cadastrada. Adicione uma primeiro.")
    st.stop()

# --- DEBUG: mostra colunas reais da planilha ---
with st.expander("🔍 Ver colunas da planilha (diagnóstico)"):
    st.write("Colunas encontradas na aba:", list(df.columns))


def _get(serie, *chaves, padrao=""):
    """Tenta múltiplos nomes de coluna e retorna o primeiro valor não nulo.

    Uso: _get(row, 'NomeDaAssinatura', 'Nome', padrao='')
    (estudante: isso ajuda quando a planilha tem nomes de colunas diferentes)
    """
    for chave in chaves:
        if chave in serie.index and pd.notna(serie[chave]):
            return serie[chave]
    return padrao


# Lista de nomes para popular o selectbox
nomes = df['NomeDaAssinatura'].tolist()
nome_selecionado = st.selectbox("Selecione a assinatura:", nomes)

# Pega os dados da assinatura selecionada e o índice na planilha
dados = df[df['NomeDaAssinatura'] == nome_selecionado].iloc[0]
idx_na_sheet = df[df['NomeDaAssinatura'] == nome_selecionado].index[0]
row_num = idx_na_sheet + 2  # +1 header, +1 base-1 gspread

st.write("---")
st.subheader(f"Editando: {nome_selecionado}")

# --- FORMULÁRIO DE EDIÇÃO ---
with st.form("edit_form"):
    col1, col2 = st.columns(2)

    with col1:
        # Campo nome
        novo_nome = st.text_input(
            "Nome da Assinatura",
            value=_get(dados, 'NomeDaAssinatura')
        )

        # Campo valor com tratamento para possíveis valores inválidos
        try:
            val_atual = float(_get(dados, 'Valor', padrao=0.01) or 0.01)
        except (ValueError, TypeError):
            val_atual = 0.01
        novo_valor = st.number_input("Valor (R$)", min_value=0.01, format="%.2f", value=val_atual)

        # Frequência (seleção baseada nas opções do config)
        freq_atual = _get(dados, 'Frequencia', 'Frequência')
        nova_frequencia = st.selectbox(
            "Frequência", FREQUENCIAS,
            index=FREQUENCIAS.index(freq_atual) if freq_atual in FREQUENCIAS else 0
        )

        # Forma de pagamento com montagem de opções tolerante a variações de nomes
        forma_pagamento_atual = _get(dados, 'FormaPagamento', 'Forma de Pagamento', 'FormaDePagamento', 'forma_pagamento')
        opcoes_forma_pagamento = montar_opcoes_selectbox(FORMAS_PAGAMENTO, forma_pagamento_atual)
        index_forma_pagamento = (
            opcoes_forma_pagamento.index(forma_pagamento_atual)
            if forma_pagamento_atual in opcoes_forma_pagamento else 0
        )
        nova_forma_pagamento = st.selectbox(
            "Forma de Pagamento", opcoes_forma_pagamento, index=index_forma_pagamento
        )

    with col2:
        # Próximo vencimento com parsing seguro
        venc_str = _get(dados, 'ProximoVencimento', 'Proximo Vencimento', 'proximo_vencimento')
        try:
            dt_venc = datetime.datetime.strptime(str(venc_str), '%d/%m/%Y').date()
        except (ValueError, TypeError):
            dt_venc = datetime.date.today()
        novo_vencimento = st.date_input("Próximo Vencimento", value=dt_venc)

        # Data de adesão com parsing seguro
        adesao_str = _get(dados, 'DataDeAdesao', 'Data de Adesão', 'DataAdesao')
        try:
            dt_adesao = datetime.datetime.strptime(str(adesao_str), '%d/%m/%Y').date()
        except (ValueError, TypeError):
            dt_adesao = datetime.date.today()
        nova_adesao = st.date_input("Data de Adesão", value=dt_adesao)

        # Categoria com montagem de opções similar à forma de pagamento
        categoria_atual = _get(dados, 'Categoria', 'categoria')
        opcoes_categoria = montar_opcoes_selectbox(CATEGORIAS, categoria_atual)
        index_categoria = (
            opcoes_categoria.index(categoria_atual) if categoria_atual in opcoes_categoria else 0
        )
        nova_categoria = st.selectbox("Categoria", opcoes_categoria, index=index_categoria)

        # Status (ativa/cancelada)
        status_opcoes = [STATUS_ATIVA, STATUS_CANCELADA]
        status_atual = _get(dados, 'Status', 'status', padrao=STATUS_ATIVA)
        status_idx = status_opcoes.index(status_atual) if status_atual in status_opcoes else 0
        novo_status = st.selectbox("Status", status_opcoes, index=status_idx)

    # Botão de salvar do form
    salvar = st.form_submit_button("Salvar Alterações", type="primary")

# --- AÇÃO DE SALVAR ---
# salva e atualizo a linha correspondente na planilha
if salvar:
    if not novo_nome:
        st.warning("O campo 'Nome da Assinatura' é obrigatório.")
    else:
        try:
            worksheet = open_worksheet_by_url(SHEET_URL, WORKSHEET_NAME)
            nova_linha = [
                novo_nome,
                novo_valor,
                nova_frequencia,
                nova_forma_pagamento,
                novo_vencimento.strftime("%d/%m/%Y"),
                nova_adesao.strftime("%d/%m/%Y"),
                nova_categoria,
                novo_status,
            ]
            # Atualiza o intervalo A:H na linha correspondente com os novos valores
            worksheet.update(f'A{row_num}:H{row_num}', [nova_linha])
            get_worksheet_data.clear()
            st.success(f"✅ Assinatura '{novo_nome}' atualizada com sucesso!")
            st.rerun()
        except Exception as e:
            # Mostra erro se houver problema ao salvar (ex: permissão, conexão)
            st.error(f"Erro ao salvar: {e}")
