import streamlit as st
import pandas as pd
import uuid
from datetime import datetime, date
import requests
import json
import os
import base64

ARQUIVO_DADOS = "dados.json"

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
        img_html = f'<img src="data:image/png;base64,{encoded_string}" style="max-width: 100%; max-height: 120px; object-fit: contain; display: block; margin: 0 auto 10px auto;">'
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
            for os_item in chamados_novos:
                col_expander, col_botao = st.columns([3, 1])
                with col_expander:
                    with st.expander(f"OS: {os_item['os']} - {os_item['problema']}"):
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
        for os_item in os_tecnico:
            with st.expander(f"OS: {os_item['os']} ({os_item['status']}) - {os_item['problema']}"):
                st.write(f"**Data:** {os_item['data']}")
                st.write(f"**Endereço:** {os_item['endereco']}")
                st.write(f"**Descrição:** {os_item['descricao']}")
                st.error(f"⚠️ **PRAZO:** {os_item.get('prazo', 'Não definido')}")
                
                st.write("---")
                novo_status = st.selectbox("Status:", ["Em Andamento", "Concluída"], index=0 if os_item['status']=="Enviada ao Técnico" else 1, key=f"status_{os_item['os']}")
                
                materiais_selecionados = st.multiselect("Materiais Utilizados:", st.session_state.materiais_disponiveis, key=f"mat_{os_item['os']}")
                qtds = {}
                for mat in materiais_selecionados:
                    qtds[mat] = st.number_input(f"Qtd '{mat}'", min_value=1, value=1, step=1, key=f"q_{os_item['os']}_{mat}")
                
                obs = st.text_area("Observações / Descrição da Atividade:", key=f"obs_{os_item['os']}")
                
                if st.button("Salvar Apontamento e Concluir", key=f"salvar_{os_item['os']}", type="primary"):
                    os_item['status'] = novo_status
                    os_item['materiais'] = [f"{qtd}x {m}" for m, qtd in qtds.items()]
                    if obs: os_item['obs_tecnico'] = obs
                    salvar_dados()
                    st.success("Salvo com sucesso!")
                    st.rerun()

def render_prefeitura():
    st.markdown("""<h2 style="white-space: nowrap; font-size: clamp(18px, 3.5vw, 32px); margin-bottom: 20px;">Painel de Gestão e Monitoramento</h2>""", unsafe_allow_html=True)
    hoje_dt = datetime.strptime(date.today().strftime("%d/%m/%Y"), "%d/%m/%Y")
    
    os_atrasadas = [os for os in st.session_state.ordens_servico if os['status'] not in ["Concluída", "Aguardando Despacho"] and os.get('prazo') and os.get('prazo') != "Não definido" and hoje_dt > datetime.strptime(os.get('prazo'), "%d/%m/%Y")]
    
    if os_atrasadas: st.error(f"⚠️ ATENÇÃO: {len(os_atrasadas)} OS com PRAZO VENCIDO!")
    else: st.success("✅ Todos os chamados técnicos estão dentro do prazo.")
    
    st.write("---")
    if st.session_state.ordens_servico:
        df_os = pd.DataFrame(st.session_state.ordens_servico)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total de Chamados", len(df_os))
        c2.metric("Aguardando Gerência", len(df_os[df_os['status'] == 'Aguardando Despacho']))
        c3.metric("Com a Equipe", len(df_os[df_os['status'].isin(['Enviada ao Técnico', 'Em Andamento'])]))
        c4.metric("Serviços Concluídos", len(df_os[df_os['status'] == 'Concluída']))
        
        st.markdown("""<h3 style="white-space: nowrap; font-size: clamp(16px, 2.5vw, 24px); margin-top: 20px; margin-bottom: 10px; color: #444;">Histórico Completo</h3>""", unsafe_allow_html=True)
        st.dataframe(df_os[['os', 'data', 'prazo', 'endereco', 'problema', 'status']], use_container_width=True)

# ==========================================
# GESTOR DE TELAS (ROTEAMENTO)
# ==========================================

