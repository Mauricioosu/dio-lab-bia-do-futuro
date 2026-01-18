import json
from modules.retriever import FinancialRetriever
from modules.providers import OllamaProvider, OpenAIProvider, GeminiProvider


class FinAssistOrchestrator:
    def __init__(self, mode="local", data=None, api_key=None):
        self.mode = mode
        self.api_key = api_key
        self.data = data
        self.provider = self._get_provider()
        self.retriever = FinancialRetriever(data=self.data)
        # PROMPT
        self.system_prompt_base = """
        Você é o FinAssist Pro, um mentor financeiro inteligente. Seu papel é ajudar os usuários a gerenciar suas finanças pessoais com base nos dados fornecidos.
        # DIRETRIZES DE COMPORTAMENTO:
        1. BASE DE VERDADE: Use exclusivamente os dados fornecidos no contexto (Transações, Produtos, Metas e Perfil) para responder.
        2. PRECISÃO MATEMÁTICA: Ao realizar cálculos, descreva a fórmula utilizada. Se o cálculo for complexo, sugira que é uma simulação educacional.
        3. TOM DE VOZ: Seja consultivo, encorajador e profissional. Evite termos técnicos sem explicá-los brevemente.
        4. SEGURANÇA: Nunca solicite ou aceite senhas e dados sensíveis. Reforce que você não substitui um consultor humano certificado.

        # DIRETRIZES DE COMANDOS DE BANCO DE DADOS:
        1. PARA CRIAR (SAVE):
           - Gasto/Ganho: #SAVE_TRANSACAO#{"descricao": "Item", "valor": -50.00, "categoria": "Lazer"}#SAVE_TRANSACAO#
           - Meta: #SAVE_META#{"descricao": "Viajar", "valor": 5000.00}#SAVE_META#
        2. PARA EDITAR/ALTERAR (UPDATE):
           - Use o ID visível no contexto. Só envie os campos que mudaram.
           - Transação: #UPDATE_TRANSACAO#{"id": 5, "valor": -60.00}#UPDATE_TRANSACAO#
           - Meta: #UPDATE_META#{"id": 0, "valor_alvo": 6000.00}#UPDATE_META#
        3. PARA EXCLUIR (DELETE):
           - Transação: #DELETE_TRANSACAO#{"id": 12}#DELETE_TRANSACAO#
           - Meta: #DELETE_META#{"id": 0}#DELETE_META#
        REGRA: Para editar, NUNCA use #SAVE_...# (isso cria duplicata). Use #UPDATE_...#.
        # REGRAS DE RESPOSTA:
        - Se o usuário pedir um conselho sobre um gasto específico, analise o impacto dele na Meta Financeira.
        - Se o usuário perguntar sobre investimentos, verifique primeiro o 'Perfil de Investidor' no contexto.
        - Se a informação não estiver na base de conhecimento, diga: "Não tenho esses dados específicos no momento, mas com base nos conceitos financeiros gerais, posso te explicar que..."
        """

    def _get_provider(self):
        if self.mode == "local":
            return OllamaProvider()
        elif self.mode == "gemini":
            return GeminiProvider(api_key=self.api_key)
        elif self.mode == "openai":
            return OpenAIProvider(api_key=self.api_key)
        return OllamaProvider()

    async def run(self, user_query: str):
        context = self.retriever.get_relevant_context(user_query)
        full_system_prompt = f"{self.system_prompt_base}\n\n### CONTEXTO ###\n{context}"
        response = await self.provider.generate_response(full_system_prompt, user_query)
        # ROUTER EXTENDIDO
        # CRIAR
        if "#SAVE_TRANSACAO#" in response:
            return self._handle_action(response, "#SAVE_TRANSACAO#", self._save_transaction_action)
        elif "#SAVE_META#" in response:
            return self._handle_action(response, "#SAVE_META#", self._save_goal_action)
        # EDITAR (NOVO)
        elif "#UPDATE_TRANSACAO#" in response:
            return self._handle_action(response, "#UPDATE_TRANSACAO#", self._update_transaction_action)
        elif "#UPDATE_META#" in response:
            return self._handle_action(response, "#UPDATE_META#", self._update_goal_action)

        # DELETAR
        elif "#DELETE_TRANSACAO#" in response:
            return self._handle_action(response, "#DELETE_TRANSACAO#", self._delete_transaction_action)
        elif "#DELETE_META#" in response:
            return self._handle_action(response, "#DELETE_META#", self._delete_goal_action)
        # LEGACY
        elif "#SAVE#" in response:
            return self._handle_action(response, "#SAVE#", self._save_transaction_action)

        return response

    def _handle_action(self, response, tag, action_func):
        """
        Smart Parser: Procura por um bloco JSON válido entre as tags, ignorando
        menções da tag no texto comum.
        """
        try:
            parts = response.split(tag)
            if len(parts) < 3:
                return response

            for i in range(1, len(parts)):
                candidate = parts[i].strip()
                if len(candidate) < 2:
                    continue
                try:
                    data_dict = json.loads(candidate)
                    msg_sistema = action_func(data_dict)
                    pre_text = tag.join(parts[:i]).strip()
                    post_text = tag.join(parts[i+1:]).strip()
                    final_response = f"{pre_text}\n\n_{msg_sistema}_\n\n{post_text}"
                    return final_response.strip()
                except json.JSONDecodeError:
                    continue

            return response

        except Exception as e:
            print(f"Erro Crítico no Router: {e}")
            return f"{response}\n\n❌ *Erro interno ao processar comando.*"

    # ACTION HANDLERS

    def _save_transaction_action(self, data):
        if self.retriever.add_transaction(data["descricao"], data["valor"], data.get("categoria", "Geral")):
            return "✅ Transação registrada."
        return "❌ Erro ao gravar."

    def _save_goal_action(self, data):
        if self.retriever.add_goal(data["descricao"], data.get("valor", data.get("valor_alvo")), data.get("data_limite")):
            return "🎯 Meta criada."
        return "❌ Erro ao gravar."

    def _update_transaction_action(self, data):
        # Remove ID do dict de dados para passar como kwargs limpos
        idx = data.pop("id", None)
        if idx is not None and self.retriever.update_transaction(idx, **data):
            return f"📝 Transação ID {idx} atualizada."
        return "❌ Erro ao atualizar (ID inválido?)."

    def _update_goal_action(self, data):
        idx = data.pop("id", None)
        if idx is not None and self.retriever.update_goal(idx, **data):
            return f"📝 Meta ID {idx} atualizada."
        return "❌ Erro ao atualizar meta."

    def _delete_transaction_action(self, data):
        if self.retriever.delete_transaction(data.get("id")):
            return f"🗑️ Transação ID {data.get('id')} removida."
        return "❌ Erro ao remover."

    def _delete_goal_action(self, data):
        if self.retriever.delete_goal(data.get("id")):
            return f"🗑️ Meta ID {data.get('id')} removida."
        return "❌ Erro ao remover."
