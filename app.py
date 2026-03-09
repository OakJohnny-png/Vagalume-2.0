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
st.set_page_config(page_title="Sistema Vagalume - Iluminação Pública", layout="wide")

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

# --- TÍTULO DO APP (RESPONSIVO E ADAPTÁVEL) ---
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
st.write("") # Espaço antes das abas

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
    st.markdown(
        """
        <h2 style="white-space: nowrap; font-size: clamp(18px, 3.5vw, 32px); margin-bottom: 10px;">
            Registrar Problema na Iluminação
        </h2>
        """, 
        unsafe_allow_html=True
    )
    
    # 1. Dados do Solicitante
    st.markdown(
        """
        <h3 style="white-space: nowrap; font-size: clamp(16px, 2.5vw, 24px); margin-bottom: 10px; color: #444;">
            1. Dados do Solicitante
        </h3>
        """, 
        unsafe_allow_html=True
    )
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
    st.markdown(
        """
        <h3 style="white-space: nowrap; font-size: clamp(16px, 2.5vw, 24px); margin-top: 20px; margin-bottom: 10px; color: #444;">
            2. Endereço do Problema
        </h3>
        """, 
        unsafe_allow_html=True
    )
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
    st.markdown(
        """
        <h3 style="white-space: nowrap; font-size: clamp(16px, 2.5vw, 24px); margin-top: 20px; margin-bottom: 10px; color: #444;">
            3. Detalhes do Problema
        </h3>
        """, 
        unsafe_allow_html=True
    )
    tipo_problema = st.selectbox("Qual o problema?", ["Lâmpada Apagada à Noite", "Lâmpada Acesa de Dia", "Poste Caído/Danificado", "Luminária Quebrada", "Luz Oscilando"])
    descricao = st.text_area("Descreva o problema com detalhes:")
    
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
