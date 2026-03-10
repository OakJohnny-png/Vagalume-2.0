import streamlit as st
import pandas as pd
import uuid
from datetime import datetime, date
import requests
import json
import os
import base64
import unicodedata

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

# --- FUNÇÃO PARA DESCOBRIR A ROTA BASEADA NO BAIRRO ---
def extrair_rota(bairro_texto):
    if not bairro_texto: return "OUTRAS ROTAS"
    b_norm = ''.join(c for c in unicodedata.normalize('NFD', bairro_texto) if unicodedata.category(c) != 'Mn').upper().strip()
    for rota, bairros in ROTAS_MAP.items():
        if any(b in b_norm for b in bairros):
            return rota
    return "OUTRAS ROTAS"

# --- FUNÇÕES DE BANCO DE DADOS ---
def carregar_dados():
    if os.path.exists(ARQUIVO_DADOS):
        with open(ARQUIVO_DADOS, "r", encoding="utf-8") as f:
            dados = json.load(f)
            if "usuarios" not in dados:
                dados["usuarios"] = [{"username": "gerencia", "password": "Ameixaseca9988?", "role": "gerencia"}]
            return dados
    else:
        return {
            "ordens_servico": [],
            "materiais_disponiveis": [
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

# --- FUNÇÃO PARA RENDERIZAR A LOGO ADAPTATIVA ---
def get_logo_html():
    img_html = ""
    if os.path.exists("logo.png"):
        with open("logo.png", "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        img_html = f'<img src="data:image/png;base64,{encoded_string}" style="width: 100%; max-width: 450px; height: auto; display: block; margin: 0 auto 15px auto;">'
    return img_html

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Sistema Vagalume - Iluminação Pública", layout="wide")

# --- INICIALIZAÇÃO DOS DADOS E PERSISTÊNCIA DE LOGIN ---
dados_iniciais = carregar_dados()
if 'ordens_servico' not in st.session_state: st.session_state.ordens_servico = dados_iniciais["ordens_servico"]
if 'materiais_disponiveis' not in st.session_state: st.session_state.materiais_disponiveis = dados_iniciais["materiais_disponiveis"]
if 'usuarios' not in st.session_state: st.session_state.usuarios = dados_iniciais["usuarios"]
if 'form_key' not in st.session_state: st.session_state.form_key = 0

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
    col_cep, col_btn = st.columns([2, 1])
    with col_cep: 
        st.text_input("Digite o CEP:", key=f"cep_{fk}")
    with col_btn:
        st.write(""); st.write("")
        st.button("Buscar CEP", on_click=action_buscar_cep)

    if st.session_state.get("cep_status") == "sucesso":
        st.success("Endereço preenchido!")
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
        if not logradouro: campos_vazios.append("Rua/Avenida")
        if not numero: campos_vazios.append("Número")
        if not bairro: campos_vazios.append("Bairro")
        if not cidade: campos_vazios.append("Cidade")

        if len(campos_vazios) == 0:
            endereco_completo = f"{logradouro}, {numero} - {complemento} | Bairro: {bairro} | {cidade}"
            nova_os = {
                "os": str(uuid.uuid4())[:8].upper(),
                "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "nome_solicitante": nome_cidadao,
                "cpf_solicitante": cpf_cidadao,
                "email_solicitante": email_cidadao,
                "whatsapp_solicitante": whatsapp_cidadao,
                "endereco": endereco_completo,
                "bairro": bairro,
                "problema": tipo_problema,
                "descricao": descricao,
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
            st.error(f"⚠️ Atenção! Preencha os seguintes campos: **{', '.join(campos_vazios)}**")

def render_gerencia():
    st.markdown("""<h2 style="white-space: nowrap; font-size: clamp(18px, 3.5vw, 32px); margin-bottom: 20px;">Gestão de Chamados, Estoque e Usuários</h2>""", unsafe_allow_html=True)
    col_chamados, col_lateral = st.columns([2, 1])
    
    with col_lateral:
        st.markdown("""<h3 style="white-space: nowrap; font-size: clamp(16px, 2.5vw, 24px); margin-bottom: 10px; color: #444;">⚙️ Menu da Gerência</h3>""", unsafe_allow_html=True)
        
        with st.expander("📂 Importar Planilha (Lote)", expanded=False):
            st.write("Suba uma planilha Excel para criar chamados automaticamente.")
            arquivo_excel = st.file_uploader("Selecione o arquivo Excel (.xlsx)", type=["xlsx", "xls"])
            if arquivo_excel is not None:
                if st.button("Processar e Gerar Chamados", type="primary"):
                    try:
                        df_import = pd.read_excel(arquivo_excel)
                        
                        # A MÁGICA ESTÁ AQUI: Convertendo colunas para texto para evitar o erro do "float"
                        df_import.columns = df_import.columns.astype(str).str.upper().str.strip()
                        colunas_upper = df_import.columns.tolist()
                        
                        col_bairro = next((c for c in colunas_upper if 'BAIRRO' in c), None)
                        col_end = next((c for c in colunas_upper if 'ENDERE' in c or 'RUA' in c or 'LOGRAD' in c), None)
                        col_prob = next((c for c in colunas_upper if 'PROBLEM' in c or 'TIPO' in c or 'SERVI' in c), None)
                        col_desc = next((c for c in colunas_upper if 'DESCRI' in c or 'OBS' in c or 'DETALHE' in c), None)
                        col_status = next((c for c in colunas_upper if 'STATUS' in c or 'SITUA' in c), None)
                        
                        if col_status:
                            df_import = df_import[df_import[col_status].astype(str).str.contains("ABERTO|PENDENTE", case=False, na=False)]
                            
                        chamados_criados = 0
                        for _, row in df_import.iterrows():
                            bairro_val = str(row[col_bairro]).title() if col_bairro and pd.notna(row[col_bairro]) else "Não informado"
                            end_val = str(row[col_end]) if col_end and pd.notna(row[col_end]) else "Endereço não informado"
                            prob_val = str(row[col_prob]).title() if col_prob and pd.notna(row[col_prob]) else "Manutenção Importada"
                            desc_val = str(row[col_desc]) if col_desc and pd.notna(row[col_desc]) else "Gerado via importação de planilha."
                            
                            if bairro_val.lower() == 'nan': bairro_val = "Não informado"
                            if end_val.lower() == 'nan': end_val = "Endereço não informado"
                            
                            nova_os = {
                                "os": str(uuid.uuid4())[:8].upper(),
                                "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                                "nome_solicitante": "SISTEMA",
                                "cpf_solicitante": "SISTEMA",
                                "email_solicitante": "SISTEMA",
                                "whatsapp_solicitante": "SISTEMA",
                                "endereco": f"{end_val} | Bairro: {bairro_val}",
                                "bairro": bairro_val,
                                "problema": prob_val,
                                "descricao": desc_val,
                                "status": "Aguardando Despacho",
                                "materiais": [],
                                "obs_tecnico": "",
                                "prazo": "Não definido"
                            }
                            st.session_state.ordens_servico.append(nova_os)
                            chamados_criados += 1
                            
                        salvar_dados()
                        st.success(f"✅ {chamados_criados} chamados importados com sucesso!")
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
                st.markdown(f"**OS {os_item['os']}** - {os_item['problema']}")
                st.caption(f"Prazo: {os_item.get('prazo', 'N/D')} | Status: {os_item['status']}")
                st.write("---")

        with st.expander("✅ Chamados Concluídos", expanded=False):
            os_concluidas = [os for os in st.session_state.ordens_servico if os['status'] == "Concluída"]
            if not os_concluidas:
                st.write("Nenhum chamado concluído ainda.")
            for os_item in os_concluidas:
                st.markdown(f"**OS {os_item['os']}** - {os_item['problema']}")
                st.write(f"👤 **Solicitante:** {os_item.get('nome_solicitante', 'N/D')}")
                st.write(f"📍 **Endereço:** {os_item['endereco']}")
                st.write(f"🛠 **Materiais Usados:** {', '.join(os_item.get('materiais', ['Nenhum']))}")
                st.write(f"📝 **Nota do Técnico:** {os_item.get('obs_tecnico', 'Sem observações')}")
                st.write("---")

    with col_chamados:
        st.markdown("""<h3 style="white-space: nowrap; font-size: clamp(16px, 2.5vw, 24px); margin-bottom: 10px; color: #444;">🚨 Aguardando Despacho</h3>""", unsafe_allow_html=True)
        chamados_novos = [os for os in st.session_state.ordens_servico if os['status'] == "Aguardando Despacho"]
        
        if not chamados_novos: 
            st.info("Nenhum chamado novo.")
        else:
            chamados_agrupados = {}
            for os_item in chamados_novos:
                bairro_os = os_item.get('bairro', '')
                if not bairro_os and '| Bairro: ' in os_item['endereco']: 
                    bairro_os = os_item['endereco'].split('| Bairro: ')[1].split(' |')[0]
                
                rota_os = extrair_rota(bairro_os)
                if rota_os not in chamados_agrupados:
                    chamados_agrupados[rota_os] = []
                chamados_agrupados[rota_os].append(os_item)
            
            rotas_ordenadas = sorted(chamados_agrupados.keys())
            if "OUTRAS ROTAS" in rotas_ordenadas:
                rotas_ordenadas.remove("OUTRAS ROTAS")
                rotas_ordenadas.append("OUTRAS ROTAS")

            for rota in rotas_ordenadas:
                st.markdown(f"<h4 style='color: #2e7bcf; margin-top: 20px; border-bottom: 2px solid #2e7bcf; padding-bottom: 5px;'>📍 {rota}</h4>", unsafe_allow_html=True)
                
                for os_item in chamados_agrupados[rota]:
                    col_expander, col_botao = st.columns([3, 1])
                    
                    bairro_display = os_item.get('bairro', 'Bairro N/D')
                    if not bairro_display and '| Bairro: ' in os_item['endereco']:
                         bairro_display = os_item['endereco'].split('| Bairro: ')[1].split(' |')[0]
                         
                    with col_expander:
                        with st.expander(f"OS: {os_item['os']} - {bairro_display} ({os_item['problema']})"):
                            st.write(f"📅 **Aberto em:** {os_item['data']}")
                            st.write(f"👤 **Contato:** {os_item.get('whatsapp_solicitante', 'N/D')} ({os_item.get('nome_solicitante', 'N/D')})")
                            st.write(f"📍 **Endereço:** {os_item['endereco']}")
                            st.write(f"📝 **Descrição:** {os_item['descricao']}")
                            prazo_selecionado = st.date_input("Definir Prazo Limite:", min_value=date.today(), key=f"prazo_{os_item['os']}")
                    
                    with col_botao:
                        if st.button("Despachar", key=f"btn_{os_item['os']}", type="primary", use_container_width=True):
                            os_item['status'] = "Enviada ao Técnico"
                            os_item['prazo'] = st.session_state[f"prazo_{os_item['os']}"].strftime("%d/%m/%Y") if f"prazo_{os_item['os']}" in st.session_state else date.today().strftime("%d/%m/%Y")
                            salvar_dados()
                            st.rerun()

def render_tecnico():
    st.markdown("""<h2 style="white-space: nowrap; font-size: clamp(18px, 3.5vw, 32px); margin-bottom: 20px;">Ordens de Serviço do Técnico</h2>""", unsafe_allow_html=True)
    os_tecnico = [os for os in st.session_state.ordens_servico if os['status'] in ["Enviada ao Técnico", "Em Andamento"]]
    os_tecnico.sort(key=lambda x: datetime.strptime(x['data'], "%d/%m/%Y %H:%M"))
    
    if not os_tecnico: st.info("Nenhuma ordem de serviço pendente!")
    else:
        fo
