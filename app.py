import chainlit as cl
import pandas as pd
import json
from modules.orchestrator import FinAssistOrchestrator

# Funções de carregamento de dados
def load_csv(filename):
    try:
        return pd.read_csv(f"data/{filename}").to_dict('records')
    except Exception as e:
        print(f"Erro ao carregar CSV {filename}: {e}")
        return None

def load_json(filename):
    try:
        with open(f"data/{filename}", 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Erro ao carregar JSON {filename}: {e}")
        return None

@cl.on_chat_start
async def start():
    data = {
        "perfil": load_json("perfil_investidor.json"),
        "produtos": load_json("produtos_financeiros.json"),
        "transacoes": load_csv("transacoes.csv"),
        "objetivos": load_json("objetivos_financeiros.json")
    }

    if data["perfil"] is None or data["transacoes"] is None:
        await cl.Message(content="Erro: Falha ao carregar arquivos base na pasta /data.").send()
        return
    
    cl.user_session.set("financial_data", data) 

    orchestrator = FinAssistOrchestrator(data=data) 
    cl.user_session.set("orchestrator", orchestrator)
    
    await cl.Message(content="Assistente FinAssist Pro online. Como posso ajudar com suas finanças hoje?").send()

@cl.on_message
async def main(message: cl.Message):
    orchestrator = cl.user_session.get("orchestrator")
    data = cl.user_session.get("financial_data")
    

    if not orchestrator or not data:
        await cl.Message(content=" Erro de sessão: Os dados financeiros não foram localizados.").send()
        return

    response = await orchestrator.run(message.content)
    await cl.Message(content=response).send()