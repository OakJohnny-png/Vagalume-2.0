import streamlit as st
import pandas as pd
import uuid
from datetime import datetime
import requests

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Gestão de Iluminação Pública", layout="wide")

# --- INICIALIZAÇÃO DOS DADOS (SIMULANDO BANCO DE DADOS) ---
if 'ordens_servico' not in st.session_state:
    st.session_state.ordens_servico = []

if 'materiais_disponiveis' not in st.session_state:
    st.session_state.materiais_disponiveis = [
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

# Variáveis temporárias para a busca de CEP
if 'end_logradouro' not in st.session_state: st.session_state.end_logradouro = ""
if 'end_bairro' not in st.session_state: st.session_state.end_bairro = ""
if 'end_cidade' not in st.session_state: st.session_state.end_cidade = ""
if 'end_uf' not in st.session_state: st.session_state.end_uf = ""

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
st.title("💡 Sistema de Gestão de Iluminação Pública - Rio do Sul")

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
    
    st.subheader("1. Endereço do Problema")
    col_cep, col_btn = st.columns([2, 1])
    with col_cep:
        cep_input = st.text_input("Digite o CEP:")
    with col_btn:
        st.write("") # Espaçamento
        st.write("")
        if st.button("Buscar CEP"):
            if buscar_cep(cep_input):
                st.success("Endereço encontrado!")
            else:
                st.error("CEP inválido ou não encontrado.")

    # Campos de endereço (preenchidos automaticamente se o CEP for válido)
    logradouro = st.text_input("Rua/Avenida:", value=st.session_state.end_logradouro)
    col_num, col_comp, col_bairro = st.columns([1, 1, 2])
    with col_num:
        numero = st.text_input("Número (ou 'S/N'):")
    with col_comp:
        complemento = st.text_input("Complemento/Ref:")
    with col_bairro:
        bairro = st.text_input("Bairro:", value=st.session_state.end_bairro)
        
    cidade = st.text_input("Cidade:", value=st.session_state.end_cidade)
    
    st.subheader("2. Detalhes do Problema")
    tipo_problema = st.selectbox("Qual o problema?", ["Lâmpada Apagada à Noite", "Lâmpada Acesa de Dia", "Poste Caído/Danificado", "Luminária Quebrada", "Luz Oscilando"])
    descricao = st.text_area("Descreva o problema com detalhes:")
    
    if st.button("Enviar Solicitação para a Prefeitura"):
        if logradouro and numero:
            endereco_completo = f"{logradouro}, {numero} - {complemento} | Bairro: {bairro} | {cidade}"
            nova_os = {
                "os": str(uuid.uuid4())[:8].upper(),
                "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "endereco": endereco_completo,
                "problema": tipo_problema,
                "descricao": descricao,
                "status": "Aguardando Despacho", # Vai para a gerência primeiro
                "materiais": []
            }
            st.session_state.ordens_servico.append(nova_os)
            st.success(f"Solicitação enviada! O número do seu protocolo é: **{nova_os['os']}**")
            # Limpa os campos temporários
            st.session_state.end_logradouro = ""
            st.session_state.end_bairro = ""
            st.session_state.end_cidade = ""
            st.session_state.end_uf = ""
        else:
            st.warning("Preencha ao menos a Rua e o Número antes de enviar.")

# ==========================================
# ABA 2: VISÃO DA GERÊNCIA (TRIAGEM E MATERIAIS)
# ==========================================
with aba_gerencia:
    st.header("Gestão de Chamados e Estoque")
    
    col_chamados, col_estoque = st.columns(2)
    
    with col_chamados:
        st.subheader("Chamados Novos (Aguardando Despacho)")
        chamados_novos = [os for os in st.session_state.ordens_servico if os['status'] == "Aguardando Despacho"]
        
        if not chamados_novos:
            st.info("Nenhum chamado novo aguardando triagem.")
        else:
            for os in chamados_novos:
                with st.expander(f"OS: {os['os']} - {os['problema']}"):
                    st.write(f"**Endereço:** {os['endereco']}")
                    st.write(f"**Descrição do Munícipe:** {os['descricao']}")
                    
                    if st.button(f"Despachar OS {os['os']} para a Equipe Técnica"):
                        os['status'] = "Enviada ao Técnico"
                        st.success("Ordem de Serviço enviada ao técnico com sucesso!")
                        st.rerun()

    with col_estoque:
        st.subheader("Cadastrar Novos Materiais")
        st.write("Materiais atualmente no sistema:")
        st.dataframe(pd.DataFrame(st.session_state.materiais_disponiveis, columns=["Material Exigido/Cadastrado"]), hide_index=True)
        
        novo_material = st.text_input("Nome do novo material:")
        if st.button("Adicionar Material"):
            if novo_material and novo_material not in st.session_state.materiais_disponiveis:
                st.session_state.materiais_disponiveis.append(novo_material)
                st.success(f"Material '{novo_material}' cadastrado com sucesso!")
                st.rerun()
            else:
                st.warning("Material já existe ou campo está vazio.")

# ==========================================
# ABA 3: VISÃO DO TÉCNICO (MANUTENÇÃO)
# ==========================================
with aba_tecnico:
    st.header("Ordens de Serviço do Técnico")
    
    # O técnico só vê o que a gerência despachou ou o que ele já começou
    os_tecnico = [os for os in st.session_state.ordens_servico if os['status'] in ["Enviada ao Técnico", "Em Andamento"]]
    
    if not os_tecnico:
        st.info("Nenhuma ordem de serviço pendente para as equipes de rua!")
    else:
        for os in os_tecnico:
            with st.expander(f"OS: {os['os']} ({os['status']}) - {os['problema']}"):
                st.write(f"**Endereço:** {os['endereco']}")
                st.write(f"**Problema Relatado:** {os['descricao']}")
                
                with st.form(f"form_tecnico_{os['os']}"):
                    novo_status = st.selectbox("Status do Serviço:", ["Em Andamento", "Concluída"], index=0 if os['status']=="Enviada ao Técnico" else 1)
                    
                    st.write("---")
                    st.write("**Materiais Utilizados no Reparo:**")
                    # Seleção de materiais da lista dinâmica
                    materiais_selecionados = st.multiselect(
                        "Selecione os materiais (pode escolher vários):", 
                        st.session_state.materiais_disponiveis
                    )
                    
                    # Se ele selecionou materiais, pede a quantidade de cada um
                    quantidades_usadas = {}
                    if materiais_selecionados:
                        for mat in materiais_selecionados:
                            qtd = st.number_input(f"Quantidade de '{mat}'", min_value=1, value=1, step=1)
                            quantidades_usadas[mat] = qtd
                    
                    obs_tecnico = st.text_area("Observações do Técnico:")
                    
                    submit_baixa = st.form_submit_button("Salvar Apontamento do Técnico")
                    if submit_baixa:
                        os['status'] = novo_status
                        # Salva a lista de materiais formatada
                        lista_final_materiais = [f"{qtd}x {mat}" for mat, qtd in quantidades_usadas.items()]
                        os['materiais'] = lista_final_materiais
                        if obs_tecnico:
                            os['obs_tecnico'] = obs_tecnico
                            
                        st.success("Apontamento salvo com sucesso!")
                        st.rerun()

# ==========================================
# ABA 4: VISÃO DA PREFEITURA (DASHBOARD)
# ==========================================
with aba_prefeitura:
    st.header("Painel de Gestão Geral (Transparência)")
    
    if st.session_state.ordens_servico:
        df_os = pd.DataFrame(st.session_state.ordens_servico)
        
        # Cria métricas rápidas
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.metric("Total de Chamados", len(df_os))
        col_m2.metric("Aguardando Gerência", len(df_os[df_os['status'] == 'Aguardando Despacho']))
        col_m3.metric("Com a Equipe Técnica", len(df_os[df_os['status'].isin(['Enviada ao Técnico', 'Em Andamento'])]))
        col_m4.metric("Serviços Concluídos", len(df_os[df_os['status'] == 'Concluída']))
        
        st.write("---")
        st.subheader("Histórico Completo de Serviços")
        st.dataframe(df_os[['os', 'data', 'endereco', 'problema', 'status', 'materiais']], use_container_width=True)
    else:
        st.write("Nenhuma OS registrada no sistema até o momento.")
