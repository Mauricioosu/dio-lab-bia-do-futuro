import os
import json
import pandas as pd
import chainlit as cl
from chainlit.input_widget import Select, TextInput
from modules.orchestrator import FinAssistOrchestrator

# CONFIGURAÇÕES DE CAMINHOS
current_dir = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.abspath(os.path.join(current_dir, "..", "data"))

# FUNÇÕES AUXILIARES

async def ensure_data_directory():
    """Garante que a pasta de dados exista na raiz do projeto."""
    if not os.path.exists(DATA_PATH):
        os.makedirs(DATA_PATH)

def load_json(filename):
    path = os.path.join(DATA_PATH, filename)
    try:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    except Exception as e:
        print(f"Erro ao carregar JSON {filename}: {e}")
        return None

def load_csv(filename):
    path = os.path.join(DATA_PATH, filename)
    try:
        if os.path.exists(path):
            return pd.read_csv(path)
        return None
    except Exception as e:
        print(f"Erro ao carregar CSV {filename}: {e}")
        return None

async def load_all_financial_data():
    """Consolida o carregamento dos dados para a sessão."""
    return {
        "perfil_investidor": load_json("perfil_investidor.json"),
        "produtos_financeiros": load_json("produtos_financeiros.json") or [],
        "transacoes": load_csv("transacoes.csv"),
        "objetivos_financeiros": load_json("objetivos_financeiros.json") or []
    }

async def run_onboarding():
    """Fluxo de configuração inicial."""
    await cl.Message(content="👋 Olá! Sou o FinAssist Pro. Vamos configurar sua base financeira.").send()
    
    res_nome = await cl.AskUserMessage(content="Qual é o seu nome?", timeout=120).send()
    if res_nome is None: return
    nome_usuario = res_nome.get('output', "Usuário")

    perfil_escolhido = None
    opcoes_validas = ["conservador", "moderado", "arrojado"]
    while not perfil_escolhido:
        res_perfil = await cl.AskUserMessage(content=f"{nome_usuario}, qual seu perfil? (Conservador, Moderado, Arrojado)", timeout=90).send()
        if res_perfil is None: return
        resp = res_perfil.get('output', "").lower().strip()
        if resp in opcoes_validas: perfil_escolhido = resp.capitalize()
        else: await cl.Message(content="💡 Escolha entre: Conservador, Moderado ou Arrojado.").send()
    
    saldo_final = 0.0
    while True:
        res_saldo = await cl.AskUserMessage(content="Qual seu saldo atual? (Ex: 1250.00)", timeout=60).send()
        if res_saldo is None: return
        try:
            saldo_final = float(res_saldo.get('output', '0').replace(',', '.'))
            break
        except ValueError: await cl.Message(content="⚠️ Use apenas números.").send()

    perfil_data = {"nome": nome_usuario, "perfil": perfil_escolhido, "saldo_atual": saldo_final}
    with open(os.path.join(DATA_PATH, "perfil_investidor.json"), "w", encoding='utf-8') as f:
        json.dump(perfil_data, f, ensure_ascii=False, indent=4)
    pd.DataFrame(columns=['data', 'descricao', 'valor', 'categoria', 'prioridade']).to_csv(os.path.join(DATA_PATH, "transacoes.csv"), index=False)
    with open(os.path.join(DATA_PATH, "objetivos_financeiros.json"), "w", encoding='utf-8') as f:
        json.dump([], f, ensure_ascii=False, indent=4)
    await cl.Message(content=f"✅ Tudo pronto, **{nome_usuario}**!").send()

# FLUXO PRINCIPAL

@cl.on_chat_start
async def start():
    await ensure_data_directory()
    
    # Renderiza Widgets (Engrenagem)
    settings = await cl.ChatSettings([
        Select(id="ModelMode", label="🤖 Modo do Modelo", values=["local", "gemini", "openai"], initial_index=0),
        TextInput(id="GeminiKey", label="Gemini API Key", placeholder="Insira aqui..."),
        TextInput(id="OpenAIKey", label="OpenAI API Key", placeholder="Insira aqui...")
    ]).send()

    perfil_path = os.path.join(DATA_PATH, "perfil_investidor.json")
    if not os.path.exists(perfil_path):
        await run_onboarding()

    # Carrega dados e Orquestrador
    data = await load_all_financial_data()
    cl.user_session.set("financial_data", data)
    
    orchestrator = FinAssistOrchestrator(mode=settings["ModelMode"])
    cl.user_session.set("orchestrator", orchestrator)
    
    nome = data.get("perfil_investidor", {}).get("nome", "Usuário")
    await cl.Message(content=f"Bem-vindo de volta, **{nome}**! Como posso ajudar hoje?").send()

@cl.on_settings_update
async def setup_agent(settings):
    mode = settings["ModelMode"]
    api_key = settings["GeminiKey"] if mode == "gemini" else settings["OpenAIKey"]
    cl.user_session.set("orchestrator", FinAssistOrchestrator(mode=mode, api_key=api_key))
    await cl.Message(content=f"⚙️ Modo **{mode.upper()}** ativado.").send()

@cl.on_message
async def main(message: cl.Message):
    orchestrator = cl.user_session.get("orchestrator")
    if orchestrator:
        response = await orchestrator.run(message.content)
        await cl.Message(content=response).send()