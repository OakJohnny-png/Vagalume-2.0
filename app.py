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
    cep = cep.replace("-
