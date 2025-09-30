from crewai import Crew, Process
from trip_components import TripAgents, TripTasks
from trip_utils import capture_output
from textwrap import dedent
import os
import streamlit as st
import time
import markdown2
from weasyprint import HTML
import io
from datetime import datetime
import shutil

OUTPUT_DIR = os.path.join(os.getcwd(), "viagem")
os.makedirs(OUTPUT_DIR, exist_ok=True)

files = {
    "roteiro_viagem.md": "roteiro_viagem.pdf",
    "guia_comunicacao.md": "guia_comunicacao.pdf",
    "relatorio_local.md": "relatorio_local.pdf",
    "relatorio_logistica.md": "relatorio_logistica.pdf"
}

# Configurações Streamlit
st.set_page_config(page_title="Planejamento de Viagens", page_icon="🌍")
st.title("🌍 Planejamento de Viagens")

class TripCrew:
  def __init__(self, from_city, destination_city, date_from, date_to, interests):
    self.from_city = from_city
    self.destination_city = destination_city
    self.date_from = date_from
    self.date_to = date_to
    self.interests = interests

  def run(self):
    agents = TripAgents()
    tasks = TripTasks()

    city_info_agent = agents.city_info_agent()
    logistics_expert_agent = agents.logistics_expert_agent()
    itinerary_planner_agent = agents.itinerary_planner_agent()
    language_guide_agent = agents.language_guide_agent()

    city_info = tasks.city_info_task(
        city_info_agent,
        self.from_city,
        self.destination_city,
        self.interests,
        self.date_from,
        self.date_to
    )

    plan_logistics = tasks.plan_logistics_task(
        [city_info],
        logistics_expert_agent,
        self.destination_city,
        self.interests,
        self.date_from,
        self.date_to
    )

    build_itinerary = tasks.build_itinerary_task(
        [city_info, plan_logistics],
        itinerary_planner_agent,
        self.destination_city,
        self.interests,
        self.date_from,
        self.date_to
    )

    language_guide = tasks.language_guide_task(
        [build_itinerary],
        language_guide_agent,
        self.destination_city
    )

    crew = Crew(
        agents=[
            city_info_agent,
            logistics_expert_agent,
            itinerary_planner_agent,
            language_guide_agent
        ],
        tasks=[city_info, plan_logistics, build_itinerary, language_guide],
        process=Process.sequential,
        full_output=True,
        max_rpm=15,
        verbose=True
    )

    return crew.kickoff()

# Função de carregamento do markdown
def load_markdown(file_path):
  try:
    with open(file_path, 'r', encoding='utf-8') as file:
      content = file.read()
      content = content.replace("```markdown", "").replace("```", "")
      return content
  except Exception as e:
    print(f"Erro ao carregar arquivo: {str(e)}")
    return None

# Função de conversão para PDF
def convert_md_to_pdf(file_md, file_pdf):
  text_md = load_markdown(file_md)
  if text_md is not None:
    html_body = markdown2.markdown(text_md)
    style_css = """
    <style>
        body {
            font-family: Arial, Helvetica, sans-serif; font-size: 12pt; line-height: 1.5;
        }
    </style>
    """
    full_html = f"<html><head>{style_css}</head><body>{html_body}</body></html>"
    HTML(string=full_html).write_pdf(file_pdf)

with st.form("trip_form"):
  st.subheader("Informe os detalhes da sua viagem")
  from_city = st.text_input("Cidade de origem:")
  destination_city = st.text_input("Cidade de destino:")
  col1, col2 = st.columns(2)
  with col1:
    date_from = st.date_input("Data de partida:")
  with col2:
    date_to = st.date_input("Data de retorno:")
  interests = st.text_area("Interesses e preferências:", placeholder = "Ex: viagem romântica, museus, gastronomia local...")
  submitted = st.form_submit_button("Gerar roteiro")

if submitted:
  date_from_str = date_from.strftime("%d de %B de %Y")
  date_to_str = date_to.strftime("%d de %B de %Y")

  if not (from_city and destination_city and date_from and date_to and interests):
    st.warning("Por favor, preencha todos os campos do formulário")
  else:
    with st.status("Montando seu roteiro... Isso pode levar alguns instantes...") as status:
      try:
        process_container = st.container(height=300, border=True)
        output_container = process_container.container()

        with capture_output(output_container) as container_content:
          trip_crew = TripCrew(from_city, destination_city, date_from_str, date_to_str, interests)
          result = trip_crew.run()
          status.update(label="✅ Roteiro gerado com sucesso!", state="complete", expanded=False)
      except Exception as e:
        status.update(label="Ocorreu um erro", state = "error")
        st.error(f"Erro: {str(e)}")
        st.stop()

    for md_file, pdf_file in files.items():
      convert_md_to_pdf(md_file, os.path.join(OUTPUT_DIR, pdf_file))

    st.toast("Arquivos PDFs salvos no diretório", icon="✅")

    for src_file in files.keys():
      if os.path.exists(src_file):
        shutil.move(src_file, os.path.join(OUTPUT_DIR, src_file))

files_md = [md for md in files if os.path.exists(os.path.join(OUTPUT_DIR, md))]
if len(files_md) == len(files):
  if not submitted:
    st.info("Exibindo relatórios da geração anterior")
  tab1, tab2, tab3, tab4 = st.tabs(["🗺️ Roteiro de Viagem", "📖 Guia de Comunicação", "📍 Relatório Cidade", "✈️ Relatório Logística"])
  with tab1:
    st.markdown(load_markdown(os.path.join(OUTPUT_DIR, "roteiro_viagem.md")))
  with tab2:
    st.markdown(load_markdown(os.path.join(OUTPUT_DIR, "guia_comunicacao.md")))
  with tab3:
    st.markdown(load_markdown(os.path.join(OUTPUT_DIR, "relatorio_local.md")))
  with tab4:
    st.markdown(load_markdown(os.path.join(OUTPUT_DIR, "relatorio_logistica.md")))
