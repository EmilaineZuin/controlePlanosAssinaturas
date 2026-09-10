import datetime
import pytest
import pandas as pd
from subscription_utils import calcular_novo_vencimento, calcular_gasto_mensal_equivalente, classificar_faixa_orcamento, montar_opcoes_selectbox, parse_valor_orcamento, parse_valor_planilha


def test_pytest_funciona():
    assert 1 + 1 == 2


def test_calcular_novo_vencimento_mensal():
    resultado = calcular_novo_vencimento(datetime.date(2026, 1, 15), "Mensal")
    assert resultado == datetime.date(2026, 2, 15)


def test_calcular_novo_vencimento_mensal_fim_de_mes():
    # Janeiro tem 31 dias, fevereiro de 2026 (não bissexto) tem 28
    resultado = calcular_novo_vencimento(datetime.date(2026, 1, 31), "Mensal")
    assert resultado == datetime.date(2026, 2, 28)


def test_calcular_novo_vencimento_trimestral():
    resultado = calcular_novo_vencimento(datetime.date(2026, 1, 31), "Trimestral")
    assert resultado == datetime.date(2026, 4, 30)


def test_calcular_novo_vencimento_semestral():
    resultado = calcular_novo_vencimento(datetime.date(2026, 1, 31), "Semestral")
    assert resultado == datetime.date(2026, 7, 31)


def test_calcular_novo_vencimento_anual_bissexto():
    # 2028 é bissexto (29/02), 2029 não é
    resultado = calcular_novo_vencimento(datetime.date(2028, 2, 29), "Anual")
    assert resultado == datetime.date(2029, 2, 28)


def test_calcular_novo_vencimento_frequencia_desconhecida():
    with pytest.raises(ValueError):
        calcular_novo_vencimento(datetime.date(2026, 1, 1), "Semanal")


def test_calcular_gasto_mensal_equivalente_df_vazio():
    df = pd.DataFrame(columns=["Frequencia", "Valor"])
    assert calcular_gasto_mensal_equivalente(df) == 0.0


def test_calcular_gasto_mensal_equivalente_mistura_frequencias():
    df = pd.DataFrame({
        "Frequencia": ["Mensal", "Trimestral", "Semestral", "Anual"],
        "Valor": [30.0, 90.0, 60.0, 120.0],
    })
    # 30 + (90/3) + (60/6) + (120/12) = 30 + 30 + 10 + 10 = 80
    resultado = calcular_gasto_mensal_equivalente(df)
    assert resultado == pytest.approx(80.0)


def test_calcular_gasto_mensal_equivalente_valor_como_string():
    df = pd.DataFrame({"Frequencia": ["Mensal"], "Valor": ["25.50"]})
    assert calcular_gasto_mensal_equivalente(df) == pytest.approx(25.50)


def test_classificar_faixa_orcamento_sem_orcamento_definido():
    assert classificar_faixa_orcamento(50.0, 0.0) == "sem_orcamento"
    assert classificar_faixa_orcamento(50.0, -10.0) == "sem_orcamento"


def test_classificar_faixa_orcamento_verde():
    assert classificar_faixa_orcamento(50.0, 100.0) == "verde"


def test_classificar_faixa_orcamento_amarelo_no_limite():
    assert classificar_faixa_orcamento(80.0, 100.0) == "amarelo"


def test_classificar_faixa_orcamento_vermelho_no_limite():
    assert classificar_faixa_orcamento(100.0, 100.0) == "vermelho"


def test_classificar_faixa_orcamento_vermelho_acima():
    assert classificar_faixa_orcamento(150.0, 100.0) == "vermelho"


def test_montar_opcoes_selectbox_valor_ja_na_lista():
    resultado = montar_opcoes_selectbox(["A", "B", "C"], "B")
    assert resultado == ["A", "B", "C"]


def test_montar_opcoes_selectbox_valor_fora_da_lista():
    resultado = montar_opcoes_selectbox(["A", "B", "C"], "Legado")
    assert resultado == ["Legado", "A", "B", "C"]


def test_montar_opcoes_selectbox_valor_vazio():
    resultado = montar_opcoes_selectbox(["A", "B", "C"], "")
    assert resultado == ["A", "B", "C"]


def test_montar_opcoes_selectbox_nao_muta_lista_original():
    opcoes_originais = ["A", "B"]
    montar_opcoes_selectbox(opcoes_originais, "Legado")
    assert opcoes_originais == ["A", "B"]


def test_parse_valor_orcamento_none():
    assert parse_valor_orcamento(None) == 0.0


def test_parse_valor_orcamento_string_vazia():
    assert parse_valor_orcamento("") == 0.0


def test_parse_valor_orcamento_ponto_decimal():
    assert parse_valor_orcamento("150.5") == 150.5


def test_parse_valor_orcamento_virgula_decimal():
    assert parse_valor_orcamento("150,5") == 150.5


def test_parse_valor_orcamento_texto_invalido():
    assert parse_valor_orcamento("abc") == 0.0


def test_parse_valor_planilha_virgula_decimal():
    # Planilha com localidade pt_BR formata Valor como "9,99" (vírgula decimal)
    assert parse_valor_planilha("9,99") == pytest.approx(9.99)


def test_parse_valor_planilha_ponto_decimal():
    # Células antigas/importadas podem estar formatadas com ponto decimal
    assert parse_valor_planilha("79.99") == pytest.approx(79.99)


def test_parse_valor_planilha_inteiro():
    assert parse_valor_planilha("999") == pytest.approx(999.0)


def test_parse_valor_planilha_milhar_ponto_e_virgula_decimal():
    # Formato pt_BR com separador de milhar: "1.234,56"
    assert parse_valor_planilha("1.234,56") == pytest.approx(1234.56)


def test_parse_valor_planilha_milhar_virgula_e_ponto_decimal():
    # Formato en_US com separador de milhar: "1,234.56"
    assert parse_valor_planilha("1,234.56") == pytest.approx(1234.56)


def test_parse_valor_planilha_valor_ja_numerico():
    assert parse_valor_planilha(9.99) == pytest.approx(9.99)
