# Guia de Instalação e Configuração: Stok Holmes

Este guia contém o passo a passo extremamente detalhado para configurar o seu computador Windows, instalar as dependências necessárias, contornar possíveis erros de política de execução do PowerShell e rodar o aplicativo **Stok Holmes** desenvolvido em Python com a biblioteca Streamlit.

## 1. Pré-requisitos e Instalação do Python

Antes de executar o sistema, você precisará ter o Python instalado no seu computador.

1. Acesse o site oficial do Python: [python.org/downloads](https://www.python.org/downloads/)
2. Baixe a versão mais recente para Windows.
3. Durante a instalação, **é fundamental marcar a caixa "Add Python to PATH"** (Adicionar Python ao PATH) antes de clicar em "Install Now". Isso permitirá que o Windows reconheça os comandos do Python no terminal.
4. Após a instalação, abra o "Prompt de Comando" (CMD) ou o "PowerShell" e digite:
   ```cmd
   python --version
   ```
   Se a versão do Python aparecer na tela, a instalação foi concluída com sucesso.

## 2. Preparando os Arquivos do Sistema

Você recebeu três arquivos principais:
- `app_busca.py`: O código-fonte do sistema.
- `estoque.xlsx`: O banco de dados inicial de exemplo.
- `iniciar_stok_holmes.bat`: O atalho para iniciar o sistema com dois cliques.

**Passo a passo:**
1. Crie uma pasta no seu computador (por exemplo, em "Documentos") com o nome `Stok_Holmes`.
2. Coloque os três arquivos mencionados acima dentro dessa pasta.

## 3. Instalando as Bibliotecas Necessárias

O sistema utiliza algumas bibliotecas externas que não vêm instaladas por padrão no Python. Você precisará instalá-las usando o gerenciador de pacotes `pip`.

1. Abra o **PowerShell** ou o **Prompt de Comando** como Administrador (clique com o botão direito no menu Iniciar e selecione "Windows PowerShell (Administrador)").
2. Digite o seguinte comando e pressione **Enter**:
   ```cmd
   pip install streamlit pandas openpyxl xlsxwriter
   ```
3. Aguarde o download e a instalação de todas as dependências. Quando o terminal liberar para digitar novamente, a instalação estará concluída.

## 4. Contornando Erros de Política de Execução do PowerShell (Opcional, mas recomendado)

Em alguns computadores com Windows, o PowerShell bloqueia a execução de scripts locais por questões de segurança, o que pode causar erros ao tentar rodar o Streamlit ou o arquivo `.bat`. Para resolver isso:

1. Ainda no **PowerShell como Administrador**, digite o seguinte comando e pressione **Enter**:
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```
2. O sistema perguntará se você deseja alterar a política de execução. Digite `S` (Sim) e pressione **Enter**.
3. Isso permitirá que scripts locais criados por você (como o arquivo `.bat` e os scripts do Python) sejam executados sem bloqueios.

## 5. Executando o Sistema

Existem duas formas de iniciar o sistema **Stok Holmes**:

### Opção A: Usando o arquivo `.bat` (Mais fácil)
1. Vá até a pasta `Stok_Holmes` onde você salvou os arquivos.
2. Dê um duplo clique no arquivo `iniciar_stok_holmes.bat`.
3. Uma janela preta (terminal) se abrirá, indicando que o servidor local está sendo iniciado.
4. Em alguns segundos, o seu navegador padrão abrirá automaticamente com a interface do sistema.

### Opção B: Pelo Terminal
1. Abra o terminal (PowerShell ou CMD) e navegue até a pasta do projeto:
   ```cmd
   cd Caminho\Para\Sua\Pasta\Stok_Holmes
   ```
2. Execute o comando:
   ```cmd
   python -m streamlit run app_busca.py
   ```
3. O navegador será aberto automaticamente.

## 6. Como Atualizar o Estoque

O sistema lê os dados diretamente do arquivo `estoque.xlsx`.
- Para adicionar novos itens, atualizar localizações ou corrigir descrições, basta abrir o arquivo `estoque.xlsx` no Microsoft Excel.
- Faça as alterações necessárias e **salve o arquivo**.
- Ao atualizar a página do sistema no navegador, as novas informações já estarão disponíveis para busca e devolução.

> **Nota importante:** O arquivo `estoque.xlsx` deve sempre manter as três colunas na primeira linha: "Código", "Descrição" e "Localização", exatamente com esses nomes.
