# Gerenciador de Assinaturas 💳

Aplicação web para controle de assinaturas e serviços recorrentes, construída com **Streamlit** e **Google Sheets** como banco de dados.

---
---
## Histórico de evolução do projeto
### Etapas das entregas
	I - Fundamentação e Justificativa - Entregar uma apresentação do caso de estudo proposto.
	II – Documentação - Neste momento deve ser entregue uma documentação do projeto e defesa da motivação do desenvolvimento dele.
	III - Desenvolvimento Inicial - Dar inicio ao desenvolvimento do projeto, primeiramente foi criado um protótipo simples.
	IV - Desenvolvimento Inicial - Nesta fase o projeto deve começar a tomar forma e foi publicado no GitHub e no Streamlit.
	V - Desenvolvimento Final - Agora o projeto deve ser finalizado atendendo aquilo que foi proposto no inicio do projeto.
	VI - CIA - Organização Final - O projeto tem que ser sujeito a testes e ter melhorias de usabilidade e tratamentos de erros aplicados.
	VII - CIA - Elaborar documentação README no GitHub, Refinar detalhes finais da aplicação e preparar o material de apresentação final (por exemplo, slides ou roteiro)
---

## Funcionalidades

| Página | Descrição |
|---|---|
| **Painel Principal** | Dashboard com alertas de vencimento, próxima cobrança e destaques gerais |
| **Adicionar Assinatura** | Formulário para cadastrar novos serviços |
| **Visualizar Assinaturas** | Tabela filtrada, gráfico por categoria, cancelamento e export CSV |
| **Editar Assinatura** | Formulário pré-preenchido para atualizar qualquer campo |
| **Calendário de Vencimentos** | Calendário mensal navegável com assinaturas destacadas por urgência |
| **Exportar Relatório** | Download em CSV ou PDF com resumo financeiro |

---

## Estrutura de Arquivos

```
controlePlanosAssinaturas/
├── Página_Principal.py          # Dashboard principal (ponto de entrada do Streamlit)
├── config.py                    # Configurações centralizadas (URL da planilha, constantes)
├── google_sheets_connector.py   # Conexão com Google Sheets + cache de dados
├── pages/
│   ├── 1_Adicionar_Assinatura.py
│   ├── 2_Visualizar_Assinaturas.py
│   ├── 3_Editar_Assinatura.py
│   ├── 4_Calendario_Vencimentos.py
│   └── 5_Exportar_Relatorio.py
├── secrets.json                 # Credenciais Google (não commitar)
├── requirements.txt             # Dependências completas (gerado por pip freeze)
└── requirements2.txt            # Dependências principais comentadas
```

---

## Estrutura da Planilha Google Sheets

A aba deve se chamar `Assinaturas` com as seguintes colunas **na ordem exata**:

| Coluna | Nome | Exemplo |
|---|---|---|
| A | NomeDaAssinatura | Netflix |
| B | Valor | 45.90 |
| C | Frequencia | Mensal |
| D | FormaPagamento | Cartão de Crédito |
| E | ProximoVencimento | 15/06/2025 |
| F | DataDeAdesao | 01/01/2023 |
| G | Categoria | Streaming |
| H | Status | Ativa |

**Valores válidos:**
- `Frequencia`: `Mensal`, `Trimestral`, `Semestral`, `Anual`
- `Status`: `Ativa`, `Cancelada`

---

## Pré-requisitos

- Python 3.9+
- Conta Google com acesso ao Google Sheets API
- Credenciais de Service Account do Google Cloud

---

## Instalação

### 1. Clone o repositório

```bash
git clone <url-do-repositorio>
cd controlePlanosAssinaturas
```

### 2. Crie e ative o ambiente virtual

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install streamlit gspread google-auth pandas plotly fpdf2
```

Ou usando o arquivo de requisitos:

```bash
pip install -r requirements.txt
pip install fpdf2   # para exportação PDF
```

### 4. Configure as credenciais do Google

#### 4.1 Crie uma Service Account no Google Cloud

1. Acesse [console.cloud.google.com](https://console.cloud.google.com)
2. Crie um novo projeto (ou use um existente)
3. Ative a **Google Sheets API** e a **Google Drive API**
4. Em **IAM e Admin > Contas de serviço**, crie uma nova conta
5. Baixe a chave JSON da conta de serviço

#### 4.2 Compartilhe a planilha

- Abra sua planilha no Google Sheets
- Clique em **Compartilhar**
- Adicione o e-mail da conta de serviço (ex: `nome@projeto.iam.gserviceaccount.com`) como **Editor**

#### 4.3 Configure os secrets do Streamlit

Crie o arquivo `.streamlit/secrets.toml` na raiz do projeto:

```toml
[google_credentials]
type = "service_account"
project_id = "seu-projeto"
private_key_id = "..."
private_key = "-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----\n"
client_email = "sua-conta@projeto.iam.gserviceaccount.com"
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."
```

> **Atenção:** Nunca commite o arquivo `secrets.toml` ou `secrets.json`. Adicione ao `.gitignore`.

### 5. Configure a URL da planilha

Edite o arquivo `config.py` e atualize `SHEET_URL` com a URL da sua planilha:

```python
SHEET_URL = "https://docs.google.com/spreadsheets/d/SEU_ID_AQUI/edit"
```

---

## Executar a aplicação

```bash
streamlit run "Página_Principal.py"
```

O app abrirá automaticamente no navegador em `http://localhost:8501`.

---

## Detalhes Técnicos

### Cache de dados

Os dados do Google Sheets são carregados com `@st.cache_data(ttl=60)`, ou seja, são buscados da API no máximo uma vez por minuto. Após qualquer operação de escrita (adicionar, editar, cancelar), o cache é limpo automaticamente com `get_worksheet_data.clear()`.

### Alertas de vencimento

Configurados em `config.py`:

```python
DIAS_ALERTA_CRITICO = 3   # exibe banner vermelho
DIAS_ALERTA_AVISO   = 7   # exibe banner laranja
```

### Cancelamento vs. exclusão

Ao cancelar uma assinatura na página **Visualizar**, o campo `Status` é atualizado para `Cancelada` na planilha. O registro nunca é excluído, preservando o histórico completo para relatórios futuros.

### Exportação PDF

A exportação PDF utiliza a biblioteca `fpdf2`. Se ela não estiver instalada, o app exibe uma instrução de instalação. O PDF gerado inclui resumo financeiro e tabela completa de assinaturas.

---

## Melhorias Implementadas (v2.0)

- **Configuração centralizada** — `config.py` elimina duplicação de constantes entre páginas
- **Cache de leitura** — `@st.cache_data(ttl=60)` reduz chamadas à API do Google Sheets
- **Editar assinatura** — nova página com formulário pré-preenchido para atualizar qualquer campo
- **Alertas visuais de vencimento** — banners vermelhos (≤ 3 dias) e laranja (≤ 7 dias) no painel principal
- **Calendário de vencimentos** — visualização mensal navegável com código de cores por urgência
- **Cancelar em vez de excluir** — preserva histórico alterando `Status` para `Cancelada`
- **Exportação CSV** — download direto da tabela filtrada em qualquer página
- **Exportação PDF** — relatório formatado com resumo financeiro e tabela de assinaturas
- **Frequência Semestral** — adicionada como opção além de Mensal, Trimestral e Anual
- **Cálculo anual corrigido** — trimestral (×4) e semestral (×2) agora incluídos no gasto anual estimado
