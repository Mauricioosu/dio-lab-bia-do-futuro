import pandas as pd
import json
import chainlit as cl

class FinancialRetriever:
    def __init__(self, data=None):
        self.data = data if data else cl.user_session.get("financial_data")
    
    def get_relevant_context(self, user_query):
        if self.data is None:
            return "Erro: Base de conhecimento não carregada."
        
        query = user_query.lower()
        context_parts = []

        perfil_data = self.data.get('perfil')
        if perfil_data:
            context_parts.append(f"### PERFIL DO CLIENTE ###\n{json.dumps(perfil_data, indent=2, ensure_ascii=False)}")

        metas_data = self.data.get('metas') or self.data.get('objetivos')
        if metas_data and any(word in query for word in ["viagem", "meta", "objetivo", "comprar", "alcançar", "reserva"]):
            context_parts.append(f"### METAS ATIVAS ###\n{json.dumps(metas_data, indent=2, ensure_ascii=False)}")

        transacoes_data = self.data.get('transacoes')
        if transacoes_data and any(word in query for word in ["gasto", "dinheiro", "extrato", "compras", "lazer", "valor", "saldo"]):
            df = pd.DataFrame(transacoes_data)
            df.tail(5)  # evitar envio de dados desnecessários

            if not df.empty:
                resumo_gastos = df.groupby('categoria')['valor'].sum().to_dict()
                context_parts.append(f"### RESUMO DE GASTOS POR CATEGORIA ###\n{resumo_gastos}")
                context_parts.append(f"### ÚLTIMAS TRANSAÇÕES ###\n{df.tail(5).to_string(index=False)}")

        return "\n\n".join(context_parts)