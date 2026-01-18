import os
import json
import pandas as pd

class FinancialRetriever:
    def __init__(self, data=None):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_path = os.path.abspath(os.path.join(current_dir, "..", "..", "data"))
        
        self.data = data if data else self._load_all_data()

    def _load_all_data(self):
        """Carrega a base de verdade de forma robusta e absoluta."""
        data = {}
        
        paths = {
            "perfil_investidor": os.path.join(self.data_path, "perfil_investidor.json"),
            "transacoes": os.path.join(self.data_path, "transacoes.csv"),
            "objetivos_financeiros": os.path.join(self.data_path, "objetivos_financeiros.json")
        }

        # Carregar Perfil
        if os.path.exists(paths["perfil_investidor"]):
            try:
                with open(paths["perfil_investidor"], 'r', encoding='utf-8') as f:
                    data["perfil_investidor"] = json.load(f)
            except Exception as e:
                print(f"Erro ao ler perfil: {e}")

        # Carregar Transações
        if os.path.exists(paths["transacoes"]):
            try:
                data["transacoes"] = pd.read_csv(paths["transacoes"])
            except Exception as e:
                print(f"Erro ao ler transações: {e}")

        return data

    def get_relevant_context(self, query: str):
        """Filtra o contexto relevante para a pergunta (Grounding)."""
        context = []
        
        # Injeta perfil do usuário sempre para manter a Persona
        perfil = self.data.get("perfil_investidor")
        if perfil:
            context.append(f"Usuário: {perfil.get('nome')} | Perfil: {perfil.get('perfil')} | Saldo Atual: R$ {perfil.get('saldo_atual'):.2f}")

        # Busca simples por palavra-chave nas transações
        if "gasto" in query.lower() or "extrato" in query.lower() or "transação" in query.lower():
            df = self.data.get("transacoes")
            if df is not None and not df.empty:
                ultimas = df.tail(5).to_string(index=False)
                context.append(f"Últimas Transações:\n{ultimas}")

        return "\n".join(context) if context else "Nenhum dado financeiro encontrado."
    
    def add_transaction(self, descricao, valor, categoria="Geral", prioridade="Média"):
            transacoes_path = os.path.join(self.data_path, "transacoes.csv")
            perfil_path = os.path.join(self.data_path, "perfil_investidor.json")
            
            nova_linha = {
                "data": pd.Timestamp.now().strftime("%d/%m/%Y"),
                "descricao": str(descricao),
                "valor": float(valor),
                "categoria": str(categoria),
                "prioridade": str(prioridade)
            }
            
            try:
                # 1. Carrega ou cria o DataFrame com colunas explícitas
                if os.path.exists(transacoes_path) and os.path.getsize(transacoes_path) > 0:
                    df = pd.read_csv(transacoes_path)
                else:
                    # Se o arquivo não existe ou está vazio, cria com a estrutura correta
                    df = pd.DataFrame(columns=['data', 'descricao', 'valor', 'categoria', 'prioridade'])

                # 2. Concatenação segura
                df = pd.concat([df, pd.DataFrame([nova_linha])], ignore_index=True)
                df.to_csv(transacoes_path, index=False)
                
                return True
            except Exception as e:
                print(f"Erro na operação de escrita: {e}")
                return False