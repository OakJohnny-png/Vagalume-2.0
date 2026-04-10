# =============================================================================
#  Lúmen Bot — NEMA
#  A inteligência que acende a sua obra
#  + Processador de Chamados de Iluminação Pública
#  + Solicitação de Materiais (Manual e via PDF)
#  Setor de Obras e Instalações Elétricas — NEMA
#  Desenvolvido com Python + Streamlit
# =============================================================================

import os
import re
import json
import glob
import io
import subprocess
from datetime import datetime

import pandas as pd
import streamlit as st
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment

try:
    import bcrypt
    BCRYPT_OK = True
except ImportError:
    import hashlib
    BCRYPT_OK = False

try:
    import pdfplumber
    PDF_DISPONIVEL = True
except ImportError:
    PDF_DISPONIVEL = False

# ---------------------------------------------------------------------------
# Configuração global da página
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Lúmen Bot — NEMA",
    page_icon="💡",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Constantes e caminhos
# ---------------------------------------------------------------------------
BASE_DIR          = os.path.dirname(os.path.abspath(__file__))
EXCEL_PATH        = os.path.join(BASE_DIR, "estoque.xlsx")
HISTORICO_DIR     = os.path.join(BASE_DIR, "historico_devolucoes")
REQUISICOES_DIR   = os.path.join(BASE_DIR, "historico_requisicoes")
RASCUNHO_PATH     = os.path.join(BASE_DIR, "rascunho_solicitacao.json")
USUARIOS_PATH     = os.path.join(BASE_DIR, "usuarios.json")

REF_CLIENTES      = os.path.join(BASE_DIR, "clientes.xlsx")
REF_VENDEDORES    = os.path.join(BASE_DIR, "vendedores.xlsx")
REF_COMPRADORES   = os.path.join(BASE_DIR, "compradores.xlsx")
REF_TIPOS_VENDA   = os.path.join(BASE_DIR, "tipos_venda.xlsx")
REF_DEPARTAMENTOS = os.path.join(BASE_DIR, "departamentos.xlsx")

os.makedirs(HISTORICO_DIR, exist_ok=True)
os.makedirs(REQUISICOES_DIR, exist_ok=True)


# ===========================================================================
# FUNÇÕES DE AUTENTICAÇÃO
# ===========================================================================

def _hash_senha(senha: str) -> str:
    if BCRYPT_OK:
        return bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()
    else:
        return hashlib.sha256(senha.encode()).hexdigest()


def _verificar_senha(senha: str, hash_salvo: str) -> bool:
    if BCRYPT_OK:
        try:
            return bcrypt.checkpw(senha.encode(), hash_salvo.encode())
        except Exception:
            return False
    else:
        return hashlib.sha256(senha.encode()).hexdigest() == hash_salvo


