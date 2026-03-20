
import streamlit as st
import pandas as pd
from datetime import datetime, date
import requests
import json
import os
import unicodedata
import folium
from streamlit_folium import st_folium

ARQUIVO_DADOS = "dados.json"

# --- MAPEAMENTO DE ROTAS E BAIRROS ---
ROTAS_MAP = {
    "ROTA 1": ["CENTRO", "JARDIM AMERICA"],
    "ROTA 2": ["ALBERTINA", "LARANJEIRAS", "BOA VISTA", "EUGENIO SCHNEIDER"],
    "ROTA 3": ["FUNDO CANOAS", "CANOAS", "PROGRESSO", "PAMPLONA", "CANTA GALO"],
    "ROTA 4": ["BARRA DO TROMBUDO", "BARRAGEM", "BUDAG", "SUMARE"],
    "ROTA 5": ["SANTANA", "TABOAO", "BREMER", "BELA ALIANCA"],
    "ROTA 6": ["BARRA DA ITOUPAVA", "NAVEGANTES", "SANTA RITA", "VALADA ITOUPAVA", "VALADA SAO PAULO", "RAINHA"]
}

# --- DICIONÁRIO DE SIGLAS DOS BAIRROS ---
SIGLAS_MAP = {
    "CENTRO": "CT", "JARDIM AMERICA": "JA", "ALBERTINA": "AB", "LARANJEIRAS": "LA",
    "BOA VISTA": "BV", "EUGENIO SCHNEIDER": "ES", "FUNDO CANOAS": "FC", "CANOAS": "CN",
    "PROGRESSO": "PR", "PAMPLONA": "PM", "CANTA GALO": "CG", "BARRA DO TROMBUDO": "BT",
    "BARRAGEM": "BG", "BUDAG": "BD", "SUMARE": "SU", "SANTANA": "ST", "TABOAO": "TB",
    "BREMER": "BR", "BELA ALIANCA": "BA", "BARRA DA ITOUPAVA": "BI", "NAVEGANTES": "NV",
    "SANTA RITA": "SR", "VALADA ITOUPAVA": "VI", "VALADA SAO PAULO": "VS", "RAINHA": "RA"
}

# --- FUNÇÃO PARA DESCOBRIR A ROTA BASEADA NO BAIRRO ---
def extrair_rota(bairro_texto):
    if not bairro_texto: return "OUTRAS ROTAS"
    b_norm = ''.join(c for c in unicodedata.normalize('NFD', bairro_texto) if unicodedata.category(c) != 'Mn').upper().strip()
    for rota, bairros in ROTAS_MAP.items():
        if any(b in b_norm for b in bairros):
            return rota
    return "OUTRAS ROTAS"

# --- FUNÇÃO PARA GERAR O NÚMERO DA OS PADRÃO NEMA VAGALUME ---
def gerar_numero_os(bairro_texto):
    if not bairro_texto: bairro_texto = "INDEFINIDO"
    b_norm = ''.join(c for c in unicodedata.normalize('NFD', bairro_texto) if unicodedata.category(c) != 'Mn').upper().strip()
    
    rota_extenso = extrair_rota(b_norm)
    num_rota = "".join([s for s in rota_extenso if s.isdigit()])
    if not num_rota: num_rota = "0"
    
    sigla = "XX"
    for bairro_chave, sigla_valor in SIGLAS_MAP.items():
        if bairro_chave in b_norm:
            sigla = sigla_valor
            break
    if sigla == "XX" and len(b_norm) >= 2:
        sigla = b_norm[:2].upper()
        
    prefixo = f"nmv{num_rota}{sigla}".lower()
    
    contador = 0
    for os_item in st.session_state.ordens_servico:
        if os_item.get('os', '').lower().startswith(prefixo):
            contador += 1
            
    return f"{prefixo}{(contador + 1):03d}"

