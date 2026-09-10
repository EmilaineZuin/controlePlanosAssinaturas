# Configurações centralizadas do projeto

SHEET_URL = "https://docs.google.com/spreadsheets/d/1JOBRMLhruD2WLfDEkVxmWgZ4hn4OrRVtsBC71s0Y_Oc/edit"
WORKSHEET_NAME = "Assinaturas"

# Alertas de vencimento
DIAS_ALERTA_CRITICO = 3   # vermelho
DIAS_ALERTA_AVISO = 7     # laranja

# Frequências disponíveis
FREQUENCIAS = ["Mensal", "Trimestral", "Semestral", "Anual"]

# Status possíveis
STATUS_ATIVA = "Ativa"
STATUS_CANCELADA = "Cancelada"

# Multiplicadores para cálculo anual
MULTIPLICADOR_ANUAL = {
    "Mensal": 12,
    "Trimestral": 4,
    "Semestral": 2,
    "Anual": 1,
}

# Listas fixas para padronização de campos
CATEGORIAS = ["Streaming", "Software", "Saúde", "Educação", "Jogos", "Financeiro", "Outros"]
FORMAS_PAGAMENTO = ["Cartão de Crédito", "Cartão de Débito", "Pix", "Boleto", "Outros"]

# Configuração persistida na aba "Config" da planilha
CONFIG_WORKSHEET_NAME = "Config"
CONFIG_KEY_ORCAMENTO_MENSAL = "OrcamentoMensal"

# Faixas de alerta do orçamento planejado (proporção gasto/orçamento)
ORCAMENTO_ALERTA_AMARELO = 0.8
ORCAMENTO_ALERTA_VERMELHO = 1.0
