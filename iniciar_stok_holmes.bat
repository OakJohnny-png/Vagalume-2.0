@echo off
REM ============================================================
REM  Stok Holmes — Iniciador do Sistema
REM  Basta dar duplo clique neste arquivo para abrir o sistema.
REM ============================================================

title Stok Holmes - NEMA

echo.
echo  =============================================
echo   Stok Holmes - Sistema de Gestao de Estoque
echo   NEMA - Obras e Instalacoes Eletricas
echo  =============================================
echo.
echo  Iniciando o servidor... Aguarde.
echo  O navegador abrira automaticamente em instantes.
echo.

REM Muda para o diretório onde este .bat está localizado
cd /d "%~dp0"

REM Executa o Streamlit
python -m streamlit run app_busca.py

pause
