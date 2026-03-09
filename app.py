import streamlit as st
import pandas as pd
import uuid
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Gestão de Iluminação Pública", layout="wide")

# --- INICIALIZAÇÃO DOS DADOS (SIMULANDO BANCO DE DADOS) ---
if 'pontos' not in st.session_state:
    st.session_state.pontos = pd.DataFrame([
        {"id": "IP-001", "lat": -27.2144, "lon": -49.6441, "tipo": "LED", "potencia": "100W"},
        {"id": "IP-002", "lat": -27.2150, "lon": -49.6450, "tipo": "Vapor Sódio", "potencia": "150W"},
        {"id": "IP-003", "lat": -27.2160, "lon": -49.6430, "tipo": "LED", "potencia": "150W"}
    ])
if 'ordens_servico' not in st.session_state:
    st.session_state.ordens_servico = []

# --- TÍTULO DO APP ---
st.title("💡 Sistema de Gestão de Iluminação Pública - Rio do Sul")

# --- CRIAÇÃO DAS ABAS (MÓDULOS DO SISTEMA) ---
aba_cidadao, aba_tecnico, aba_prefeitura = st.tabs(["📱 Aplicativo do Cidadão", "🛠️ App do Técnico", "📊 Painel da Prefeitura (Gestão)"])

# ==========================================
# ABA 1: VISÃO DO CIDADÃO (SOLICITAÇÕES)
# ==========================================
with aba_cidadao:
    st.header("Registrar Problema na Iluminação")
    
    with st.form("form_solicitacao"):
        ponto_afetado = st.selectbox("Selecione o Poste Próximo:", st.session_state.pontos['id'].tolist())
        tipo_problema = st.selectbox("Qual o problema?", ["Lâmpada Apagada à Noite", "Lâmpada Acesa de Dia", "Poste Caído/Danificado", "Luminária Quebrada", "Luz Oscilando"])
        descricao = st.text_area("Descreva o problema com detalhes:")
        
        submit = st.form_submit_button("Enviar Solicitação")
        
        if submit:
            nova_os = {
                "os": str(uuid.uuid4())[:8].upper(),
                "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "ponto": ponto_afetado,
                "problema": tipo_problema,
                "descricao": descricao,
                "status": "Aberta",
                "materiais": []
            }
            st.session_state.ordens_servico.append(nova_os)
            st.success(f"Solicitação enviada com sucesso! Número da OS gerada: {nova_os['os']}")

# ==========================================
# ABA 2: VISÃO DO TÉCNICO (MANUTENÇÃO)
# ==========================================
with aba_tecnico:
    st.header("Ordens de Serviço em Aberto")
    
    os_abertas = [os for os in st.session_state.ordens_servico if os['status'] in ["Aberta", "Em Andamento"]]
    
    if not os_abertas:
        st.info("Nenhuma ordem de serviço pendente!")
    else:
        for os in os_abertas:
            with st.expander(f"OS: {os['os']} - {os['ponto']} ({os['status']})"):
                st.write(f"**Problema:** {os['problema']}")
                st.write(f"**Descrição:** {os['descricao']}")
                st.write(f"**Data:** {os['data']}")
                
                # Formulário para baixar a OS
                with st.form(f"form_baixa_{os['os']}"):
                    novo_status = st.selectbox("Atualizar Status:", ["Em Andamento", "Concluída"], index=0 if os['status']=="Aberta" else 1)
                    materiais = st.text_input("Materiais Utilizados (Ex: 1x Lâmpada LED 100W, 2m Cabo):")
                    
                    submit_baixa = st.form_submit_button("Salvar Apontamento")
                    if submit_baixa:
                        os['status'] = novo_status
                        if materiais:
                            os['materiais'].append(materiais)
                        st.success("Ordem de Serviço atualizada!")
                        st.rerun() # Recarrega a página para atualizar os dados

# ==========================================
# ABA 3: VISÃO DA PREFEITURA (DASHBOARD)
# ==========================================
with aba_prefeitura:
    st.header("Painel de Gestão em Tempo Real")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Mapa Georreferenciado dos Pontos")
        # O Streamlit possui uma função nativa para plotar mapas usando latitude e longitude
        st.map(st.session_state.pontos)
        
    with col2:
        st.subheader("Resumo das Ordens de Serviço")
        if st.session_state.ordens_servico:
            df_os = pd.DataFrame(st.session_state.ordens_servico)
            st.dataframe(df_os[['os', 'data', 'ponto', 'problema', 'status']])
        else:
            st.write("Nenhuma OS registrada até o momento.")