if st.session_state.page == 'app':
    
    # 1. NAVBAR SUPERIOR
    col_nav_texto, col_nav_btn = st.columns([8, 2])
    with col_nav_texto:
        if st.session_state.user_role == 'cidadao':
            st.markdown("<div style='padding-top: 10px; color: #666;'>👤 <b>Modo:</b> Atendimento ao Cidadão</div>", unsafe_allow_html=True)
    with col_nav_btn:
        if st.button("Sair / Voltar", type="secondary", use_container_width=True):
            st.query_params.clear() 
            st.session_state.page = 'home'
            st.session_state.user_role = None
            st.rerun()
            
    st.divider()

    # 2. LOGO E TÍTULO PRINCIPAL
    st.markdown(
        f"""
        <div style="text-align: center; margin-bottom: 15px; margin-top: -30px;">
            {get_logo_html()}
            <h1 style="white-space: nowrap; font-size: clamp(22px, 4vw, 50px); margin-bottom: 0px;">
                💡 Sistema Vagalume
            </h1>
            <h4 style="white-space: nowrap; font-size: clamp(12px, 2vw, 20px); font-style: italic; font-weight: normal; margin-top: 0px; color: #555;">
                Sistema de gestão de iluminação pública
            </h4>
        </div>
        """, 
        unsafe_allow_html=True
    )

    # 3. BARRA DE NAVEGAÇÃO DE PÁGINAS (ABAS)
    if st.session_state.user_role == 'gerencia':
        aba_1, aba_2, aba_3, aba_4 = st.tabs(["📱 Cidadão", "🗂️ Gerência", "🛠️ Técnico", "📊 Prefeitura"])
        with aba_1: render_cidadao()
        with aba_2: render_gerencia()
        with aba_3: render_tecnico()
        with aba_4: render_prefeitura()
    elif st.session_state.user_role == 'cidadao':
        render_cidadao()
    elif st.session_state.user_role == 'tecnico':
        render_tecnico()
    elif st.session_state.user_role == 'prefeitura':
        render_prefeitura()

elif st.session_state.page == 'home':
    st.markdown(
        f"""
        <div style="text-align: center; padding-top: 5vh; padding-bottom: 5vh;">
            {get_logo_html() if get_logo_html() else '<img src="https://cdn-icons-png.flaticon.com/512/427/427242.png" style="width: 100%; max-width: 120px; margin: 0 auto; display: block; margin-bottom: 20px;">'}
            <h1 style="font-size: clamp(28px, 5vw, 60px); margin: 0;">Sistema Vagalume</h1>
            <p style="font-size: clamp(14px, 2vw, 22px); color: #666; font-style: italic; margin-top: 5px;">Sistema de gestão de iluminação pública</p>
        </div>
        """, 
        unsafe_allow_html=True
    )
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚨 Cadastrar Problema (Cidadão)", type="primary", use_container_width=True):
            st.session_state.page = 'app'
            st.session_state.user_role = 'cidadao'
            st.rerun()
        st.write("")
        if st.button("🔒 Acesso Restrito (Login)", use_container_width=True):
            st.session_state.page = 'login'
            st.rerun()

elif st.session_state.page == 'login':
    st.markdown("""<div style="text-align: center; margin-bottom: 30px;"><h2 style="font-size: clamp(24px, 4vw, 40px);">Acesso Restrito</h2></div>""", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("form_login"):
            usuario = st.text_input("Usuário")
            senha = st.text_input("Senha", type="password")
            btn_login = st.form_submit_button("Entrar", use_container_width=True)
            
            if btn_login:
                usuario_valido = None
                for u in st.session_state.usuarios:
                    if u['username'] == usuario and u['password'] == senha:
                        usuario_valido = u
                        break
                if usuario_valido:
                    st.query_params['role'] = usuario_valido['role'] 
                    st.session_state.page = 'app'
                    st.session_state.user_role = usuario_valido['role']
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")
                    
        if st.button("Voltar ao Início", use_container_width=True):
            st.session_state.page = 'home'
            st.rerun()
