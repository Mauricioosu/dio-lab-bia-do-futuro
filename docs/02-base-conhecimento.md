# Base de Conhecimento

## Dados Utilizados

| Arquivo | Formato | Utilização no Agente |
|---------|---------|---------------------|
| `historico_atendimento.csv` | CSV | Contextualização: Permite que o agente dê continuidade ao atendimento, lembrando de dúvidas anteriores. |
| `perfil_investidor.json` | JSON | Personalização: Ajusta a linguagem e o risco das sugestões ao nível de tolerância do cliente. |
| `produtos_financeiros.json` | JSON | Base Didática: Fornece os detalhes técnicos (taxas, prazos) dos investimentos para ensinar o usuário. |
| `transacoes.csv` | CSV | Análise Prática: Permite identificar padrões de consumo e diagnosticar "ralos de dinheiro". |
| `objetivos_financeiros.json` | JSON | Planejamento: Define as metas do usuário, permitindo que a IA crie planos de ação personalizados para alcançá-las. |

---

## Adaptações nos Dados

- Os dados originais foram expandidos para incluir metadados de risco e liquidez nos produtos financeiros. No arquivo de transações, foram adicionadas "tags de prioridade" (Essencial vs. Supérfluo). Além disso, o arquivo de objetivos financeiros foi estruturado para incluir prazos e valores alvo, permitindo que o agente calcule a viabilidade das metas em relação ao saldo atual.

---

## Estratégia de Integração

### Como os dados são carregados?

- O agente utiliza a biblioteca Pandas para carregar os arquivos CSV e a biblioteca nativa json do Python para os arquivos estruturados. O carregamento ocorre no momento em que a sessão do chat é iniciada (@cl.on_chat_start). Os dados são armazenados na user_session do Chainlit para acesso rápido sem a necessidade de re-leitura do disco a cada mensagem.

### Como os dados são usados no prompt?

- Os dados são consultados dinamicamente através de uma função de recuperação (RAG). Quando o usuário faz uma pergunta, o Orquestrador filtra as informações relevantes (ex: busca metas de curto prazo se o usuário falar sobre "comprar algo logo") e injeta esses dados no System Prompt. Isso garante que a IA tenha uma "Base de Verdade" para realizar cálculos e dar conselhos sem alucinar.

---

## Exemplo de Contexto Montado

```
### PERFIL DO CLIENTE ###
- Nome: Mauricio
- Perfil: Moderado (Aceita riscos baixos para maior rentabilidade)
- Saldo em conta: R$ 4.250,00

### METAS ATIVAS ###
- Meta: Reserva de Emergência | Alvo: R$ 10.000,00 | Progresso: 42%

### RESUMO DE GASTOS RECENTES ###
- Categoria 'Lazer': R$ 850,00 (Acima da média de R$ 400,00)
- Categoria 'Essencial': R$ 2.100,00

### PRODUTOS PARA SUGESTÃO (BASE DIDÁTICA) ###
- CDB Liquidez Diária: 100% do CDI | Risco: Baixo
- Tesouro IPCA+: Inflação + 6% | Risco: Médio
...