# --- FUNÇÕES DE BANCO DE DADOS ---
def carregar_dados():
    if os.path.exists(ARQUIVO_DADOS):
        try:
            with open(ARQUIVO_DADOS, "r", encoding="utf-8") as f:
                dados = json.load(f)
                if "usuarios" not in dados:
                    dados["usuarios"] = [{"username": "gerencia", "password": "Ameixaseca9988?", "role": "gerencia"}]
                return dados
        except:
            pass 
            
    return {
        "ordens_servico": [],
        "materiais_disponiveis": [
            "Nenhum material (Apenas ajuste/vistoria)",
            "Lâmpada 70w vapor de sódio",
            "Lâmpada 250w vapor de sódio",
            "Lâmpada 400w vapor de sódio",
            "Lâmpada 250w vapor metálico",
            "Lâmpada 400w vapor metálico",
            "Luminária led 100w",
            "Luminária led 150w",
            "Reator 70w",
            "Reator 250w",
            "Reator 400w",
            "Base de relé",
            "Relé fotoelétrico",
            "Relé fotoelétrico para grupo"
        ],
        "usuarios": [
            {"username": "gerencia", "password": "Ameixaseca9988?", "role": "gerencia"}
        ]
    }

def salvar_dados():
    dados = {
        "ordens_servico": st.session_state.ordens_servico,
        "materiais_disponiveis": st.session_state.materiais_disponiveis,
        "usuarios": st.session_state.usuarios
    }
    with open(ARQUIVO_DADOS, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Sistema Vagalume - Iluminação Pública", layout="wide")

# --- INICIALIZAÇÃO DOS DADOS E PERSISTÊNCIA DE LOGIN ---
dados_iniciais = carregar_dados()
if 'ordens_servico' not in st.session_state: st.session_state.ordens_servico = dados_iniciais["ordens_servico"]
if 'materiais_disponiveis' not in st.session_state: st.session_state.materiais_disponiveis = dados_iniciais["materiais_disponiveis"]
if 'usuarios' not in st.session_state: st.session_state.usuarios = dados_iniciais["usuarios"]
if 'form_key' not in st.session_state: st.session_state.form_key = 0

if "Nenhum material (Apenas ajuste/vistoria)" not in st.session_state.materiais_disponiveis:
    st.session_state.materiais_disponiveis.insert(0, "Nenhum material (Apenas ajuste/vistoria)")

if 'user_role' not in st.session_state:
    if 'role' in st.query_params:
        st.session_state.user_role = st.query_params['role']
        st.session_state.page = 'app'
    else:
        st.session_state.user_role = None
        st.session_state.page = 'home'

# --- FUNÇÃO DE CALLBACK PARA BUSCAR CEP ---
def action_buscar_cep():
    fk = st.session_state.form_key
    cep_digitado = st.session_state.get(f"cep_{fk}", "").replace("-", "").replace(".", "")
    if len(cep_digitado) == 8:
        try:
            resposta = requests.get(f"https://viacep.com.br/ws/{cep_digitado}/json/")
            dados = resposta.json()
            if "erro" not in dados:
                st.session_state[f"rua_{fk}"] = dados.get("logradouro", "")
                st.session_state[f"bairro_{fk}"] = dados.get("bairro", "")
                st.session_state[f"cidade_{fk}"] = dados.get("localidade", "")
                st.session_state.cep_status = "sucesso"
                return
        except: pass
    st.session_state.cep_status = "erro"

# ==========================================
# MÓDULOS (TELAS) DO SISTEMA
# ==========================================

def render_cidadao():
    fk = st.session_state.form_key
    
    if st.session_state.get("chamado_sucesso"):
        st.success(f"✅ Solicitação enviada com sucesso! O número do protocolo é: **{st.session_state.chamado_sucesso}**")
        st.session_state.chamado_sucesso = False

    st.markdown("""<h2 style="white-space: nowrap; font-size: clamp(18px, 3.5vw, 32px); margin-bottom: 10px;">Registrar Problema na Iluminação</h2>""", unsafe_allow_html=True)
    
    st.markdown("""<h3 style="white-space: nowrap; font-size: clamp(16px, 2.5vw, 24px); margin-bottom: 10px; color: #444;">1. Dados do Solicitante</h3>""", unsafe_allow_html=True)
    col_nome, col_cpf = st.columns(2)
    with col_nome: nome_cidadao = st.text_input("Nome Completo*", key=f"nome_{fk}")
    with col_cpf: cpf_cidadao = st.text_input("CPF*", key=f"cpf_{fk}")
        
    col_email, col_whats = st.columns(2)
    with col_email: email_cidadao = st.text_input("E-mail*", key=f"email_{fk}")
    with col_whats: whatsapp_cidadao = st.text_input("WhatsApp (com DDD)*", key=f"whats_{fk}")

    st.markdown("""<h3 style="white-space: nowrap; font-size: clamp(16px, 2.5vw, 24px); margin-top: 20px; margin-bottom: 10px; color: #444;">2. Endereço do Problema</h3>""", unsafe_allow_html=True)
    
    st.write("📍 **Opção A: Localize no Mapa** (Clique no local do poste para inserir um pino)")
    
    lat_inicial, lon_inicial = -27.2142, -49.6425
    m = folium.Map(location=[lat_inicial, lon_inicial], zoom_start=13)
    m.add_child(folium.ClickForMarker(popup="Local do Problema"))
    
    map_data = st_folium(m, height=350, width="100%", key=f"mapa_{fk}")
    
    lat_marcada = None
    lon_marcada = None
    if map_data and map_data.get("last_clicked"):
        lat_marcada = map_data["last_clicked"]["lat"]
        lon_marcada = map_data["last_clicked"]["lng"]
        st.success(f"📌 Pino inserido! Coordenadas capturadas: ({lat_marcada:.4f}, {lon_marcada:.4f})")

    st.write("---")
    st.write("📝 **Opção B: Preencha o Endereço**")
    
    col_cep, col_btn = st.columns([2, 1])
    with col_cep: 
        st.text_input("Digite o CEP:", key=f"cep_{fk}")
    with col_btn:
        st.write(""); st.write("")
        st.button("Buscar CEP", on_click=action_buscar_cep)

    if st.session_state.get("cep_status") == "sucesso":
        st.success("Endereço preenchido via CEP!")
        st.session_state.cep_status = None
    elif st.session_state.get("cep_status") == "erro":
        st.error("CEP inválido ou não encontrado.")
        st.session_state.cep_status = None

    logradouro = st.text_input("Rua/Avenida*:", key=f"rua_{fk}")
    col_num, col_comp, col_bairro = st.columns([1, 1, 2])
    with col_num: numero = st.text_input("Número (ou 'S/N')*:", key=f"num_{fk}")
    with col_comp: complemento = st.text_input("Complemento/Ref:", key=f"comp_{fk}")
    with col_bairro: bairro = st.text_input("Bairro*:", key=f"bairro_{fk}")
        
    cidade = st.text_input("Cidade*:", key=f"cidade_{fk}")
    
    st.markdown("""<h3 style="white-space: nowrap; font-size: clamp(16px, 2.5vw, 24px); margin-top: 20px; margin-bottom: 10px; color: #444;">3. Detalhes do Problema</h3>""", unsafe_allow_html=True)
    tipo_problema = st.selectbox("Qual o problema?", ["Lâmpada Apagada à Noite", "Lâmpada Acesa de Dia", "Poste Caído/Danificado", "Luminária Quebrada", "Luz Oscilando"], key=f"prob_{fk}")
    descricao = st.text_area("Descreva o problema com detalhes:", key=f"desc_{fk}")
    
    st.markdown("*Campos com (*) são obrigatórios.*")
    
    if st.button("Enviar Solicitação para a Prefeitura", type="primary"):
        campos_vazios = []
        if not nome_cidadao: campos_vazios.append("Nome Completo")
        if not cpf_cidadao: campos_vazios.append("CPF")
        if not email_cidadao: campos_vazios.append("E-mail")
        if not whatsapp_cidadao: campos_vazios.append("WhatsApp")
        
        if not lat_marcada:
            if not logradouro: campos_vazios.append("Rua/Avenida")
            if not numero: campos_vazios.append("Número")
            if not bairro: campos_vazios.append("Bairro")
            if not cidade: campos_vazios.append("Cidade")

        if len(campos_vazios) == 0:
            endereco_completo = f"{logradouro}, {numero} - {complemento} | Bairro: {bairro} | {cidade}"
            descricao_final = descricao
            
            if lat_marcada and lon_marcada:
                link_maps = f"https://www.google.com/maps?q={lat_marcada},{lon_marcada}"
                descricao_final += f"\n\n📍 **Localização GPS (Google Maps):**\n{link_maps}"
                
                if not bairro: bairro = "Bairro não informado via GPS"
            
            nova_os = {
                "os": gerar_numero_os(bairro),
                "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "nome_solicitante": nome_cidadao,
                "cpf_solicitante": cpf_cidadao,
                "email_solicitante": email_cidadao,
                "whatsapp_solicitante": whatsapp_cidadao,
                "endereco": endereco_completo,
                "bairro": bairro,
                "problema": tipo_problema,
                "descricao": descricao_final,
                "status": "Aguardando Despacho",
                "materiais": [],
                "obs_tecnico": "",
                "prazo": "Não definido"
            }
            st.session_state.ordens_servico.append(nova_os)
            salvar_dados()
            
            st.session_state.chamado_sucesso = nova_os['os']
            st.session_state.form_key += 1 
            st.rerun()
        else:
            st.error(f"⚠️ Atenção! Preencha os seguintes campos (ou marque o local no mapa): **{', '.join(campos_vazios)}**")

def render_gerencia():
    st.markdown("""<h2 style="white-space: nowrap; font-size: clamp(18px, 3.5vw, 32px); margin-bottom: 20px;">Gestão de Chamados, Estoque e Usuários</h2>""", unsafe_allow_html=True)
    col_chamados, col_lateral = st.columns([2, 1])
    
    with col_lateral:
        st.markdown("""<h3 style="white-space: nowrap; font-size: clamp(16px, 2.5vw, 24px); margin-bottom: 10px; color: #444;">⚙️ Menu da Gerência</h3>""", unsafe_allow_html=True)
        
        with st.expander("📂 Importar Planilha (Por Abas)", expanded=False):
            st.write("Suba sua planilha onde cada ABA é um Bairro.")
            ano_sel = st.number_input("Ano das Pendências/Concluídas:", value=datetime.now().year, step=1)
            arquivo_excel = st.file_uploader("Selecione o arquivo Excel (.xlsx)", type=["xlsx"])
            
            if arquivo_excel is not None:
                if st.button("🚀 Processar e Gerar Chamados", type="primary"):
                    with st.spinner('Lendo abas e processando histórico (Pendentes e Concluídas)...'):
                        try:
                            COL_DATA = 7      # Coluna H
                            COL_PROBLEMA = 1  # Coluna B
                            COL_STATUS = 3    # Coluna D
                            
                            xls = pd.read_excel(arquivo_excel, sheet_name=None, header=None)
                            abas_disponiveis = {nome.strip().upper(): nome for nome in xls.keys()}
                            
                            chamados_importados = 0
                            chamados_concluidos_importados = 0

                            for route, neighborhoods in ROTAS_MAP.items():
                                for neighborhood in neighborhoods:
                                    nome_upper = neighborhood.upper()
                                    if nome_upper in abas_disponiveis:
                                        df = xls[abas_disponiveis[nome_upper]].copy()
                                        if df.shape[1] <= COL_DATA: continue

                                        df[COL_DATA] = pd.to_datetime(df[COL_DATA], errors='coerce')
                                        mask_ano = (df[COL_DATA].dt.year == ano_sel)
                                        linhas_do_ano = df[mask_ano]
                                        
                                        for _, row in linhas_do_ano.iterrows():
                                            status_excel = str(row[COL_STATUS]).strip().upper()
                                            
                                            status_interno = ""
                                            mats_iniciais = []
                                            
                                            if status_excel in ['NÃO REALIZADO', 'NÃO EXECUTADO', 'NAO REALIZADO', 'NAO EXECUTADO', 'ABERTO', 'PENDENTE']:
                                                status_interno = "Aguardando Despacho"
                                            elif status_excel in ['REALIZADO', 'EXECUTADO', 'CONCLUIDO', 'CONCLUÍDO', 'OK', 'FINALIZADO', 'FINALIZADA']:
                                                status_interno = "Concluída"
                                                mats_iniciais = ["Lançado via histórico da planilha"]
                                                chamados_concluidos_importados += 1
                                            else:
                                                continue 
                                                
                                            prob_val = str(row[COL_PROBLEMA]).title() if pd.notna(row[COL_PROBLEMA]) else "Manutenção Importada"
                                            
                                            nova_os = {
                                                "os": gerar_numero_os(neighborhood),
                                                "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                                                "nome_solicitante": "SISTEMA",
                                                "cpf_solicitante": "SISTEMA",
                                                "email_solicitante": "SISTEMA",
                                                "whatsapp_solicitante": "SISTEMA",
                                                "endereco": f"Endereço não detalhado na planilha | Bairro: {neighborhood}",
                                                "bairro": neighborhood,
                                                "problema": prob_val,
                                                "descricao": f"Chamado importado automaticamente da planilha (Aba: {neighborhood}). Status na planilha: {status_excel}.",
                                                "status": status_interno,
                                                "materiais": mats_iniciais,
                                                "obs_tecnico": "Importado do Excel.",
                                                "prazo": "Não definido"
                                            }
                                            st.session_state.ordens_servico.append(nova_os)
                                            chamados_importados += 1
                                            
                            if chamados_importados > 0:
                                salvar_dados()
                                st.success(f"✅ {chamados_importados} chamados importados no total! ({chamados_concluidos_importados} já contabilizados na aba Prefeitura como concluídos).")
                                st.rerun()
                            else:
                                st.warning(f"Nenhum dado válido encontrado para o ano de {ano_sel}.")

                        except Exception as e:
                            st.error(f"Erro ao ler a planilha: {e}")

        with st.expander("👥 Gerenciar Usuários", expanded=False):
            st.write("Usuários Atuais:")
            df_users = pd.DataFrame(st.session_state.usuarios)
            df_users['password'] = '******'
            st.dataframe(df_users, hide_index=True)
            st.write("---")
            new_user = st.text_input("Usuário (Login):")
            new_pass = st.text_input("Senha:", type="password")
            new_role = st.selectbox("Nível de Acesso:", ["tecnico", "prefeitura", "gerencia"])
            if st.button("Cadastrar Usuário"):
                if new_user and new_pass:
                    if any(u['username'] == new_user for u in st.session_state.usuarios):
                        st.error("Usuário já existe!")
                    else:
                        st.session_state.usuarios.append({"username": new_user, "password": new_pass, "role": new_role})
                        salvar_dados()
                        st.success("Usuário criado!")
                        st.rerun()

        with st.expander("📦 Gerenciar Materiais", expanded=False):
            st.write("Estoque atual:")
            st.dataframe(pd.DataFrame(st.session_state.materiais_disponiveis, columns=["Materiais"]), hide_index=True)
            novo_material = st.text_input("Novo material:")
            if st.button("Adicionar Material"):
                if novo_material and novo_material not in st.session_state.materiais_disponiveis:
                    st.session_state.materiais_disponiveis.append(novo_material)
                    salvar_dados()
                    st.success("Adicionado!")
                    st.rerun()

        with st.expander("📋 Chamados em Andamento", expanded=False):
            os_andamento = [os for os in st.session_state.ordens_servico if os['status'] in ["Enviada ao Técnico", "Em Andamento"]]
            for os_item in os_andamento:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**OS {os_item['os']}** - {os_item['problema']}")
                    st.caption(f"Prazo: {os_item.get('prazo', 'N/D')} | Status: {os_item['status']}")
                with col2:
                    if st.button(
