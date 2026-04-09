"""
Script auxiliar para gerar um arquivo estoque.xlsx de exemplo.
Execute uma única vez para criar o banco de dados inicial.
"""
import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXCEL_PATH = os.path.join(BASE_DIR, "estoque.xlsx")

dados = [
    {"Código": "EL-001", "Descrição": "CABO FLEXÍVEL 2,5MM² PRETO",          "Localização": "PRATELEIRA A1"},
    {"Código": "EL-002", "Descrição": "CABO FLEXÍVEL 4MM² AZUL",              "Localização": "PRATELEIRA A1"},
    {"Código": "EL-003", "Descrição": "CABO FLEXÍVEL 6MM² VERDE",             "Localização": "PRATELEIRA A2"},
    {"Código": "EL-004", "Descrição": "DISJUNTOR MONOPOLAR 10A",              "Localização": "PRATELEIRA B1"},
    {"Código": "EL-005", "Descrição": "DISJUNTOR MONOPOLAR 16A",              "Localização": "PRATELEIRA B1"},
    {"Código": "EL-006", "Descrição": "DISJUNTOR BIPOLAR 20A",                "Localização": "PRATELEIRA B2"},
    {"Código": "EL-007", "Descrição": "DISJUNTOR TRIPOLAR 32A",               "Localização": "PRATELEIRA B2"},
    {"Código": "EL-008", "Descrição": "TOMADA 2P+T 10A BRANCA",               "Localização": "PRATELEIRA C1"},
    {"Código": "EL-009", "Descrição": "TOMADA 2P+T 20A BRANCA",               "Localização": "PRATELEIRA C1"},
    {"Código": "EL-010", "Descrição": "INTERRUPTOR SIMPLES 10A",              "Localização": "PRATELEIRA C2"},
    {"Código": "EL-011", "Descrição": "INTERRUPTOR PARALELO 10A",             "Localização": "PRATELEIRA C2"},
    {"Código": "EL-012", "Descrição": "QUADRO DE DISTRIBUIÇÃO 12 DISJUNTORES","Localização": "PRATELEIRA D1"},
    {"Código": "EL-013", "Descrição": "ELETRODUTO PVC 3/4\" CORRUGADO 25M",   "Localização": "CORREDOR 1"},
    {"Código": "EL-014", "Descrição": "ELETRODUTO PVC 1\" RÍGIDO 3M",         "Localização": "CORREDOR 1"},
    {"Código": "EL-015", "Descrição": "FITA ISOLANTE ANTICHAMA 19MM",         "Localização": "PRATELEIRA E1"},
    {"Código": "EL-016", "Descrição": "CONECTOR PARAFUSO TIPO U 10MM²",       "Localização": "PRATELEIRA E2"},
    {"Código": "EL-017", "Descrição": "LUMINÁRIA LED SOBREPOR 40W",           "Localização": "PRATELEIRA F1"},
    {"Código": "EL-018", "Descrição": "LÂMPADA LED BULBO 9W E27",             "Localização": "PRATELEIRA F1"},
    {"Código": "EL-019", "Descrição": "SENSOR DE PRESENÇA TETO 360°",         "Localização": "PRATELEIRA F2"},
    {"Código": "EL-020", "Descrição": "TRANSFORMADOR DE ISOLAMENTO 1KVA",     "Localização": "PRATELEIRA G1"},
]

df = pd.DataFrame(dados)
df.to_excel(EXCEL_PATH, index=False)
print(f"Arquivo criado com sucesso: {EXCEL_PATH}")
