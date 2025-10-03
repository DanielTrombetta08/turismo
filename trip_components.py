from crewai import Agent, Task, LLM
from trip_tools import SearchTools, CalculatorTools
from textwrap import dedent
import os
from dotenv import load_dotenv
load_dotenv()

class TripAgents:
    def __init__(self):
        self.gemini = LLM(
            model="gemini/gemini-2.0-flash",
            api_key=os.getenv("GOOGLE_API_KEY"),
        )

    def city_info_agent(self):
        return Agent(
            role="Especialista em informações da cidade",
            goal=dedent(
                """Reunir informações úteis sobre o destino escolhido, com base nos interesses e datas da viagem,
                ajudando viajantes a entender o contexto geral do local."""
            ),
            backstory=dedent(
                """
                Sou um especialista com amplo conhecimento sobre cidades ao redor do mundo,
                capaz de fornecer detalhes atualizados sobre clima, eventos culturais, segurança,
                costumes locais e outros aspectos práticos para quem pretende visitar o local.
                Sou apaixonado por compartilhar as melhores experiências e 'joias escondidas' do local.
                """
            ),
            llm=self.gemini,
            tools=[SearchTools.search_tavily],
            verbose=True,
            max_iter=10,
            allow_delegation=False,
      )

    def logistics_expert_agent(self):
        return Agent(
            role="Especialista em logística de viagem",
            goal="Identificar as melhores opções logísticas para a viagem, com foco em praticidade, custo-benefício e conforto.",
            backstory=dedent(
                """
                Sou um profissional focado em planejar a logística da viagem: transporte, hospedagem e deslocamento local.
                Tenho conhecimento sobre companhias aéreas, apps de mobilidade, regiões seguras para se hospedar e otimização de trajetos.
                """
            ),
            llm=self.gemini,
            tools=[
                SearchTools.search_tavily,
                CalculatorTools.calculate
            ],
            verbose=True,
            max_iter=10,
            allow_delegation=False,
        )

    def itinerary_planner_agent(self):
        return Agent(
            role="Planejador de itinerário personalizado",
            goal="Criar um roteiro completo com base nas preferências do usuário.",
            backstory=dedent(
                """
                Sou um guia profissional apaixonado por viagens, especialista em organização de itinerários personalizados.
                Minha missão é integrar dados sobre clima, atrações, eventos e logística em uma experiência otimizada para o turista.
                """
            ),
            llm=self.gemini,
            tools=[SearchTools.search_tavily],
            verbose=True,
            max_iter=10,
            allow_delegation=False,
        )

    def language_guide_agent(self):
        return Agent(
            role="Especialista em comunicação e etiqueta local",
            goal="Gerar um guia traduzido com frases úteis, dicas de etiqueta e expressões práticas com base nas atividades do roteiro.",
            backstory=dedent(
                """
                Sou um especialista em línguas e culturas do mundo.
                Meu trabalho é ajudar turistas a se comunicarem melhor no destino, traduzindo expressões essenciais relacionadas ao roteiro,
                como pedidos em restaurantes, orientações para transporte e interações cotidianas.
                Também forneço dicas culturais para evitar gafes e tornar a experiência mais fluida e respeitosa.
                """
            ),
            llm=self.gemini,
            tools=[SearchTools.search_tavily],
            verbose=True,
            max_iter=5,
            allow_delegation=False,
        )