def carregar_usuarios() -> dict:
    """Carrega o arquivo de usuários. Cria admin padrão se não existir."""
    if not os.path.exists(USUARIOS_PATH):
        usuarios = {
            "admin": {
                "nome": "Administrador",
                "senha_hash": _hash_senha("Ameixaseca9988?"),
                "perfil": "admin",
                "ativo": True,
            }
        }
        salvar_usuarios(usuarios)
        return usuarios
    try:
        with open(USUARIOS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def salvar_usuarios(usuarios: dict):
    with open(USUARIOS_PATH, "w", encoding="utf-8") as f:
        json.dump(usuarios, f, ensure_ascii=False, indent=4)
    # Tenta fazer commit automático no Git para persistir no Streamlit Cloud
    _git_commit_file(USUARIOS_PATH, "Atualização de usuários")


def _git_commit_file(filepath: str, msg: str):
    """Faz git add + commit + push do arquivo para persistir no Streamlit Cloud."""
    try:
        cwd = BASE_DIR
        subprocess.run(["git", "add", filepath], cwd=cwd, capture_output=True, timeout=10)
        subprocess.run(["git", "commit", "-m", msg], cwd=cwd, capture_output=True, timeout=10)
        subprocess.run(["git", "push"], cwd=cwd, capture_output=True, timeout=30)
    except Exception:
        pass  # Falha silenciosa — funciona localmente sem Git


def autenticar(usuario: str, senha: str) -> bool:
    usuarios = carregar_usuarios()
    u = usuarios.get(usuario.strip().lower())
    if not u:
        return False
    if not u.get("ativo", True):
        return False
    return _verificar_senha(senha, u["senha_hash"])


def get_perfil(usuario: str) -> str:
    usuarios = carregar_usuarios()
    u = usuarios.get(usuario.strip().lower(), {})
    return u.get("perfil", "usuario")


# ===========================================================================
# TELA DE LOGIN
# ===========================================================================

def mostrar_login():
    # CSS da tela de login
    st.markdown("""
    <style>
        /* Esconde sidebar e header padrão na tela de login */
        [data-testid="stSidebar"] { display: none !important; }
        header { display: none !important; }
        #MainMenu { display: none !important; }
        footer { display: none !important; }

        /* Fundo vermelho full-screen */
        .stApp {
            background-color: #FF2800 !important;
        }
        .block-container {
            padding: 0 !important;
            max-width: 100% !important;
        }

        /* Labels dos inputs em branco */
        label { color: white !important; font-size: 1rem !important; font-weight: 500 !important; }

        /* Inputs brancos com borda */
        input[type="text"], input[type="password"] {
            background-color: white !important;
            border-radius: 8px !important;
            border: none !important;
            font-size: 1rem !important;
            padding: 0.6rem 1rem !important;
        }

        /* Botão de login amarelo */
        div[data-testid="stForm"] button[kind="primaryFormSubmit"],
        div[data-testid="stForm"] button {
            background-color: #FEA700 !important;
            color: #000 !important;
            font-weight: 700 !important;
            font-size: 1.1rem !important;
            border-radius: 10px !important;
            border: none !important;
            width: 50% !important;
            padding: 0.7rem !important;
        }

        /* Mensagem de erro */
        .login-erro {
            color: #fff;
            background-color: rgba(0,0,0,0.25);
            border-radius: 8px;
            padding: 0.5rem 1rem;
            text-align: center;
            margin-top: 0.5rem;
            font-weight: 600;
        }
    </style>
    """, unsafe_allow_html=True)

    # Header: NEMA logo + título + botão login (decorativo)
    col_logo, col_titulo, col_btn = st.columns([2, 5, 2])
    with col_logo:
        st.markdown("""
        <div style='padding: 1.5rem 1rem 1rem 2rem;'>
            <div style='border: 3px solid white; display:inline-block; padding: 4px 10px;'>
                <span style='color:white; font-size:2rem; font-weight:900; letter-spacing:2px;
                             font-family: Arial Black, sans-serif;'>N<span style='font-size:1.4rem;'>E</span>M<span style='font-size:1.4rem;'>A</span></span>
            </div>
            <div style='border-top: 3px solid white; margin-top:4px; width:90%;'></div>
        </div>
        """, unsafe_allow_html=True)
    with col_titulo:
        st.markdown("""
        <div style='padding: 1.5rem 0 0 0;'>
            <h1 style='color:white; font-size:clamp(1.8rem,5vw,3rem); font-weight:900;
                       margin:0; letter-spacing:1px; font-family: Arial Black, sans-serif;'>
                LÚMEN BOT
            </h1>
            <p style='color:white; font-size:clamp(0.8rem,2vw,1rem); margin:0.2rem 0 0 0;
                      font-style:italic; opacity:0.9;'>
                A inteligência que acende a sua obra.
            </p>
        </div>
        """, unsafe_allow_html=True)
    with col_btn:
        st.markdown("""
        <div style='padding: 1.8rem 2rem 0 0; text-align:right;'>
            <span style='background:#FEA700; color:#000; font-weight:700; font-size:1.1rem;
                         padding: 0.6rem 2rem; border-radius:10px; display:inline-block;'>
                Login
            </span>
        </div>
        """, unsafe_allow_html=True)

    # Área central do formulário
    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

    col_esq, col_form, col_dir = st.columns([1, 2, 1])
    with col_form:
        # Ícone do robô
        st.markdown("""
        <div style='text-align:center; font-size:4rem; margin-bottom:0.5rem;'>🤖</div>
        """, unsafe_allow_html=True)

        with st.form("form_login", clear_on_submit=False):
            usuario_input = st.text_input("Usuário", placeholder="", key="login_usuario")
            senha_input   = st.text_input("Senha", type="password", placeholder="", key="login_senha")
            st.markdown("<div style='height:0.3rem'></div>", unsafe_allow_html=True)
            entrar = st.form_submit_button("Entrar", use_container_width=True)

        if entrar:
            if autenticar(usuario_input, senha_input):
                st.session_state.logado = True
                st.session_state.usuario_logado = usuario_input.strip().lower()
                st.session_state.perfil_logado = get_perfil(usuario_input.strip().lower())
                st.session_state.pagina_atual = "🏠 Início"
                st.rerun()
            else:
                st.markdown(
                    "<div class='login-erro'>❌ Usuário ou senha incorretos.</div>",
                    unsafe_allow_html=True
                )

    # Espaçador
    st.markdown("<div style='height: 4rem;'></div>", unsafe_allow_html=True)

    # Rodapé escuro
    st.markdown("""
    <div style='background-color:#8B0000; padding: 1.5rem 2rem; margin-top: 2rem;'>
        <p style='color:#ccc; font-size:0.8rem; margin:0;'>
            © 2024 <strong>NEMA TECNOLOGIA | LÚMEN BOT</strong> v1.0 | Rio do Sul, SC |
            Todos os direitos reservados.
        </p>
        <p style='color:#ccc; font-size:0.8rem; margin:0.3rem 0 0 0;'>
            Este sistema é para uso autorizado e monitorado para a manutenção e gerenciamento
            de iluminação pública na região. Em caso de dúvidas, contate o suporte técnico
            NEMA no telefone (47) 5555-0199.
        </p>
    </div>
    """, unsafe_allow_html=True)


# ===========================================================================
# FUNÇÕES AUXILIARES — APP PRINCIPAL
# ===========================================================================

@st.cache_data
def carregar_estoque() -> pd.DataFrame:
    df = pd.read_excel(EXCEL_PATH, dtype=str)
    for col in ["Código", "Descrição", "Localização"]:
        if col not in df.columns:
            st.error(f"Coluna '{col}' não encontrada no arquivo estoque.xlsx.")
            st.stop()
    df["Código"] = df["Código"].str.strip()
    df["Descrição"] = df["Descrição"].str.strip()
    df["Localização"] = df["Localização"].str.strip()
    df.dropna(how="all", inplace=True)
    df.sort_values("Descrição", inplace=True, ignore_index=True)
    return df


@st.cache_data
def carregar_referencia(caminho: str, colunas: list) -> list:
    if not os.path.exists(caminho):
        return []
    try:
        df = pd.read_excel(caminho, dtype=str).fillna("")
        resultado = []
        for _, row in df.iterrows():
            partes = [str(row[c]).strip() for c in colunas if c in df.columns and str(row[c]).strip()]
            if partes:
                resultado.append(" — ".join(partes) if len(partes) > 1 else partes[0])
        return resultado
    except Exception:
        return []


@st.cache_data
def carregar_clientes() -> list:
    return carregar_referencia(REF_CLIENTES, ["Código", "Nome"])


@st.cache_data
def carregar_vendedores() -> list:
    return carregar_referencia(REF_VENDEDORES, ["Código", "Nome"])


@st.cache_data
def carregar_compradores() -> list:
    return carregar_referencia(REF_COMPRADORES, ["Nome"])


@st.cache_data
def carregar_tipos_venda() -> list:
    return carregar_referencia(REF_TIPOS_VENDA, ["Tipo"])


@st.cache_data
def carregar_departamentos() -> list:
    return carregar_referencia(REF_DEPARTAMENTOS, ["Código", "Nome"])


def gerar_protocolo() -> str:
    hoje = datetime.now().strftime("%d%m%Y")
    padrao = os.path.join(HISTORICO_DIR, f"DEV_{hoje}*.json")
    arquivos_hoje = glob.glob(padrao)
    sequencial = len(arquivos_hoje) + 1
    return f"{hoje}.{sequencial:03d}"


def gerar_numero_solicitacao(cliente_cod: str) -> str:
    hoje = datetime.now().strftime("%d%m%Y")
    cod = re.sub(r'\D', '', str(cliente_cod))
    prefixo = f"{cod}{hoje}"
    padrao = os.path.join(REQUISICOES_DIR, f"SOL_{prefixo}*.json")
    existentes = glob.glob(padrao)
    sequencial = len(existentes) + 1
    return f"{prefixo}{sequencial:02d}"


def df_lista_vazio() -> pd.DataFrame:
    return pd.DataFrame(columns=["Código", "Descrição", "Localização", "Quantidade"])


def salvar_rascunho(cabecalho: dict, itens: list):
    dados = {"cabecalho": cabecalho, "itens": itens}
    with open(RASCUNHO_PATH, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)


def carregar_rascunho() -> dict:
    if os.path.exists(RASCUNHO_PATH):
        try:
            with open(RASCUNHO_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def limpar_rascunho():
    if os.path.exists(RASCUNHO_PATH):
        os.remove(RASCUNHO_PATH)


def inicializar_session_state():
    if "logado" not in st.session_state:
        st.session_state.logado = False
    if "usuario_logado" not in st.session_state:
        st.session_state.usuario_logado = ""
    if "perfil_logado" not in st.session_state:
        st.session_state.perfil_logado = "usuario"
    if "lista_devolucao" not in st.session_state:
        st.session_state.lista_devolucao = df_lista_vazio()
    if "empresa" not in st.session_state:
        st.session_state.empresa = ""
    if "protocolo" not in st.session_state:
        st.session_state.protocolo = gerar_protocolo()
    if "req_cabecalho" not in st.session_state:
        st.session_state.req_cabecalho = {}
    if "req_itens" not in st.session_state:
        st.session_state.req_itens = []
    if "req_manual_itens" not in st.session_state:
        rascunho = carregar_rascunho()
        st.session_state.req_manual_itens = rascunho.get("itens", [])
    if "req_manual_cab" not in st.session_state:
        rascunho = carregar_rascunho()
        st.session_state.req_manual_cab = rascunho.get("cabecalho", {})
    if "pagina_atual" not in st.session_state:
        st.session_state.pagina_atual = "🏠 Início"


# ---------------------------------------------------------------------------
# Funções auxiliares — DEVOLUÇÃO
# ---------------------------------------------------------------------------

def salvar_devolucao():
    protocolo = st.session_state.protocolo
    dados = {
        "protocolo": protocolo,
        "empresa": st.session_state.empresa,
        "data_hora": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "itens": st.session_state.lista_devolucao.to_dict(orient="records"),
    }
    caminho = os.path.join(HISTORICO_DIR, f"DEV_{protocolo}.json")
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)
    st.success(f"Devolução salva com sucesso! Protocolo: **{protocolo}**")


def nova_devolucao():
    st.session_state.lista_devolucao = df_lista_vazio()
    st.session_state.empresa = ""
    st.session_state.protocolo = gerar_protocolo()


def exportar_excel_devolucao() -> bytes:
    df_export = st.session_state.lista_devolucao.copy()
    df_export.insert(0, "Protocolo", st.session_state.protocolo)
    df_export.insert(1, "Empresa", st.session_state.empresa)
    df_export["Data/Hora"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df_export.to_excel(writer, index=False, sheet_name="Devolução")
    return buffer.getvalue()


def listar_historico() -> list:
    arquivos = sorted(glob.glob(os.path.join(HISTORICO_DIR, "DEV_*.json")), reverse=True)
    registros = []
    for arq in arquivos:
        with open(arq, "r", encoding="utf-8") as f:
            dados = json.load(f)
        registros.append({
            "arquivo": arq,
            "protocolo": dados.get("protocolo", "—"),
            "empresa": dados.get("empresa", "—"),
            "data_hora": dados.get("data_hora", "—"),
            "qtd_itens": len(dados.get("itens", [])),
            "itens": dados.get("itens", []),
        })
    return registros


# ---------------------------------------------------------------------------
# Funções auxiliares — PROCESSADOR DE CHAMADOS IP
# ---------------------------------------------------------------------------

ROUTES = {
    "ROTA 1": ["CENTRO", "JARDIM AMERICA"],
    "ROTA 2": ["ALBERTINA", "LARANJEIRAS", "BOA VISTA", "EUGENIO SCHNEIDER"],
    "ROTA 3": ["FUNDO CANOAS", "CANOAS", "PROGRESSO", "PAMPLONA", "CANTA GALO"],
    "ROTA 4": ["BELA VISTA", "VILA NOVA", "BAIRRO NOVO", "JARDIM ESPERANÇA"],
    "ROTA 5": ["INDUSTRIAL", "JARDIM INDUSTRIAL", "ZONA INDUSTRIAL"],
}


def processar_chamados(
    uploaded_file, fonte_escolhida,
    cor_fundo_rota, cor_fonte_rota, tamanho_rota,
    cor_fundo_bairro, cor_fonte_bairro, tamanho_bairro,
    cor_fundo_prob, cor_fonte_prob, tamanho_prob,
) -> bytes:
    xls = pd.read_excel(uploaded_file, sheet_name=None, header=None, dtype=str)
    abas_disponiveis = {nome.strip().upper(): nome for nome in xls.keys()}
    data_by_route = {r: {} for r in ROUTES}

    for route, neighborhoods in ROUTES.items():
        for neighborhood in neighborhoods:
            nome_aba_upper = neighborhood.upper()
            if nome_aba_upper in abas_disponiveis:
                nome_real_aba = abas_disponiveis[nome_aba_upper]
                df = xls[nome_real_aba]
                if len(df.columns) >= 4:
                    df_filtered = df[
                        (df[3].isin(['NÃO REALIZADO', 'NÃO EXECUTADO'])) &
                        (df[1].notna()) & (df[1].str.strip() != "")
                    ]
                    problems = df_filtered[1].tolist()
                    if problems:
                        data_by_route[route][neighborhood] = problems

    wb = Workbook()
    ws = wb.active
    ws.title = "Chamados Pendentes"
    ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE

    hex_bg_rota   = cor_fundo_rota.replace('#', '')
    hex_fg_rota   = cor_fonte_rota.replace('#', '')
    hex_bg_bairro = cor_fundo_bairro.replace('#', '')
    hex_fg_bairro = cor_fonte_bairro.replace('#', '')
    hex_bg_prob   = cor_fundo_prob.replace('#', '')
    hex_fg_prob   = cor_fonte_prob.replace('#', '')

    font_rota   = Font(name=fonte_escolhida, size=tamanho_rota,   color=hex_fg_rota,   bold=True)
    fill_rota   = PatternFill(start_color=hex_bg_rota,   end_color=hex_bg_rota,   fill_type="solid")
    font_bairro = Font(name=fonte_escolhida, size=tamanho_bairro, color=hex_fg_bairro, bold=True)
    fill_bairro = PatternFill(start_color=hex_bg_bairro, end_color=hex_bg_bairro, fill_type="solid")
    font_prob   = Font(name=fonte_escolhida, size=tamanho_prob,   color=hex_fg_prob)
    fill_prob   = PatternFill(start_color=hex_bg_prob,   end_color=hex_bg_prob,   fill_type="solid")
    thin_border = Border(left=Side(style='thin'), right=Side(style='thin'),
                         top=Side(style='thin'), bottom=Side(style='thin'))

    current_row = 1
    for route, neighborhoods in data_by_route.items():
        if not neighborhoods:
            continue
        cell = ws.cell(row=current_row, column=1, value=route)
        cell.font = font_rota; cell.fill = fill_rota
        cell.border = thin_border; cell.alignment = Alignment(wrap_text=True)
        current_row += 1
        first_bairro = True
        for bairro, problems in neighborhoods.items():
            if not first_bairro:
                current_row += 1
            first_bairro = False
            cell = ws.cell(row=current_row, column=1, value=bairro)
            cell.font = font_bairro; cell.fill = fill_bairro
            cell.border = thin_border; cell.alignment = Alignment(wrap_text=True)
            current_row += 1
            for problem in problems:
                cell = ws.cell(row=current_row, column=1, value=str(problem).strip())
                cell.font = font_prob
                if hex_bg_prob != "FFFFFF":
                    cell.fill = fill_prob
                cell.border = thin_border; cell.alignment = Alignment(wrap_text=True)
                current_row += 1

    ws.column_dimensions['A'].width = 150
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output.getvalue()


# ---------------------------------------------------------------------------
# Funções auxiliares — SOLICITAÇÃO DE MATERIAIS
# ---------------------------------------------------------------------------

def extrair_dados_requisicao(pdf_bytes) -> dict:
    cabecalho = {}
    itens = []

    with pdfplumber.open(pdf_bytes) as pdf:
        texto_completo = ""
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                texto_completo += t + "\n"

    linhas = texto_completo.split("\n")

    for linha in linhas:
        m = re.search(r'Orçamento[:\s]+(\d+)', linha)
        if m and 'orcamento_pdf' not in cabecalho:
            cabecalho['orcamento_pdf'] = m.group(1).strip()

        m = re.search(r'Cliente[:\s]+(\d+)\s+(.+?)(?=\s{2,}|Comprador|$)', linha)
        if m and 'cliente_nome' not in cabecalho:
            cabecalho['cliente_cod'] = m.group(1).strip()
            cabecalho['cliente_nome'] = m.group(2).strip()

        m = re.search(r'Vendedor[.\s:]+(.+?)(?=\s{2,}|Prazo|$)', linha)
        if m and 'vendedor' not in cabecalho:
            cabecalho['vendedor'] = m.group(1).strip()

        m = re.search(r'Comprador[.\s:]+(.+?)(?=\s{2,}|Em\.\.|$)', linha)
        if m and 'comprador' not in cabecalho:
            val = re.sub(r'Em\.+:\s*\S+', '', m.group(1)).strip()
            if val:
                cabecalho['comprador'] = val

        m = re.search(r'Tipo de Venda[.\s:]+(.+)', linha)
        if m and 'tipo_venda' not in cabecalho:
            cabecalho['tipo_venda'] = m.group(1).strip()

        m = re.search(r'Departamento[.\s:]+(.+)', linha)
        if m and 'departamento' not in cabecalho:
            cabecalho['departamento'] = m.group(1).strip()

        m = re.search(r'Marcações[.\s:]+(.+)', linha)
        if m and 'marcacoes' not in cabecalho:
            val = m.group(1).strip().lstrip(':').strip()
            cabecalho['marcacoes'] = val if val else "—"

        m = re.search(r'Observação\s*:\s*(.+)', linha)
        if m and 'observacao' not in cabecalho:
            cabecalho['observacao'] = m.group(1).strip()

    _UN = r'PC|KG|MT|CX|PAR|VB|SC|BD|GL|TB|KIT|FD|CJ|JG|RL|LT|UN|M'

    # Padrão 1: Seq + Localização + Código + Descrição + UN + Qtd (PDFs com Loc.Física)
    # Localização aceita: 29.A3, 93.D4, 51G.B2, 68, 69 A2, etc.
    _LOC = r'\d{1,3}(?:[A-Z./]\S*)?(?:\s+[A-Z]\w*)?'
    padrao_com_loc = re.compile(
        r'^(\d{2})\s+(' + _LOC + r')\s+(\d{3,6})\s+(.+?)\s+(' + _UN + r')\s+([\d.,]+)',
        re.IGNORECASE
    )
    # Padrão 1b: Seq + Localização + Código + Descrição colada com UN + Qtd
    padrao_com_loc_colado = re.compile(
        r'^(\d{2})\s+(' + _LOC + r')\s+(\d{3,6})\s+(.+?)(' + _UN + r')\s+([\d.,]+)$',
        re.IGNORECASE
    )
    # Padrão 2: Seq + Código + Descrição + UN + Qtd (PDFs sem Loc.Física)
    padrao_normal = re.compile(
        r'^(\d{2})\s+(\d{3,6})\s+(.+?)\s+(' + _UN + r')\s+([\d.,]+)',
        re.IGNORECASE
    )
    # Padrão 3: Seq + Código + Descrição colada com UN + Qtd
    padrao_colado = re.compile(
        r'^(\d{2})\s+(\d{3,6})\s+(.+?)(' + _UN + r')\s+([\d.,]+)$',
        re.IGNORECASE
    )

    for linha in linhas:
        linha_strip = linha.strip()

        # Tenta padrão com localização primeiro
        m = padrao_com_loc.match(linha_strip)
        if m:
            itens.append({
                "Seq": m.group(1), "Localização": m.group(2),
                "Código": m.group(3), "Descrição": m.group(4).strip(),
                "UN": m.group(5).upper(),
                "Quantidade": float(m.group(6).replace(',', '.') or 0),
            })
            continue

        m = padrao_com_loc_colado.match(linha_strip)
        if m:
            itens.append({
                "Seq": m.group(1), "Localização": m.group(2),
                "Código": m.group(3), "Descrição": m.group(4).strip(),
                "UN": m.group(5).upper(),
                "Quantidade": float(m.group(6).replace(',', '.') or 0),
            })
            continue

        # Tenta padrão sem localização
        m = padrao_normal.match(linha_strip)
        if m:
            itens.append({
                "Seq": m.group(1), "Localização": "",
                "Código": m.group(2), "Descrição": m.group(3).strip(),
                "UN": m.group(4).upper(),
                "Quantidade": float(m.group(5).replace(',', '.') or 0),
            })
            continue

        m = padrao_colado.match(linha_strip)
        if m:
            itens.append({
                "Seq": m.group(1), "Localização": "",
                "Código": m.group(2), "Descrição": m.group(3).strip(),
                "UN": m.group(4).upper(),
                "Quantidade": float(m.group(5).replace(',', '.') or 0),
            })

    return {"cabecalho": cabecalho, "itens": itens}


def salvar_requisicao(cabecalho: dict, itens: list) -> str:
    cliente_cod = cabecalho.get('cliente_cod', '0')
    num_sol = gerar_numero_solicitacao(cliente_cod)
    cabecalho['num_solicitacao'] = num_sol

    nome_arquivo = f"SOL_{num_sol}.json"
    caminho = os.path.join(REQUISICOES_DIR, nome_arquivo)
    dados = {
        "cabecalho": cabecalho,
        "itens": itens,
        "data_importacao": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
    }
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)
    return nome_arquivo


def listar_requisicoes() -> list:
    arquivos = sorted(
        glob.glob(os.path.join(REQUISICOES_DIR, "SOL_*.json")),
        reverse=True,
    )
    registros = []
    for arq in arquivos:
        with open(arq, "r", encoding="utf-8") as f:
            dados = json.load(f)
        cab = dados.get("cabecalho", {})
        registros.append({
            "arquivo": arq,
            "num_solicitacao": cab.get("num_solicitacao", "—"),
            "orcamento_pdf": cab.get("orcamento_pdf", "—"),
            "cliente_cod": cab.get("cliente_cod", "—"),
            "cliente_nome": cab.get("cliente_nome", "—"),
            "vendedor": cab.get("vendedor", "—"),
            "departamento": cab.get("departamento", "—"),
            "observacao": cab.get("observacao", "—"),
            "data_importacao": dados.get("data_importacao", "—"),
            "qtd_itens": len(dados.get("itens", [])),
            "cabecalho": cab,
            "itens": dados.get("itens", []),
        })
    return registros


def exportar_requisicao_excel(cabecalho: dict, itens: list) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Solicitação"

    fonte_titulo    = Font(name="Calibri", size=12, bold=True, color="FFFFFF")
    fill_titulo     = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    fonte_cab_label = Font(name="Calibri", size=10, bold=True)
    fonte_cab_valor = Font(name="Calibri", size=10)
    fill_cab        = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
    fonte_header    = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
    fill_header     = PatternFill(start_color="2E75B6", end_color="2E75B6", fill_type="solid")
    fonte_item      = Font(name="Calibri", size=10)
    fill_item_alt   = PatternFill(start_color="EBF3FB", end_color="EBF3FB", fill_type="solid")
    borda = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'), bottom=Side(style='thin')
    )
    alinhamento_centro = Alignment(horizontal="center", vertical="center")
    alinhamento_esq    = Alignment(horizontal="left", vertical="center", wrap_text=True)

    linha = 1

    ws.merge_cells(f"A{linha}:G{linha}")
    cell = ws.cell(row=linha, column=1, value="SOLICITAÇÃO DE MATERIAIS — LÚMEN BOT / NEMA")
    cell.font = fonte_titulo; cell.fill = fill_titulo
    cell.alignment = alinhamento_centro
    ws.row_dimensions[linha].height = 22
    linha += 1

    campos_cab = [
        ("Nº Solicitação", cabecalho.get("num_solicitacao", "—")),
        ("Nº Orçamento PDF", cabecalho.get("orcamento_pdf", "—")),
        ("Tipo de Pedido", cabecalho.get("tipo_pedido", "—")),
        ("Cliente", f"{cabecalho.get('cliente_cod', '')} — {cabecalho.get('cliente_nome', '')}"),
        ("Vendedor", cabecalho.get("vendedor", "—")),
        ("Comprador", cabecalho.get("comprador", "—")),
        ("Tipo de Venda", cabecalho.get("tipo_venda", "—")),
        ("Departamento", cabecalho.get("departamento", "—")),
        ("Marcações", cabecalho.get("marcacoes", "—")),
        ("Observação", cabecalho.get("observacao", "—")),
    ]

    for label, valor in campos_cab:
        ws.merge_cells(f"A{linha}:B{linha}")
        cell_label = ws.cell(row=linha, column=1, value=label)
        cell_label.font = fonte_cab_label; cell_label.fill = fill_cab
        cell_label.border = borda; cell_label.alignment = alinhamento_esq

        ws.merge_cells(f"C{linha}:G{linha}")
        cell_valor = ws.cell(row=linha, column=3, value=valor)
        cell_valor.font = fonte_cab_valor
        cell_valor.border = borda; cell_valor.alignment = alinhamento_esq
        linha += 1

    linha += 1

    headers     = ["Seq", "Local.", "Código", "Descrição", "UN", "Quantidade"]
    col_widths  = [6, 14, 12, 52, 8, 12]
    col_letters = ["A", "B", "C", "D", "E", "F"]

    for i, h in enumerate(headers):
        cell = ws.cell(row=linha, column=i + 1, value=h)
        cell.font = fonte_header; cell.fill = fill_header
        cell.border = borda; cell.alignment = alinhamento_centro
    ws.row_dimensions[linha].height = 18
    linha += 1

    for idx, item in enumerate(itens):
        fill_atual = fill_item_alt if idx % 2 == 0 else None
        valores = [
            item.get("Seq", ""),
            item.get("Localização", ""),
            item.get("Código", ""),
            item.get("Descrição", ""),
            item.get("UN", ""),
            item.get("Quantidade", 0),
        ]
        for i, val in enumerate(valores):
            cell = ws.cell(row=linha, column=i + 1, value=val)
            cell.font = fonte_item; cell.border = borda
            cell.alignment = alinhamento_esq if i == 3 else alinhamento_centro
            if fill_atual:
                cell.fill = fill_atual
        ws.row_dimensions[linha].height = 15
        linha += 1

    for col_letter, width in zip(col_letters, col_widths):
        ws.column_dimensions[col_letter].width = width
    ws.column_dimensions["G"].width = 5

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output.getvalue()


