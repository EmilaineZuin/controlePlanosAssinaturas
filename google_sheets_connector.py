import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from subscription_utils import parse_valor_planilha

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


@st.cache_resource
def connect_to_gsheet():
    """Estabelece conexão com o Google Sheets (reutilizada via cache de recurso)."""
    try:
        credentials_info = st.secrets.get("google_credentials")
        if not credentials_info:
            st.error(
                "Credenciais do Google Sheets não configuradas. No Streamlit Cloud, "
                "abra o app em Settings > Secrets e adicione a seção "
                "[google_credentials] com os dados da conta de serviço."
            )
            return None

        creds = Credentials.from_service_account_info(
            credentials_info, scopes=SCOPES
        )
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error(f"Erro ao conectar com o Google Sheets: {e}")
        return None


def open_worksheet_by_url(url: str, worksheet_name: str):
    """Abre uma aba específica da planilha. Usado para operações de escrita."""
    client = connect_to_gsheet()
    if client:
        try:
            spreadsheet = client.open_by_url(url)
            return spreadsheet.worksheet(worksheet_name)
        except gspread.exceptions.SpreadsheetNotFound:
            st.error("A planilha não foi encontrada ou o acesso foi negado.")
            st.warning("Verifique se o e-mail da conta de serviço foi compartilhado como 'Editor'.")
            return None
        except gspread.exceptions.WorksheetNotFound:
            st.error(f"A aba '{worksheet_name}' não foi encontrada na planilha.")
            return None
    return None


@st.cache_data(ttl=60)
def get_worksheet_data(url: str, worksheet_name: str):
    """Retorna todos os registros com cache de 60 segundos (leitura otimizada).

    numericise_ignore=["all"] evita a conversão numérica automática do gspread,
    que assume separador de milhar americano e corrompe valores formatados com
    vírgula decimal (planilhas com localidade pt_BR, por exemplo "9,99" -> 999).
    O campo Valor é convertido explicitamente com parse_valor_planilha, que
    interpreta corretamente os dois formatos.
    """
    worksheet = open_worksheet_by_url(url, worksheet_name)
    if worksheet:
        registros = worksheet.get_all_records(numericise_ignore=["all"])
        for registro in registros:
            if "Valor" in registro:
                registro["Valor"] = parse_valor_planilha(registro["Valor"])
        return registros
    return None


CONFIG_HEADERS = ["Chave", "Valor"]


def get_or_create_config_worksheet(url: str, config_worksheet_name: str):
    """Abre a aba de configuração; cria com cabeçalho se ainda não existir."""
    client = connect_to_gsheet()
    if not client:
        return None
    try:
        spreadsheet = client.open_by_url(url)
    except gspread.exceptions.SpreadsheetNotFound:
        st.error("A planilha não foi encontrada ou o acesso foi negado.")
        return None
    try:
        return spreadsheet.worksheet(config_worksheet_name)
    except gspread.exceptions.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=config_worksheet_name, rows=10, cols=2)
        worksheet.append_row(CONFIG_HEADERS)
        return worksheet


@st.cache_data(ttl=60)
def get_config_value(url: str, config_worksheet_name: str, chave: str, padrao: str = "") -> str:
    """Lê o valor associado a uma chave na aba de configuração (cache de 60s)."""
    worksheet = get_or_create_config_worksheet(url, config_worksheet_name)
    if worksheet is None:
        return padrao
    # numericise_ignore=["all"]: mesmo motivo de get_worksheet_data — evita que
    # o gspread corrompa um valor decimal formatado com vírgula (locale pt_BR).
    for registro in worksheet.get_all_records(numericise_ignore=["all"]):
        if registro.get("Chave") == chave:
            return str(registro.get("Valor", padrao))
    return padrao


def set_config_value(url: str, config_worksheet_name: str, chave: str, valor) -> None:
    """Grava (atualiza ou cria) o valor de uma chave na aba de configuração."""
    worksheet = get_or_create_config_worksheet(url, config_worksheet_name)
    if worksheet is None:
        return
    linhas = worksheet.get_all_values()
    for i, linha in enumerate(linhas):
        if i == 0:
            continue
        if linha and linha[0] == chave:
            worksheet.update_cell(i + 1, 2, valor)
            get_config_value.clear()
            return
    worksheet.append_row([chave, valor])
    get_config_value.clear()
