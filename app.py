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
                {"username": "ger
