import streamlit as st
import pandas as pd
import uuid
from datetime import datetime, date
import requests
import json
import os

ARQUIVO_DADOS = "dados.json"

# --- FUNÇÕES DE BANCO DE DADOS (SALVAR EM ARQUIVO LOCAL) ---
def carregar_dados():
    if os.path.exists(ARQUIVO_DADOS):
        with open(ARQUIVO_DADOS, "r", encoding="utf-8") as f:
            return json.load(f)
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
            ]
        }

def salvar_dados():
    dados = {
        "ordens_servico": st.session_state.ordens_servico,
        "materiais_disponiveis": st.session_state.materiais_disponiveis
    }
    with open(ARQUIVO_DADOS, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Gestão de Iluminação Pública", layout="wide")

# --- INICIALIZAÇÃO DOS DADOS REAIS ---
if 'dados_carregados' not in st.session_state:
    dados_iniciais = carregar_dados()
    st.session_state.ordens_servico = dados_iniciais["ordens_servico"]
    st.session_state.materiais_disponiveis = dados_iniciais["materiais_disponiveis"]
    st.session_state.dados_carregados = True

# Variáveis temporárias para a busca de CEP
for campo in ['end_logradouro', 'end_bairro', 'end_cidade', 'end_uf']:
    if campo not in st.session_state: 
        st.session_state[campo] = ""

# --- FUNÇÃO PARA BUSCAR CEP ---
def buscar_cep(cep):
    cep = cep.replace("-", "").replace(".", "")
    if len(cep) == 8:
        try:
            resposta = requests.get(f"https://viacep.com.br/ws/{cep}/json/")
            dados = resposta.json()
            if "erro" not in dados:
                st.session_state.end_logradouro = dados.get("logradouro", "")
                st.session_state.end_bairro = dados.get("bairro", "")
                st.session_state.end_cidade = dados.get("localidade", "")
                st.session_state.end_uf = dados.get("uf", "")
                return True
        except:
            pass
    return False

# --- TÍTULO DO APP ---
st.markdown(
    """
    <div>
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
st.write("") # Dá um pequeno espaço antes das abas



# --- CRIAÇÃO DAS ABAS ---
aba_cidadao, aba_gerencia, aba_tecnico, aba_prefeitura = st.tabs([
    "📱 Cidadão (Solicitar)", 
    "🗂️ Gerência (Triagem)", 
    "🛠️ Técnico (Manutenção)", 
    "📊 Prefeitura (Dashboard)"
])

# ==========================================
# ABA 1: VISÃO DO CIDADÃO (SOLICITAÇÕES)
# ==========================================
with aba_cidadao:
    st.header("Registrar Problema na Iluminação")
    
    # 1. Dados do Solicitante (Novidade)
    st.subheader("1. Dados do Solicitante")
    col_nome, col_cpf = st.columns(2)
    with col_nome:
        nome_cidadao = st.text_input("Nome Completo*")
    with col_cpf:
        cpf_cidadao = st.text_input("CPF*")
        
    col_email, col_whats = st.columns(2)
    with col_email:
        email_cidadao = st.text_input("E-mail*")
    with col_whats:
        whatsapp_cidadao = st.text_input("WhatsApp (com DDD)*")

    # 2. Endereço
    st.subheader("2. Endereço do Problema")
    col_cep, col_btn = st.columns([2, 1])
    with col_cep:
        cep_input = st.text_input("Digite o CEP:")
    with col_btn:
        st.write("")
        st.write("")
        if st.button("Buscar CEP"):
            if buscar_cep(cep_input):
                st.success("Endereço encontrado!")
            else:
                st.error("CEP inválido ou não encontrado.")

    logradouro = st.text_input("Rua/Avenida*:", value=st.session_state.end_logradouro)
    col_num, col_comp, col_bairro = st.columns([1, 1, 2])
    with col_num:
        numero = st.text_input("Número (ou 'S/N')*:")
    with col_comp:
        complemento = st.text_input("Complemento/Ref:")
    with col_bairro:
        bairro = st.text_input("Bairro*:", value=st.session_state.end_bairro)
        
    cidade = st.text_input("Cidade*:", value=st.session_state.end_cidade)
    
    # 3. Problema
    st.subheader("3. Detalhes do Problema")
    tipo_problema = st.selectbox("Qual o problema?", ["Lâmpada Apagada à Noite", "Lâmpada Acesa de Dia", "Poste Caído/Danificado", "Luminária Quebrada", "Luz Oscilando"])
    descricao = st.text_area("Descreva o problema com detalhes:")
    
    st.markdown("*Campos com (*) são obrigatórios.*")
    
    if st.button("Enviar Solicitação para a Prefeitura", type="primary"):
        # Validação de campos obrigatórios
        if logradouro and numero and bairro and cidade and nome_cidadao and cpf_cidadao and email_cidadao and whatsapp_cidadao:
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
                "prazo": "Não definido"
            }
            st.session_state.ordens_servico.append(nova_os)
            salvar_dados()
            
            st.success(f"Solicitação enviada! O número do seu protocolo é: **{nova_os['os']}**")
            
            for campo in ['end_logradouro', 'end_bairro', 'end_cidade', 'end_uf']:
                st.session_state[campo] = ""
        else:
            st.error("⚠️ Preencha todos os campos obrigatórios (*) antes de enviar a solicitação.")

# ==========================================
# ABA 2: VISÃO DA GERÊNCIA (TRIAGEM E MATERIAIS)
# ==========================================
with aba_gerencia:
    st.header("Gestão de Chamados e Estoque")
    
    # Dividindo a tela: Esquerda (Chamados Novos) | Direita (Menu Oculto/Suspenso)
    col_chamados, col_lateral = st.columns([2, 1])
    
    # --- COLUNA DIREITA: MENU SUSPENSO ---
    with col_lateral:
        st.markdown("### ⚙️ Menu da Gerência")
        
        # Menu 1: Materiais
        with st.expander("📦 Gerenciar Materiais", expanded=False):
            st.write("Estoque atual:")
            st.dataframe(pd.DataFrame(st.session_state.materiais_disponiveis, columns=["Materiais"]), hide_index=True)
            st.write("---")
            novo_material = st.text_input("Novo material:")
            if st.button("Adicionar Material"):
                if novo_material and novo_material not in st.session_state.materiais_disponiveis:
                    st.session_state.materiais_disponiveis.append(novo_material)
                    salvar_dados()
                    st.success("Adicionado!")
                    st.rerun()
                else:
                    st.warning("Já existe ou vazio.")
                    
        # Menu 2: Chamados em Andamento (Técnico na rua)
        with st.expander("📋 Chamados em Andamento", expanded=False):
            os_andamento = [os for os in st.session_state.ordens_servico if os['status'] in ["Enviada ao Técnico", "Em Andamento"]]
            if not os_andamento:
                st.write("Nenhum chamado com a equipe técnica no momento.")
            for os_item in os_andamento:
                st.markdown(f"**OS {os_item['os']}** - {os_item['problema']}")
                st.caption(f"Prazo: {os_item.get('prazo', 'N/D')} | Status: {os_item['status']}")
                st.write("---")

        # Menu 3: Chamados Concluídos (Histórico)
        with st.expander("✅ Chamados Concluídos", expanded=False):
            os_concluidas = [os for os in st.session_state.ordens_servico if os['status'] == "Concluída"]
            if not os_concluidas:
                st.write("Nenhum chamado concluído ainda.")
            for os_item in os_concluidas:
                st.markdown(f"**OS {os_item['os']}** - {os_item['problema']}")
                st.write(f"**Solicitante:** {os_item.get('nome_solicitante', 'N/D')} (WhatsApp: {os_item.get('whatsapp_solicitante', 'N/D')})")
                st.write(f"**Endereço:** {os_item['endereco']}")
                st.write(f"**Obs Técnico:** {os_item.get('obs_tecnico', 'Sem observação')}")
                st.write(f"**Materiais Gastos:** {', '.join(os_item.get('materiais', []))}")
                st.write("---")

    # --- COLUNA ESQUERDA: CHAMADOS NOVOS (TRIAGEM) ---
    with col_chamados:
        st.subheader("🚨 Chamados Aguardando Despacho")
        chamados_novos = [os for os in st.session_state.ordens_servico if os['status'] == "Aguardando Despacho"]
        
        if not chamados_novos:
            st.info("Nenhum chamado novo aguardando triagem no momento.")
        else:
            for os_item in chamados_novos:
                with st.container():
                    st.markdown(f"#### OS: {os_item['os']} - {os_item['problema']}")
                    st.write(f"📅 **Aberto em:** {os_item['data']}")
                    st.write(f"👤 **Solicitante:** {os_item.get('nome_solicitante', 'N/D')} - Contato: {os_item.get('whatsapp_solicitante', 'N/D')}")
                    st.write(f"📍 **Endereço:** {os_item['endereco']}")
                    st.write(f"📝 **Descrição:** {os_item['descricao']}")
                    
                    # Definir prazo e enviar
                    col_prazo, col_btn_envio = st.columns([2, 1])
                    with col_prazo:
                        prazo_selecionado = st.date_input("Prazo Limite para o Técnico:", min_value=date.today(), key=f"prazo_{os_item['os']}")
                    with col_btn_envio:
                        st.write("")
                        st.write("")
                        if st.button(f"Despachar OS", key=f"btn_{os_item['os']}", type="primary"):
                            os_item['status'] = "Enviada ao Técnico"
                            os_item['prazo'] = prazo_selecionado.strftime("%d/%m/%Y")
                            salvar_dados()
                            st.success("OS enviada com sucesso!")
                            st.rerun()
                    st.divider()

# ==========================================
# ABA 3: VISÃO DO TÉCNICO (MANUTENÇÃO)
# ==========================================
with aba_tecnico:
    st.header("Ordens de Serviço do Técnico")
    
    os_tecnico = [os for os in st.session_state.ordens_servico if os['status'] in ["Enviada ao Técnico", "Em Andamento"]]
    os_tecnico.sort(key=lambda x: datetime.strptime(x['data'], "%d/%m/%Y %H:%M"))
    
    if not os_tecnico:
        st.info("Nenhuma ordem de serviço pendente para a equipe de rua!")
    else:
        for os_item in os_tecnico:
            with st.expander(f"OS: {os_item['os']} ({os_item['status']}) - {os_item['problema']}"):
                st.write(f"**Data da Solicitação:** {os_item['data']}")
                st.write(f"**Endereço:** {os_item['endereco']}")
                st.write(f"**Problema Relatado:** {os_item['descricao']}")
                
                prazo_texto = os_item.get('prazo', 'Não definido')
                st.error(f"⚠️ **PRAZO LIMITE:** {prazo_texto}")
                
                with st.form(f"form_tecnico_{os_item['os']}"):
                    novo_status = st.selectbox("Status do Serviço:", ["Em Andamento", "Concluída"], index=0 if os_item['status']=="Enviada ao Técnico" else 1)
                    
                    st.write("---")
                    materiais_selecionados = st.multiselect("Materiais Utilizados:", st.session_state.materiais_disponiveis)
                    quantidades_usadas = {}
                    if materiais_selecionados:
                        for mat in materiais_selecionados:
                            qtd = st.number_input(f"Quantidade de '{mat}'", min_value=1, value=1, step=1)
                            quantidades_usadas[mat] = qtd
                    
                    obs_tecnico = st.text_area("Observações do Técnico (Ex: Falei com o solicitante, rede estava em curto...):")
                    
                    submit_baixa = st.form_submit_button("Salvar Apontamento")
                    if submit_baixa:
                        os_item['status'] = novo_status
                        os_item['materiais'] = [f"{qtd}x {mat}" for mat, qtd in quantidades_usadas.items()]
                        if obs_tecnico: os_item['obs_tecnico'] = obs_tecnico
                            
                        salvar_dados()
                        st.success("Apontamento salvo!")
                        st.rerun()

# ==========================================
# ABA 4: VISÃO DA PREFEITURA (DASHBOARD)
# ==========================================
with aba_prefeitura:
    st.header("Painel de Gestão e Monitoramento")
    
    # --- SISTEMA DE ALERTA DE ATRASOS ---
    hoje_str = date.today().strftime("%d/%m/%Y")
    hoje_dt = datetime.strptime(hoje_str, "%d/%m/%Y")
    
    os_atrasadas = []
    for os_item in st.session_state.ordens_servico:
        if os_item['status'] not in ["Concluída", "Aguardando Despacho"]:
            prazo_str = os_item.get('prazo', '')
            if prazo_str and prazo_str != "Não definido":
                prazo_dt = datetime.strptime(prazo_str, "%d/%m/%Y")
                if hoje_dt > prazo_dt:
                    os_atrasadas.append(os_item)
    
    if len(os_atrasadas) > 0:
        st.error(f"⚠️ ATENÇÃO: Existem {len(os_atrasadas)} ordem(ns) de serviço com o PRAZO VENCIDO!")
    else:
        st.success("✅ Todos os chamados técnicos estão dentro do prazo estipulado.")
    
    st.write("---")
    
    if st.session_state.ordens_servico:
        df_os = pd.DataFrame(st.session_state.ordens_servico)
        
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.metric("Total de Chamados", len(df_os))
        col_m2.metric("Aguardando Gerência", len(df_os[df_os['status'] == 'Aguardando Despacho']))
        col_m3.metric("Com a Equipe Técnica", len(df_os[df_os['status'].isin(['Enviada ao Técnico', 'Em Andamento'])]))
        col_m4.metric("Serviços Concluídos", len(df_os[df_os['status'] == 'Concluída']))
        
        st.subheader("Histórico Completo")
        # Mostrar o DataFrame ordenado (mais recentes primeiro)
        st.dataframe(df_os[['os', 'data', 'prazo', 'endereco', 'problema', 'status']], use_container_width=True)
    else:
        st.write("Nenhuma OS registrada.")
