import datetime
import pandas as pd
from dateutil.relativedelta import relativedelta

FREQUENCIA_PARA_DELTA = {
    "Mensal": relativedelta(months=1),
    "Trimestral": relativedelta(months=3),
    "Semestral": relativedelta(months=6),
    "Anual": relativedelta(years=1),
}


def calcular_novo_vencimento(vencimento_atual: datetime.date, frequencia: str) -> datetime.date:
    """Avança a data de vencimento em 1 período da frequência informada."""
    delta = FREQUENCIA_PARA_DELTA.get(frequencia)
    if delta is None:
        raise ValueError(f"Frequência desconhecida: {frequencia!r}")
    return vencimento_atual + delta


MULTIPLICADOR_MENSAL = {
    "Mensal": 1.0,
    "Trimestral": 1 / 3,
    "Semestral": 1 / 6,
    "Anual": 1 / 12,
}


def calcular_gasto_mensal_equivalente(df: pd.DataFrame) -> float:
    """Soma o valor de cada assinatura ativa, mensalizado conforme a frequência."""
    if df.empty:
        return 0.0
    total = 0.0
    for _, row in df.iterrows():
        multiplicador = MULTIPLICADOR_MENSAL.get(row["Frequencia"], 0.0)
        total += float(row["Valor"]) * multiplicador
    return total


def classificar_faixa_orcamento(
    gasto: float, orcamento: float, limite_amarelo: float = 0.8, limite_vermelho: float = 1.0
) -> str:
    """Classifica o gasto em relação ao orçamento planejado em uma faixa de cor."""
    if orcamento <= 0:
        return "sem_orcamento"
    proporcao = gasto / orcamento
    if proporcao >= limite_vermelho:
        return "vermelho"
    if proporcao >= limite_amarelo:
        return "amarelo"
    return "verde"


def montar_opcoes_selectbox(opcoes: list, valor_atual: str) -> list:
    """Garante que valor_atual apareça nas opções, mesmo se for um valor legado fora da lista fixa."""
    if not valor_atual or valor_atual in opcoes:
        return list(opcoes)
    return [valor_atual] + list(opcoes)


def parse_valor_orcamento(valor_bruto) -> float:
    """Converte o valor de orçamento lido da planilha (texto) em float, com fallback seguro para 0.0."""
    if valor_bruto is None:
        return 0.0
    texto = str(valor_bruto).strip()
    if not texto:
        return 0.0
    try:
        return float(texto.replace(",", "."))
    except ValueError:
        return 0.0


def parse_valor_planilha(valor_bruto) -> float:
    """Converte o Valor lido da planilha em float, independente da localidade
    usada para formatar a célula (ex: "9,99" ou "9.99" ou "1.234,56").

    gspread numericiza valores automaticamente assumindo formato americano
    (vírgula = milhar, ponto = decimal), o que corrompe células formatadas
    com vírgula decimal (ex: planilha com localidade pt_BR). Por isso a
    leitura da planilha deve pedir o valor bruto (numericise_ignore=["all"])
    e usar esta função para interpretar corretamente o separador decimal.
    """
    texto = str(valor_bruto).strip()
    if "," in texto and "." in texto:
        if texto.rindex(",") > texto.rindex("."):
            texto = texto.replace(".", "").replace(",", ".")
        else:
            texto = texto.replace(",", "")
    elif "," in texto:
        texto = texto.replace(",", ".")
    return float(texto)