# ===========================================================================
# INICIALIZAÇÃO
# ===========================================================================
inicializar_session_state()

# Garante que o arquivo de usuários existe
carregar_usuarios()

# ---------------------------------------------------------------------------
# CONTROLE DE FLUXO: LOGIN ou APP
# ---------------------------------------------------------------------------
if not st.session_state.logado:
    mostrar_login()
    st.stop()

# ---------------------------------------------------------------------------
# CSS do app principal (só carrega após login)
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    [data-testid="stSidebar"] {
        min-width: 220px !important;
        max-width: 260px !important;
    }
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
    }
    [data-testid="stSidebar"] .stRadio label {
        font-size: 1rem !important;
        padding: 6px 0 !important;
    }
    [data-testid="stDataFrame"] {
        overflow-x: auto !important;
    }
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 0.95rem;
        font-weight: 600;
    }
    @media (max-width: 768px) {
        .block-container {
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
        }
        h1 { font-size: 1.8rem !important; }
        h2 { font-size: 1.3rem !important; }
        h3 { font-size: 1.1rem !important; }
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Carrega dados
# ---------------------------------------------------------------------------
df_estoque = carregar_estoque()
lista_clientes      = carregar_clientes()
lista_vendedores    = carregar_vendedores()
lista_compradores   = carregar_compradores()
lista_tipos_venda   = carregar_tipos_venda()
lista_departamentos = carregar_departamentos()

# ---------------------------------------------------------------------------
# SIDEBAR — Navegação principal
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding: 1rem 0 0.5rem 0;'>
        <span style='font-size:2.5rem;'>💡</span>
        <h2 style='color:#F5A623; margin:0.2rem 0 0 0; font-size:1.4rem;'>Lúmen Bot</h2>
        <p style='color:#888; font-size:0.75rem; margin:0; font-style:italic;'>
            A inteligência que acende a sua obra
        </p>
        <p style='color:#aaa; font-size:0.65rem; margin:0.2rem 0 0 0; letter-spacing:2px;'>NEMA</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    # Monta lista de páginas conforme perfil
    paginas_disponiveis = ["🏠 Início", "🔍 Finder", "💡 Chamados IP", "📋 Solicitação de Materiais"]
    if st.session_state.perfil_logado == "admin":
        paginas_disponiveis.append("👤 Gestão de Usuários")

    # Garante que a página atual é válida
    if st.session_state.pagina_atual not in paginas_disponiveis:
        st.session_state.pagina_atual = "🏠 Início"

    pagina = st.radio(
        "Navegação",
        paginas_disponiveis,
        index=paginas_disponiveis.index(st.session_state.pagina_atual),
        label_visibility="collapsed",
    )
    st.session_state.pagina_atual = pagina

    st.markdown("---")
    st.caption(f"👤 {st.session_state.usuario_logado}  |  {st.session_state.perfil_logado}")
    st.caption(f"Estoque: {len(df_estoque)} itens")

    if st.button("🚪 Sair", use_container_width=True):
        st.session_state.logado = False
        st.session_state.usuario_logado = ""
        st.session_state.perfil_logado = "usuario"
        st.session_state.pagina_atual = "🏠 Início"
        st.rerun()


# ===========================================================================
# PÁGINA: INÍCIO
# ===========================================================================
if pagina == "🏠 Início":
    st.markdown("""
    <div style='text-align:center; padding: 3rem 1rem 1.5rem 1rem;'>
        <span style='font-size:4rem;'>💡</span>
        <h1 style='font-size:clamp(2rem, 8vw, 4rem); color:#F5A623; margin: 0.3rem 0 0 0;
                   font-weight:800; letter-spacing:1px;'>Lúmen Bot</h1>
        <p style='font-size:clamp(0.9rem, 3vw, 1.2rem); color:#888; margin:0.5rem 0 0 0;
                  font-style:italic;'>A inteligência que acende a sua obra</p>
        <p style='font-size:clamp(0.75rem, 2.5vw, 0.95rem); color:#aaa; margin:0.3rem 0 0 0;
                  letter-spacing:3px; text-transform:uppercase; font-weight:600;'>NEMA</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.info(
        "Use o menu lateral para navegar entre as funcionalidades do sistema.\n\n"
        "- **Finder**: pesquise itens do estoque por código ou descrição.\n"
        "- **Chamados IP**: processe planilhas de chamados de iluminação pública.\n"
        "- **Solicitação de Materiais**: crie, importe e gerencie solicitações de materiais."
    )


# ===========================================================================
# PÁGINA: FINDER
# ===========================================================================
elif pagina == "🔍 Finder":
    st.title("🔍 Finder — Busca de Materiais")
    st.markdown("Pesquise itens pelo **Código** ou pela **Descrição**.")

    termo = st.text_input("Digite o código ou a descrição do item:", placeholder="Ex: 1001 ou CABO")

    if termo.strip():
        mask = (
            df_estoque["Código"].str.contains(termo.strip(), case=False, na=False)
            | df_estoque["Descrição"].str.contains(termo.strip(), case=False, na=False)
        )
        resultado = df_estoque[mask].sort_values("Descrição").reset_index(drop=True)

        if resultado.empty:
            st.warning("Nenhum item encontrado para o termo pesquisado.")
        else:
            st.success(f"{len(resultado)} item(ns) encontrado(s).")
            st.dataframe(resultado, use_container_width=True, hide_index=True)
    else:
        st.dataframe(df_estoque, use_container_width=True, hide_index=True)


# ===========================================================================
# PÁGINA: CHAMADOS IP
# ===========================================================================
elif pagina == "💡 Chamados IP":
    st.title("💡 Processador de Chamados de Iluminação Pública")
    st.write("Faça o upload da planilha Excel contendo as abas dos bairros e personalize a formatação do arquivo final.")

    with st.expander("🎨 Personalização de Formatação", expanded=True):
        st.subheader("Configurações de Estilo")

        fonte_escolhida = st.selectbox(
            "Estilo da Fonte",
            ["Helvetica", "Arial", "Calibri", "Times New Roman", "Tahoma"],
            key="fonte_chamados"
        )

        st.subheader("1. Formatação das Rotas")
        col_rota1, col_rota2 = st.columns(2)
        with col_rota1:
            cor_fundo_rota = st.color_picker("Cor de Fundo (Rotas)", "#FF0000", key="bg_rota")
        with col_rota2:
            cor_fonte_rota = st.color_picker("Cor da Fonte (Rotas)", "#000000", key="fg_rota")
        tamanho_rota = st.number_input("Tamanho da Fonte (Rotas)", min_value=8, max_value=36, value=16, key="size_rota")

        st.subheader("2. Formatação dos Bairros")
        col_bairro1, col_bairro2 = st.columns(2)
        with col_bairro1:
            cor_fundo_bairro = st.color_picker("Cor de Fundo (Bairros)", "#D3D3D3", key="bg_bairro")
        with col_bairro2:
            cor_fonte_bairro = st.color_picker("Cor da Fonte (Bairros)", "#000000", key="fg_bairro")
        tamanho_bairro = st.number_input("Tamanho da Fonte (Bairros)", min_value=8, max_value=36, value=16, key="size_bairro")

        st.subheader("3. Formatação dos Problemas")
        col_prob1, col_prob2 = st.columns(2)
        with col_prob1:
            cor_fundo_prob = st.color_picker("Cor de Fundo (Problemas)", "#FFFFFF", key="bg_prob")
        with col_prob2:
            cor_fonte_prob = st.color_picker("Cor da Fonte (Problemas)", "#000000", key="fg_prob")
        tamanho_prob = st.number_input("Tamanho da Fonte (Problemas)", min_value=8, max_value=36, value=14, key="size_prob")

    st.markdown("---")
    uploaded_file = st.file_uploader("Arraste e solte sua planilha Excel (.xlsx) aqui", type=["xlsx"], key="upload_chamados")

    if uploaded_file is not None:
        if st.button("Processar Planilha", key="btn_processar"):
            with st.spinner('Lendo e processando os dados...'):
                try:
                    dados_excel = processar_chamados(
                        uploaded_file, fonte_escolhida,
                        cor_fundo_rota, cor_fonte_rota, tamanho_rota,
                        cor_fundo_bairro, cor_fonte_bairro, tamanho_bairro,
                        cor_fundo_prob, cor_fonte_prob, tamanho_prob,
                    )
                    st.success("✅ Processamento concluído com sucesso!")
                    st.download_button(
                        label="📥 Baixar Planilha Pronta",
                        data=dados_excel,
                        file_name="Chamados_Pendentes_Rotas.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="download_chamados"
                    )
                except Exception as e:
                    st.error(f"❌ Ocorreu um erro ao processar o arquivo: {e}")


# ===========================================================================
# PÁGINA: SOLICITAÇÃO DE MATERIAIS
# ===========================================================================
elif pagina == "📋 Solicitação de Materiais":
    st.title("📋 Solicitação de Materiais")

    sub_manual, sub_pdf, sub_historico = st.tabs([
        "✏️ Criar Manualmente",
        "📄 Importar via PDF",
        "📂 Solicitações",
    ])

    # -------------------------------------------------------------------
    # SUB-ABA: CRIAR MANUALMENTE
    # -------------------------------------------------------------------
    with sub_manual:
        st.subheader("✏️ Nova Solicitação Manual")

        rascunho_existente = carregar_rascunho()
        if rascunho_existente and rascunho_existente.get("itens"):
            st.info(
                f"💾 Há um rascunho salvo com **{len(rascunho_existente['itens'])}** item(ns). "
                "Os dados foram restaurados automaticamente."
            )

        st.markdown("---")
        st.subheader("📌 Dados do Cabeçalho")
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            man_tipo_pedido = st.selectbox(
                "Tipo de Pedido",
                ["", "Orçamento", "Pedido", "Devolução"],
                key="man_tipo_pedido"
            )

            opcoes_cliente = [""] + lista_clientes
            man_cliente_sel = st.selectbox("Cliente", opcoes_cliente, key="man_cliente_sel")
            if man_cliente_sel and " — " in man_cliente_sel:
                man_cliente_cod = man_cliente_sel.split(" — ")[0].strip()
                man_cliente_nome = man_cliente_sel.split(" — ", 1)[1].strip()
            else:
                man_cliente_cod = ""
                man_cliente_nome = man_cliente_sel

            opcoes_comprador = [""] + lista_compradores
            man_comprador = st.selectbox("Comprador", opcoes_comprador, key="man_comprador")

        with col_m2:
            opcoes_vendedor = [""] + lista_vendedores
            man_vendedor_sel = st.selectbox("Vendedor", opcoes_vendedor, key="man_vendedor_sel")

            opcoes_tipo_venda = [""] + lista_tipos_venda
            man_tipo_venda = st.selectbox("Tipo de Venda", opcoes_tipo_venda, key="man_tipo_venda")

            opcoes_depto = [""] + lista_departamentos
            man_departamento = st.selectbox("Departamento", opcoes_depto, key="man_departamento")

            man_marcacoes = st.text_input("Marcações", key="man_marcacoes")
            man_observacao = st.text_input("Observação", key="man_observacao")

        st.markdown("---")
        st.subheader("📦 Adicionar Itens")
        col_busca, col_qtd, col_un = st.columns([3, 1, 1])

        with col_busca:
            man_busca = st.text_input(
                "Buscar item no estoque (código ou descrição):",
                key="man_busca_item",
                placeholder="Ex: CABO ou 160001"
            )

        man_item_sel = None
        if man_busca.strip():
            mask_man = (
                df_estoque["Código"].str.contains(man_busca.strip(), case=False, na=False)
                | df_estoque["Descrição"].str.contains(man_busca.strip(), case=False, na=False)
            )
            man_opcoes = df_estoque[mask_man].sort_values("Descrição").reset_index(drop=True)

            if not man_opcoes.empty:
                rotulos_man = [
                    f"{row['Código']} — {row['Descrição']} [{row['Localização']}]"
                    for _, row in man_opcoes.iterrows()
                ]
                escolha_man = st.selectbox("Selecione o item:", rotulos_man, key="man_selectbox")
                idx_man = rotulos_man.index(escolha_man)
                man_item_sel = man_opcoes.iloc[idx_man]
            else:
                st.warning("Nenhum item encontrado no estoque.")

        with col_qtd:
            man_quantidade = st.number_input("Quantidade", min_value=1, value=1, step=1, key="man_qtd")

        with col_un:
            man_un = st.selectbox(
                "UN",
                ["PC", "M", "KG", "UN", "CJ", "JG", "RL", "MT", "LT", "CX", "PAR", "KIT"],
                key="man_un"
            )

        if st.button("➕ Adicionar Item à Solicitação", use_container_width=True, key="btn_add_man"):
            if man_item_sel is None:
                st.error("Selecione um item do estoque antes de adicionar.")
            else:
                seq_num = len(st.session_state.req_manual_itens) + 1
                novo_item = {
                    "Seq": f"{seq_num:02d}",
                    "Localização": man_item_sel["Localização"],
                    "Código": man_item_sel["Código"],
                    "Descrição": man_item_sel["Descrição"],
                    "UN": man_un,
                    "Quantidade": float(man_quantidade),
                }
                st.session_state.req_manual_itens.append(novo_item)
                salvar_rascunho(
                    {"tipo_pedido": man_tipo_pedido, "cliente_cod": man_cliente_cod,
                     "cliente_nome": man_cliente_nome},
                    st.session_state.req_manual_itens
                )
                st.success(f"✅ Item **{man_item_sel['Descrição']}** adicionado.")

        st.markdown("---")
        st.subheader(f"📝 Lista de Itens ({len(st.session_state.req_manual_itens)} item(ns))")

        if st.session_state.req_manual_itens:
            df_man = pd.DataFrame(st.session_state.req_manual_itens)
            st.dataframe(df_man, use_container_width=True, hide_index=True)

            col_rem, col_limpar = st.columns(2)
            with col_rem:
                idx_remover = st.number_input(
                    "Nº Seq para remover:", min_value=1,
                    max_value=len(st.session_state.req_manual_itens), value=1,
                    step=1, key="man_idx_rem"
                )
                if st.button("❌ Remover item", key="btn_rem_man"):
                    st.session_state.req_manual_itens = [
                        it for it in st.session_state.req_manual_itens
                        if it["Seq"] != f"{idx_remover:02d}"
                    ]
                    for i, it in enumerate(st.session_state.req_manual_itens):
                        it["Seq"] = f"{i+1:02d}"
                    salvar_rascunho({}, st.session_state.req_manual_itens)
                    st.rerun()

            with col_limpar:
                if st.button("🗑️ Limpar toda a lista", key="btn_limpar_man"):
                    st.session_state.req_manual_itens = []
                    limpar_rascunho()
                    st.rerun()
        else:
            st.info("Nenhum item adicionado ainda.")

        st.markdown("---")
        st.subheader("💾 Salvar / Exportar")
        st.info(
            "ℹ️ O **Nº da Solicitação** é gerado automaticamente ao salvar, "
            "no formato: CódigoCliente + Data + Sequencial (ex: 10900904202601)."
        )
        col_sv1, col_sv2 = st.columns(2)

        def _montar_cabecalho_manual():
            return {
                "tipo_pedido": man_tipo_pedido,
                "cliente_cod": man_cliente_cod,
                "cliente_nome": man_cliente_nome,
                "comprador": man_comprador,
                "vendedor": man_vendedor_sel,
                "tipo_venda": man_tipo_venda,
                "departamento": man_departamento,
                "marcacoes": man_marcacoes,
                "observacao": man_observacao,
                "orcamento_pdf": "",
            }

        with col_sv1:
            if st.button("💾 Salvar Solicitação", use_container_width=True, key="btn_salvar_man"):
                if not st.session_state.req_manual_itens:
                    st.error("Adicione pelo menos um item antes de salvar.")
                elif not man_cliente_cod:
                    st.error("Selecione um cliente antes de salvar.")
                else:
                    cab_man = _montar_cabecalho_manual()
                    nome_salvo = salvar_requisicao(cab_man, st.session_state.req_manual_itens)
                    num_gerado = cab_man.get("num_solicitacao", "—")
                    limpar_rascunho()
                    st.session_state.req_manual_itens = []
                    st.success(f"✅ Solicitação salva! Nº: **{num_gerado}** | Arquivo: **{nome_salvo}**")

        with col_sv2:
            if st.session_state.req_manual_itens:
                cab_man_exp = _montar_cabecalho_manual()
                dados_man_excel = exportar_requisicao_excel(cab_man_exp, st.session_state.req_manual_itens)
                st.download_button(
                    label="📥 Exportar para Excel",
                    data=dados_man_excel,
                    file_name=f"SOL_{man_cliente_cod or 'nova'}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    key="btn_dl_man"
                )

    # -------------------------------------------------------------------
    # SUB-ABA: IMPORTAR VIA PDF
    # -------------------------------------------------------------------
    with sub_pdf:
        st.subheader("📄 Importar Solicitação via PDF")
        st.markdown(
            "Faça o upload de um arquivo PDF de requisição de materiais. "
            "O sistema irá **ler, interpretar e extrair** automaticamente os dados."
        )

        if not PDF_DISPONIVEL:
            st.error("❌ A biblioteca **pdfplumber** não está instalada. Execute `pip install pdfplumber`.")
        else:
            st.markdown("---")
            pdf_upload = st.file_uploader(
                "Selecione o arquivo PDF da requisição:",
                type=["pdf"],
                key="upload_req_pdf"
            )

            if pdf_upload is not None:
                with st.spinner("🔍 Lendo e interpretando o PDF..."):
                    try:
                        resultado = extrair_dados_requisicao(pdf_upload)
                        cabecalho = resultado["cabecalho"]
                        itens = resultado["itens"]
                        st.session_state.req_cabecalho = cabecalho
                        st.session_state.req_itens = itens
                        st.success(f"✅ PDF lido com sucesso! **{len(itens)}** item(ns) encontrado(s).")
                    except Exception as e:
                        st.error(f"❌ Erro ao processar o PDF: {e}")
                        cabecalho = {}
                        itens = []

                if cabecalho or itens:
                    st.markdown("---")
                    st.subheader("📌 Dados do Cabeçalho")
                    col_c1, col_c2 = st.columns(2)
                    with col_c1:
                        st.markdown(f"**Nº Orçamento PDF:** {cabecalho.get('orcamento_pdf', '—')}")
                        st.markdown(f"**Cliente:** {cabecalho.get('cliente_cod', '')} — {cabecalho.get('cliente_nome', '—')}")
                        st.markdown(f"**Vendedor:** {cabecalho.get('vendedor', '—')}")
                        st.markdown(f"**Comprador:** {cabecalho.get('comprador', '—')}")
                    with col_c2:
                        st.markdown(f"**Tipo de Venda:** {cabecalho.get('tipo_venda', '—')}")
                        st.markdown(f"**Departamento:** {cabecalho.get('departamento', '—')}")
                        st.markdown(f"**Marcações:** {cabecalho.get('marcacoes', '—')}")
                        st.markdown(f"**Observação:** {cabecalho.get('observacao', '—')}")

                    st.markdown("---")
                    st.subheader(f"📦 Itens Extraídos ({len(itens)} itens)")
                    if itens:
                        df_itens = pd.DataFrame(itens)
                        st.dataframe(df_itens, use_container_width=True, hide_index=True)
                    else:
                        st.warning("Nenhum item foi extraído do PDF.")

                    st.markdown("---")
                    st.subheader("💾 Ações")
                    col_a1, col_a2 = st.columns(2)
                    with col_a1:
                        if st.button("💾 Salvar no Sistema", use_container_width=True, key="btn_salvar_req"):
                            if not itens:
                                st.error("Não há itens para salvar.")
                            else:
                                nome_salvo = salvar_requisicao(cabecalho, itens)
                                num_gerado = cabecalho.get("num_solicitacao", "—")
                                st.success(f"✅ Salvo! Nº Solicitação: **{num_gerado}** | Arquivo: **{nome_salvo}**")
                    with col_a2:
                        if itens:
                            dados_excel_req = exportar_requisicao_excel(cabecalho, itens)
                            st.download_button(
                                label="📥 Exportar para Excel",
                                data=dados_excel_req,
                                file_name=f"REQ_{cabecalho.get('orcamento_pdf', 'requisicao')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True,
                                key="btn_download_req"
                            )

    # -------------------------------------------------------------------
    # SUB-ABA: SOLICITAÇÕES (HISTÓRICO)
    # -------------------------------------------------------------------
    with sub_historico:
        st.subheader("📂 Solicitações")

        requisicoes_salvas = listar_requisicoes()

        if not requisicoes_salvas:
            st.info("Nenhuma solicitação salva ainda.")
        else:
            st.markdown(f"**{len(requisicoes_salvas)}** solicitação(ões) registrada(s).")
            st.markdown("---")

            clientes_dict: dict = {}
            for req in requisicoes_salvas:
                chave = f"{req['cliente_cod']} — {req['cliente_nome']}"
                if chave not in clientes_dict:
                    clientes_dict[chave] = []
                clientes_dict[chave].append(req)

            for cliente_label, reqs in sorted(clientes_dict.items()):
                st.markdown(f"### 👤 {cliente_label}  ·  {len(reqs)} solicitação(ões)")
                for req in reqs:
                    cab = req["cabecalho"]
                    titulo_exp = (
                        f"📄 Nº Sol.: {req['num_solicitacao']}  |  "
                        f"PDF: {req['orcamento_pdf']}  |  "
                        f"Tipo: {cab.get('tipo_pedido', cab.get('tipo_venda', '—'))}  |  "
                        f"Itens: {req['qtd_itens']}  |  "
                        f"Data: {req['data_importacao']}"
                    )
                    with st.expander(titulo_exp):
                        col_h1, col_h2 = st.columns(2)
                        with col_h1:
                            st.markdown(f"**Vendedor:** {cab.get('vendedor', '—')}")
                            st.markdown(f"**Comprador:** {cab.get('comprador', '—')}")
                            st.markdown(f"**Departamento:** {cab.get('departamento', '—')}")
                        with col_h2:
                            st.markdown(f"**Tipo de Venda:** {cab.get('tipo_venda', '—')}")
                            st.markdown(f"**Marcações:** {cab.get('marcacoes', '—')}")
                            st.markdown(f"**Observação:** {cab.get('observacao', '—')}")

                        if req["itens"]:
                            df_req_hist = pd.DataFrame(req["itens"])
                            st.dataframe(df_req_hist, use_container_width=True, hide_index=True)

                        dados_re_export = exportar_requisicao_excel(cab, req["itens"])
                        st.download_button(
                            label="📥 Exportar Excel",
                            data=dados_re_export,
                            file_name=f"SOL_{req['num_solicitacao']}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key=f"re_export_{req['num_solicitacao']}"
                        )
                st.markdown("---")


# ===========================================================================
# PÁGINA: GESTÃO DE USUÁRIOS (somente admin)
# ===========================================================================
elif pagina == "👤 Gestão de Usuários":
    if st.session_state.perfil_logado != "admin":
        st.error("❌ Acesso negado. Esta página é exclusiva para administradores.")
        st.stop()

    st.title("👤 Gestão de Usuários")
    st.markdown("Gerencie os usuários do sistema. Apenas o **administrador** tem acesso a esta página.")

    usuarios_atuais = carregar_usuarios()

    # --- Lista de usuários ---
    st.subheader("📋 Usuários Cadastrados")
    dados_tabela = []
    for login, info in usuarios_atuais.items():
        dados_tabela.append({
            "Login": login,
            "Nome": info.get("nome", "—"),
            "Perfil": info.get("perfil", "usuario"),
            "Ativo": "✅ Sim" if info.get("ativo", True) else "❌ Não",
        })
    if dados_tabela:
        st.dataframe(pd.DataFrame(dados_tabela), use_container_width=True, hide_index=True)

    st.markdown("---")

    # --- Cadastrar novo usuário ---
    st.subheader("➕ Cadastrar Novo Usuário")
    with st.form("form_novo_usuario", clear_on_submit=True):
        col_u1, col_u2 = st.columns(2)
        with col_u1:
            novo_login  = st.text_input("Login (sem espaços)", placeholder="ex: joao.silva")
            novo_nome   = st.text_input("Nome completo", placeholder="ex: João Silva")
        with col_u2:
            novo_perfil = st.selectbox("Perfil", ["usuario", "admin"])
            nova_senha  = st.text_input("Senha", type="password")
            st.success(f"✅ Usuário **{login_excluir}** excluído com sucesso!")
            conf_senha  = st.text_input("Confirmar Senha", type="password")

        salvar_novo = st.form_submit_button("✅ Cadastrar Usuário", use_container_width=True)

    if salvar_novo:
        novo_login = novo_login.strip().lower()
        if not novo_login or not nova_senha or not novo_nome:
            st.error("Preencha todos os campos.")
        elif nova_senha != conf_senha:
            st.error("As senhas não coincidem.")
        elif novo_login in usuarios_atuais:
            st.error(f"O login '{novo_login}' já existe.")
        elif len(nova_senha) < 6:
            st.error("A senha deve ter pelo menos 6 caracteres.")
        else:
            usuarios_atuais[novo_login] = {
                "nome": novo_nome.strip(),
                "senha_hash": _hash_senha(nova_senha),
                "perfil": novo_perfil,
                "ativo": True,
            }
            salvar_usuarios(usuarios_atuais)
            st.success(f"✅ Usuário **{novo_login}** cadastrado com sucesso!")
            st.rerun()

    st.markdown("---")

    # --- Alterar senha ---
    st.subheader("🔑 Alterar Senha de Usuário")
    with st.form("form_alterar_senha", clear_on_submit=True):
        logins_disponiveis = list(usuarios_atuais.keys())
        login_alterar = st.selectbox("Selecione o usuário", logins_disponiveis, key="sel_alterar")
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            nova_senha_alt = st.text_input("Nova Senha", type="password", key="nova_senha_alt")
        with col_s2:
            conf_senha_alt = st.text_input("Confirmar Nova Senha", type="password", key="conf_senha_alt")
        alterar_btn = st.form_submit_button("🔑 Alterar Senha", use_container_width=True)

    if alterar_btn:
        if not nova_senha_alt:
            st.error("Digite a nova senha.")
        elif nova_senha_alt != conf_senha_alt:
            st.error("As senhas não coincidem.")
        elif len(nova_senha_alt) < 6:
            st.error("A senha deve ter pelo menos 6 caracteres.")
        else:
            usuarios_atuais[login_alterar]["senha_hash"] = _hash_senha(nova_senha_alt)
            salvar_usuarios(usuarios_atuais)
            st.success(f"✅ Senha do usuário **{login_alterar}** alterada com sucesso!")

    st.markdown("---")

    # --- Ativar / Desativar usuário ---
    st.subheader("🔒 Ativar / Desativar Usuário")
    logins_nao_admin = [l for l in usuarios_atuais.keys() if l != "admin"]
    if logins_nao_admin:
        with st.form("form_ativar_desativar", clear_on_submit=False):
            login_toggle = st.selectbox("Selecione o usuário", logins_nao_admin, key="sel_toggle")
            status_atual = usuarios_atuais[login_toggle].get("ativo", True)
            acao_label = "🔒 Desativar" if status_atual else "🔓 Ativar"
            toggle_btn = st.form_submit_button(acao_label, use_container_width=True)

        if toggle_btn:
            usuarios_atuais[login_toggle]["ativo"] = not status_atual
            salvar_usuarios(usuarios_atuais)
            acao_str = "desativado" if status_atual else "ativado"
            st.success(f"✅ Usuário **{login_toggle}** {acao_str} com sucesso!")
            st.rerun()
    else:
        st.info("Nenhum outro usuário cadastrado além do admin.")

    st.markdown("---")

    # --- Excluir usuário ---
    st.subheader("🗑️ Excluir Usuário")
    logins_excluiveis = [l for l in usuarios_atuais.keys() if l != "admin"]
    if logins_excluiveis:
        with st.form("form_excluir", clear_on_submit=False):
            login_excluir = st.selectbox("Selecione o usuário para excluir", logins_excluiveis, key="sel_excluir")
            excluir_btn = st.form_submit_button("🗑️ Excluir Usuário", use_container_width=True)

        if excluir_btn:
            del usuarios_atuais[login_excluir]
            salvar_usuarios(usuarios_atuais)
            st.rerun()
    else:
        st.info("Nenhum outro usuário para excluir além do admin.")
