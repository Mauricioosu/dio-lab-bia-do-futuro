import os
import json
from modules.retriever import FinancialRetriever
from modules.providers import OllamaProvider, OpenAIProvider, GeminiProvider

class FinAssistOrchestrator:
    def __init__(self, mode="local", data=None, api_key=None): 
        self.mode = mode
        self.api_key = api_key
        self.data = data 
        # Importante: Definir api_key antes de instanciar o provider
        self.provider = self._get_provider()
        
        # O Retriever agora recebe os dados da sessão ou carrega do disco
        self.retriever = FinancialRetriever(data=self.data)
        
        self.system_prompt_base = """
        Você é o FinAssist Pro, um mentor financeiro inteligente, ético e educativo. você Deve registrar gastos, sugerir investimentos e ajudar no planejamento financeiro. 
        Seu objetivo é ajudar os usuários a organizarem suas finanças e entenderem o mercado financeiro de forma didática.

        DIRETRIZES DE COMPORTAMENTO:
        1. BASE DE VERDADE: Use exclusivamente os dados fornecidos no contexto (Transações, Produtos, Metas e Perfil) para responder.
        2. PRECISÃO MATEMÁTICA: Ao realizar cálculos, descreva a fórmula utilizada.
        3. TOM DE VOZ: Seja consultivo, encorajador e profissional.
        4. SEGURANÇA: Nunca solicite ou aceite senhas e dados sensíveis.

        REGRA DE REGISTRO:
        Se o usuário solicitar o registro de um gasto ou ganho, você deve enviar um valor POSITIVO para Ganho e NEGATIVO para gasto. e por final confirmar a ação no texto e, OBRIGATORIAMENTE, incluir ao final da resposta o seguinte formato:
        #SAVE#{"descricao": "nome do item", "valor": 100.00, "categoria": "Lazer"}#SAVE#
        
        Exemplo: "Com certeza! Registrei sua compra de 150 reais no mercado. #SAVE#{"descricao": "Mercado", "valor": 150.00, "categoria": "Alimentação"}#SAVE#"
        Mantenha sempre esse formato para que o sistema possa identificar e salvar a transação corretamente.
        """

    def _get_provider(self):
        """Seleciona o provedor usando a chave dinâmica da interface."""
        if self.mode == "local":
            return OllamaProvider()
        elif self.mode == "gemini":
            return GeminiProvider(api_key=self.api_key)
        elif self.mode == "openai":
            return OpenAIProvider(api_key=self.api_key)
        return OllamaProvider() # Fallback seguro

    async def run(self, user_query: str):
            context = self.retriever.get_relevant_context(user_query)
            full_system_prompt = f"{self.system_prompt_base}\n\n### CONTEXTO ###\n{context}"
            
            response = await self.provider.generate_response(full_system_prompt, user_query)
            
            # Lógica de interceptação de salvamento
            if "#SAVE#" in response:
                try:
                    # Extrai o conteúdo entre as tags #SAVE#
                    json_str = response.split("#SAVE#")[1]
                    data_to_save = json.loads(json_str)
                    
                    # Executa a gravação física
                    sucesso = self.retriever.add_transaction(
                        descricao=data_to_save["descricao"],
                        valor=data_to_save["valor"],
                        categoria=data_to_save.get("categoria", "Outros")
                    )
                    
                    if sucesso:
                        # Remove a tag técnica da resposta para o usuário não ver o JSON
                        clean_response = response.split("#SAVE#")[0]
                        return f"{clean_response}\n\n✅ *Transação registrada no sistema!*"
                except Exception as e:
                    print(f"Erro no processamento do salvamento: {e}")
            
            return response