class TripTasks:
    def city_info_task(self, agent, from_city, destination_city, interests, date_from, date_to):
        return Task(
            description=dedent(
                f"""
                Levantar informações detalhadas sobre a cidade e coletar dados úteis sobre clima, segurança e costumes locais.
                Identificar marcos culturais, pontos históricos, locais de entretenimento, experiências gastronômicas e quaisquer atividades que se alinhem às preferências do usuário.
                Também destacar eventos e festivais sazonais que podem ser de interesse durante a visita do viajante.
                Use as ferramentas disponíveis para buscar fontes atualizadas e confiáveis.
                Retorne em português.

                Viajando de: {from_city}
                Para: {destination_city}
                Interesses do viajante: {interests}
                Chegada: {date_from}
                Partida: {date_to}

                Seja criterioso, como se estivesse ajudando alguém a ter uma experiência inesquecível.
                """
            ),
            expected_output=dedent(
                f"""
                Um guia detalhado (em formato markdown) em português que inclui:
                - Resumo da cidade e sua cultura;
                - Uma lista selecionada de lugares recomendados para visitar e eventos (se houver);
                - Um detalhamento das despesas diárias, como custos médios com alimentação;
                - Recomendações de segurança;
                - Dicas de costumes locais;
                """
            ),
            agent=agent,
            output_file='relatorio_local.md',
        )

    def plan_logistics_task(self, context, agent, destination_city, interests, date_from, date_to):
        return Task(
            description=dedent(
                f"""
                Planejar a logística da viagem.
                Identificar as melhores opções de hospedagem, voos e transporte local considerando:

                Destino: {destination_city}
                Data de chegada: {date_from}
                Data de partida: {date_to}
                Interesses: {interests}

                Avalie preço, localização, conveniência e segurança.
                Retorne em português.
                """
            ),
            expected_output=dedent(
                f"""
                Relatório em português (em formato markdown):
                - Sugestão de hospedagens, preferencialmente com localização estratégica;
                - Opções de voos ou meios de transporte para chegada/partida;
                - Sugestões de deslocamento dentro da cidade;
                - Estimativas de custo para cada item;
                """
            ),
            context=context,
            agent=agent,
            output_file='relatorio_logistica.md',
        )

    def build_itinerary_task(self, context, agent, destination_city, interests, date_from, date_to):
        return Task(
            description=dedent(
                f"""
                Esta tarefa sintetiza todas as informações para criar o roteiro final da viagem.
                Com base nas informações dos outros agentes, desenvolva um itinerário detalhado.
                Cada dia deve conter atividades, clima, transporte, refeições e estimativa de gastos.
                Retorne em português.

                Destino: {destination_city}
                Interesses: {interests}
                Data de chegada: {date_from}
                Data de partida: {date_to}
                """
            ),
            expected_output=dedent("""
                Documento em português que inclui (em formato markdown):
                - Boas vindas e apresentação da cidade em até 2 parágrafos.
                - Programação diária com sugestões de horários e atividades
                - Atrações distribuídas por região e logística
                - Clima previsto, sugestões de transporte e alimentação
                - Eventos e festivais sazonais (se houver)
                - Estimativa de gastos por dia, custo médio das despesas diárias e pontos turísticos.
                - Visão geral dos destaques da cidade com base nas recomendações do guia.
                - Outras dicas e informações adicionais para uma viagem e estadia tranquila.
                """),
            context=context,
            agent=agent,
            output_file='roteiro_viagem.md',
        )


    def language_guide_task(self, context, agent, destination_city):
        return Task(
            description=dedent(
                f"""
                Com base no destino ({destination_city}) e nas atividades previstas no roteiro, monte um guia traduzido com frases úteis e dicas culturais.
                Deve ser no idioma falado nesse local (ou também em inglês, caso seja uma língua aceitável para ser usada por turistas nesse local).

                Inclua expressões comuns para situações que podem ser úteis, como:
                - Interações em restaurantes (como fazer pedidos, pagar a conta, pedir recomendações);
                - Deslocamento (perguntar por rotas, chamar transporte, entender sinalização);
                - Situações cotidianas (compras, pedidos de ajuda, saudações e agradecimentos);
                - Dicas de etiqueta local que o turista deve saber (gestos, hábitos, regras sociais).

                Use linguagem clara e educativa.

                Considere o seguinte roteiro de viagem:
                '{context}'
                """
            ),
            expected_output=dedent(
                """
                Um mini-guia em português contendo:
                - Lista de frases traduzidas organizadas por situação (restaurantes, transporte, compras, etc.);
                - Dicas de etiqueta e costumes locais;
                - Sugestões de como pronunciar corretamente (quando aplicável);
                - Recomendações práticas para comunicação eficaz no destino.
                """
            ),
            agent=agent,
            output_file='guia_comunicacao.md',
        )

