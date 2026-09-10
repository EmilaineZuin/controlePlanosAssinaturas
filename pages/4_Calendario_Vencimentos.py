# --Página que mostra um calendário com os próximos vencimentos das assinaturas.

import streamlit as st
import pandas as pd
import calendar
import datetime
from google_sheets_connector import get_worksheet_data
from config import SHEET_URL, WORKSHEET_NAME, STATUS_ATIVA, DIAS_ALERTA_CRITICO, DIAS_ALERTA_AVISO

# Configuração da página (título, ícone e layout)
st.set_page_config(page_title="Calendário de Vencimentos", page_icon="📅", layout="wide")
st.title("Calendário de Vencimentos 📅")

# --- NAVEGAÇÃO DE MÊS ---
# esse bloco cria botões pra navegar entre meses e guarda o mês/ano no session_state
hoje = datetime.date.today()

if 'cal_year' not in st.session_state:
    st.session_state.cal_year = hoje.year
if 'cal_month' not in st.session_state:
    st.session_state.cal_month = hoje.month

col_prev, col_titulo, col_next = st.columns([1, 4, 1])
with col_prev:
    if st.button("◀ Mês anterior"):
        if st.session_state.cal_month == 1:
            st.session_state.cal_month = 12
            st.session_state.cal_year -= 1
        else:
            st.session_state.cal_month -= 1
        st.rerun()

with col_titulo:
    # Lista de meses em português para exibir no título
    meses_pt = [
        "", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
    ]
    st.markdown(
        f"<h2 style='text-align:center; margin:0'>"
        f"{meses_pt[st.session_state.cal_month]} {st.session_state.cal_year}</h2>",
        unsafe_allow_html=True
    )

with col_next:
    if st.button("Próximo mês ▶"):
        if st.session_state.cal_month == 12:
            st.session_state.cal_month = 1
            st.session_state.cal_year += 1
        else:
            st.session_state.cal_month += 1
        st.rerun()

st.write("---")

# --- CARREGAR DADOS ---
records = get_worksheet_data(SHEET_URL, WORKSHEET_NAME)

if records is None:
    st.error("Não foi possível carregar a planilha.")
    st.stop()

df = pd.DataFrame(records)

if df.empty:
    st.info("Nenhuma assinatura cadastrada.")
    st.stop()

# Filtra apenas assinaturas ativas e converte a coluna de data para datetime
df_ativas = df[df['Status'] == STATUS_ATIVA].copy()
df_ativas['ProximoVencimento'] = pd.to_datetime(df_ativas['ProximoVencimento'], format='%d/%m/%Y')

ano = st.session_state.cal_year
mes = st.session_state.cal_month

# Filtra assinaturas cujo próximo vencimento cai neste mês/ano
df_mes = df_ativas[
    (df_ativas['ProximoVencimento'].dt.month == mes) &
    (df_ativas['ProximoVencimento'].dt.year == ano)
].copy()
# Observação: usamos a coluna do dataframe original pra extrair o dia corretamente
df_mes['dia'] = df_ativas['ProximoVencimento'].dt.day

# Monta dicionário: dia -> lista de assinaturas
por_dia: dict[int, list] = {}
for _, row in df_mes.iterrows():
    d = int(row['dia'])
    por_dia.setdefault(d, []).append({
        'nome': row['NomeDaAssinatura'],
        'valor': float(row['Valor']),
    })

# --- RENDERIZAR CALENDÁRIO HTML ---
dias_semana = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
semanas = calendar.monthcalendar(ano, mes)

th_style = "background:#4062f7;color:white;padding:10px;text-align:center;font-weight:bold;width:14%;"
td_base = "border:1px solid #ddd;padding:8px;vertical-align:top;min-height:90px;width:14%;"
td_empty = td_base + "background:#f5f5f5;"
dia_num_style = "font-weight:bold;font-size:1.1em;"

html = f"<table style='width:100%;border-collapse:collapse;'>"
html += "<tr>" + "".join(f"<th style='{th_style}'>{d}</th>" for d in dias_semana) + "</tr>"

for semana in semanas:
    html += "<tr>"
    for dia in semana:
        if dia == 0:
            # Célula vazia (dias que não pertencem ao mês)
            html += f"<td style='{td_empty}'></td>"
        else:
            data_dia = datetime.date(ano, mes, dia)
            dias_ate = (data_dia - hoje).days

            # Define estilo da célula com base em quanto tempo falta pro vencimento
            if dias_ate < 0:
                td_style = td_base + "background:#fafafa;"
                num_color = "#aaa"
            elif dias_ate < DIAS_ALERTA_CRITICO:
                td_style = td_base + "background:#fff0f0;"
                num_color = "#c0392b"
            elif dias_ate < DIAS_ALERTA_AVISO:
                td_style = td_base + "background:#fff8e1;"
                num_color = "#e67e22"
            else:
                td_style = td_base + "background:#ffffff;"
                num_color = "#333"

            hoje_marker = " ⬅️" if data_dia == hoje else ""
            cell = f"<span style='{dia_num_style}color:{num_color}'>{dia}{hoje_marker}</span>"

            # Se houver assinaturas nesse dia, adiciona badges com nome e valor
            for sub in por_dia.get(dia, []):
                badge_color = "#c0392b" if dias_ate < DIAS_ALERTA_CRITICO else (
                    "#e67e22" if dias_ate < DIAS_ALERTA_AVISO else "#27ae60"
                )
                cell += (
                    f"<br><span style='display:inline-block;margin-top:4px;"
                    f"background:{badge_color};color:white;padding:2px 5px;"
                    f"border-radius:4px;font-size:0.75em;'>"
                    f"{sub['nome']}<br>R$ {sub['valor']:.2f}</span>"
                )

            html += f"<td style='{td_style}'>{cell}</td>"
    html += "</tr>"

html += "</table>"

# Renderiza o HTML na página
st.markdown(html, unsafe_allow_html=True)

# --- LEGENDA ---
st.write("")
leg1, leg2, leg3 = st.columns(3)
leg1.markdown("🔴 **Crítico** — vence em menos de 3 dias")
leg2.markdown("🟠 **Atenção** — vence em menos de 7 dias")
leg3.markdown("🟢 **Normal** — vencimento futuro")

# --- RESUMO DO MÊS ---
if not df_mes.empty:
    st.write("---")
    st.subheader(f"Assinaturas a vencer em {meses_pt[mes]}/{ano}")
    total_mes = df_mes['Valor'].astype(float).sum()
    st.metric("Total do mês", f"R$ {total_mes:.2f}", help=f"{len(df_mes)} assinatura(s)")

    df_resumo = df_mes[['NomeDaAssinatura', 'Valor', 'ProximoVencimento', 'Categoria']].copy()
    df_resumo['ProximoVencimento'] = df_resumo['ProximoVencimento'].dt.strftime('%d/%m/%Y')
    df_resumo = df_resumo.sort_values('ProximoVencimento').rename(columns={
        'NomeDaAssinatura': 'Assinatura',
        'ProximoVencimento': 'Vencimento',
    })
    st.dataframe(df_resumo, use_container_width=True, hide_index=True)
else:
    st.info(f"Nenhuma assinatura ativa vence em {meses_pt[mes]}/{ano}.")
