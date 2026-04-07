import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime
import json
import os
import glob
from pypdf import PdfReader
from fpdf import FPDF

# Configuração da página
st.set_page_config(page_title="Stok Holmes", layout="wide", page_icon="🕵️‍♂️")

# --- DIRETÓRIOS ---
PASTA_DEVOLUCOES = "historico_devolucoes"
PASTA_PEDIDOS = "historico_pedidos"
for pasta in [PASTA_DEVOLUCOES, PASTA_PEDIDOS]:
    if not os.path.exists(pasta):
        os.makedirs(pasta)

# --- CARREGAMENTO DE DADOS ---
@st.cache_data
def carregar_dados_estoque():
    try:
        df = pd.read_excel("estoque.xlsx")
        df.columns = [str(c).strip() for c in df.columns]
        return df.sort_values(by='Descrição', ascending=True).astype(str)
    except:
        return pd.DataFrame(columns=['Código', 'Descrição', 'Localização'])

@st.cache_data
def carregar_dados_clientes():
    try:
        df = pd.read_excel("CLIENTE.xlsx")
        df.columns = [str(c).strip() for c in df.columns]
        return df.sort_values(by='Nome do Cliente', ascending=True).astype(str)
    except:
        return pd.DataFrame(columns=['código', 'Nome do Cliente', 'Cidade'])

df_estoque = carregar_dados_estoque()
df_clientes = carregar_dados_clientes()

# --- FUNÇÕES DE PDF ---
def extrair_dados_pdf(arquivo_pdf):
    texto = ""
    dados = {
        "os": "", 
        "comprador": "", 
        "depto": "", 
        "cliente_nome": "", 
        "cliente_cod": "",
        "itens": []
    }
    
    try:
        reader = PdfReader(arquivo_pdf)
        for page in reader.pages:
            content = page.extract_text()
            if content:
                texto += content + "\n"
        
        linhas = texto.split('\n')
        
        for linha in linhas:
            # --- 1. CAPTURA DE CABEÇALHO ---
            if "Orçamento:" in linha:
                partes_os = linha.split("Orçamento:")
                if len(partes_os) > 1:
                    dados['os'] = partes_os[1].strip().split()[0] [cite: 2]
            
            if "Cliente:" in linha:
                partes_cli = linha.split("Cliente:")
                if len(partes_cli) > 1:
                    info = partes_cli[1].strip().split(maxsplit=1)
                    if len(info) >= 1: dados['cliente_cod'] = info[0] [cite: 8]
                    if len(info) >= 2: dados['cliente_nome'] = info[1] [cite: 8]
            
            if "136-LEONARDO" in linha:
                dados['comprador'] = "LEONARDO" [cite: 13]
            
            if "3-INSTALAÇÕES ELÉTRICAS" in linha:
                dados['depto'] = "INSTALAÇÕES ELÉTRICAS" [cite: 16]

            # --- 2. CAPTURA DE ITENS (ESTILO CSV) ---
            # Limpa aspas e espaços
            linha_limpa = linha.replace('"', '').strip()
            
            if "," in linha_limpa:
                colunas = [c.strip() for c in linha_limpa.split(',')]
                
                # Validação: A linha deve ter pelo menos 6 colunas e começar com a sequência (ex: 01)
                if len(colunas) >= 6 and colunas[0].isdigit() and len(colunas[0]) == 2:
                    try:
                        dados['itens'].append({
                            "Código": colunas[2],       # Código do item (ex: 460131) 
                            "Descrição": colunas[3],    # Descrição do produto 
                            "Quantidade": colunas[5]    # Quantidade (ex: 6,00) 
                        })
                    except IndexError:
                        continue # Pula linhas que não encaixam no formato

        return dados
    except Exception as e:
        st.error(f"Erro ao processar PDF: {e}")
        return dados
def gerar_pdf_pedido(dados):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="PEDIDO DE MATERIAL - STOK HOLMES", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Data: {dados['data_abertura']}", ln=True)
    pdf.cell(200, 10, txt=f"OS: {dados['os']} | Comprador: {dados['comprador']}", ln=True)
    pdf.cell(200, 10, txt=f"Cliente: {dados['cliente_nome']} ({dados['cliente_cod']})", ln=True)
    pdf.cell(200, 10, txt=f"Departamento: {dados['depto']} | Responsável: {dados['responsavel']}", ln=True)
    pdf.ln(5)
    pdf.cell(200, 10, txt="ITENS:", ln=True)
    for item in dados['itens']:
        pdf.cell(200, 10, txt=f"- {item['Quantidade']}x {item['Descrição']} (Cod: {item['Código']})", ln=True)
    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- ESTADO DA SESSÃO ---
if 'pedido_editando' not in st.session_state: st.session_state.pedido_editando = None
if 'itens_pedido' not in st.session_state: st.session_state.itens_pedido = []

