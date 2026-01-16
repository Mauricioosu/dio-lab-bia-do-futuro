import pandas

class FinanceEngine:
    @staticmethod
    def calcular_progresso_meta(valor_atual, valor_alvo):
        """Calcula a porcentagem de conclusão de uma meta."""
        if valor_alvo <= 0: return 0
        progresso = (valor_atual / valor_alvo) * 100
        formula = f"({valor_atual} / {valor_alvo}) * 100"
        return round(progresso, 2), formula

    @staticmethod
    def simular_poupanca(montante_inicial, aporte_mensal, taxa_anual, meses):
        """Simulação de juros compostos para planejamento de metas."""
        taxa_mensal = (1 + taxa_anual)**(1/12) - 1
        total = montante_inicial * (1 + taxa_mensal)**meses + \
                aporte_mensal * (((1 + taxa_mensal)**meses - 1) / taxa_mensal)
        formula = "M = P(1+i)^n + PMT[((1+i)^n - 1) / i]"
        return round(total, 2), formula

    @staticmethod
    def analisar_gastos(df_transacoes):
        """Identifica 'ralos de dinheiro' conforme estratégia de Análise Prática."""
        # Filtra apenas categorias 'Supérfluo' conforme tags de prioridade
        gastos_categoria = df_transacoes.groupby('categoria')['valor'].sum()
        return gastos_categoria.to_dict()