# --- MENU ---
pagina = st.sidebar.radio("Navegar:", ["Início", "Finder", "Devolução", "Pedidos", "Histórico Pedidos"])

# --- PÁGINA PEDIDOS ---
if pagina == "Pedidos":
    st.title("📝 Gerenciar Pedido")
    
    # Upload de PDF para auto-preenchimento
    arquivo_upload = st.file_uploader("Importar dados de um PDF?", type="pdf")
    dados_extraidos = extrair_dados_pdf(arquivo_upload) if arquivo_upload else {}

    with st.form("form_pedido"):
        col1, col2, col3 = st.columns(3)
        os_num = col1.text_input("Nº Ordem de Serviço", value=dados_extraidos.get('os', ""))
        comprador = col2.text_input("Comprador", value=dados_extraidos.get('comprador', ""))
        data_abertura = col3.text_input("Data de Abertura", value=datetime.now().strftime("%d/%m/%Y"), disabled=True)
        
        col4, col5 = st.columns(2)
        depto = col4.text_input("Departamento", value=dados_extraidos.get('depto', ""))
        responsavel = col5.text_input("Responsável")

        # Busca de Cliente
        busca_cli = st.text_input("Buscar Cliente (Nome ou Código)")
        cliente_final = None
        if busca_cli:
            res_cli = df_clientes[df_clientes['Nome do Cliente'].str.contains(busca_cli, case=False) | df_clientes['código'].str.contains(busca_cli, case=False)]
            if not res_cli.empty:
                sel_cli = st.selectbox("Selecione o Cliente", res_cli['Nome do Cliente'].tolist())
                cliente_final = res_cli[res_cli['Nome do Cliente'] == sel_cli].iloc[0]

        btn_pre_salvar = st.form_submit_button("Confirmar Cabeçalho")

    st.divider()
    
    # Adição de Itens
    col_it, col_list = st.columns([1, 1])
    with col_it:
        st.subheader("Adicionar Itens ao Pedido")
        busca_it = st.text_input("Buscar Item")
        if busca_it:
            res_it = df_estoque[df_estoque['Descrição'].str.contains(busca_it, case=False)]
            if not res_it.empty:
                item_sel = st.selectbox("Item:", res_it['Descrição'].tolist())
                qtd = st.number_input("Quantidade", min_value=1, value=1)
                if st.button("➕ Adicionar Item"):
                    linha = res_it[res_it['Descrição'] == item_sel].iloc[0]
                    st.session_state.itens_pedido.append({
                        "Código": linha['Código'], "Descrição": item_sel, "Quantidade": qtd
                    })
    
    with col_list:
        st.subheader("Itens na Lista")
        df_itens = pd.DataFrame(st.session_state.itens_pedido)
        st.table(df_itens)
        if st.button("🗑️ Limpar Itens"): 
            st.session_state.itens_pedido = []
            st.rerun()

    if st.button("💾 FINALIZAR E GERAR PDF", use_container_width=True):
        if not cliente_final is None and st.session_state.itens_pedido:
            id_pedido = os_num if os_num else datetime.now().strftime("%H%M%S")
            dados_finais = {
                "os": os_num, "comprador": comprador, "data_abertura": data_abertura,
                "depto": depto, "responsavel": responsavel,
                "cliente_nome": cliente_final['Nome do Cliente'], "cliente_cod": cliente_final['código'],
                "itens": st.session_state.itens_pedido
            }
            # Salva JSON
            with open(os.path.join(PASTA_PEDIDOS, f"ped_{id_pedido}.json"), "w") as f:
                json.dump(dados_finais, f)
            
            # Gera PDF
            pdf_out = gerar_pdf_pedido(dados_finais)
            st.download_button("📥 Baixar PDF do Pedido", pdf_out, f"Pedido_{id_pedido}.pdf")
            st.success("Pedido Salvo!")
        else:
            st.error("Selecione um cliente e adicione itens.")

# --- HISTÓRICO DE PEDIDOS (EDITAR / EXCLUIR) ---
elif pagina == "Histórico Pedidos":
    st.title("📂 Gestão de Pedidos")
    arquivos = glob.glob(os.path.join(PASTA_PEDIDOS, "*.json"))
    
    for arq in arquivos:
        with open(arq, "r") as f:
            d = json.load(f)
            col1, col2, col3 = st.columns([3, 1, 1])
            col1.write(f"OS: {d['os']} | Cliente: {d['cliente_nome']}")
            
            if col2.button("✏️ Editar", key="edit"+arq):
                st.session_state.itens_pedido = d['itens']
                # Aqui você redirecionaria para a aba Pedidos para terminar
                st.info("Itens carregados na aba Pedidos para edição.")
            
            if col3.button("❌ Excluir", key="del"+arq):
                os.remove(arq)
                st.rerun()