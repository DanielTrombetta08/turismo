# -*- coding: utf-8 -*-
from crewai import Crew, Process
from trip_components import TripAgents, TripTasks
from trip_utils import capture_output
import os
import streamlit as st
import time
import markdown2
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.units import cm
import shutil
from datetime import datetime

# Diretório de saída
OUTPUT_DIR = os.path.join(os.getcwd(), "viagem")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Arquivos a gerar
files = {
    "roteiro_viagem.md": "roteiro_viagem.pdf",
    "guia_comunicacao.md": "guia_comunicacao.pdf",
    "relatorio_local.md": "relatorio_local.pdf",
    "relatorio_logistica.md": "relatorio_logistica.pdf"
}

# Configurações Streamlit
st.set_page_config(page_title="Planejamento de Viagens", page_icon="🌍")
st.title("🌍 Planejamento de Viagens")

# --------------------- CLASSE DE EXECUÇÃO DA VIAGEM ---------------------
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
            agents=[city_info_agent, logistics_expert_agent, itinerary_planner_agent, language_guide_agent],
            tasks=[city_info, plan_logistics, build_itinerary, language_guide],
            process=Process.sequential,
            full_output=True,
            max_rpm=15,
            verbose=False
        )

        return crew.kickoff()

# --------------------- FUNÇÕES AUXILIARES ---------------------
def load_markdown(file_path):
    """Carrega o markdown de um arquivo"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().replace("```markdown", "").replace("```", "")
            return content
    except Exception as e:
        print(f"Erro ao carregar arquivo: {str(e)}")
        return None

def convert_md_to_pdf(file_md, file_pdf, title="Guia de Viagem"):
    # Carrega markdown
    text_md = load_markdown(file_md)
    if text_md is None:
        return

    # Cria documento
    doc = SimpleDocTemplate(file_pdf, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)

    elements = []

    # Estilos customizados
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='CustomTitle', fontSize=20, leading=24, spaceAfter=16, textColor=colors.HexColor('#004080')))
    styles.add(ParagraphStyle(name='CustomHeading2', fontSize=16, leading=20, spaceAfter=12, textColor=colors.HexColor('#004080')))
    styles.add(ParagraphStyle(name='CustomBodyText', fontSize=12, leading=16, spaceAfter=8))
    styles.add(ParagraphStyle(name='CustomBullet', fontSize=12, leading=16, leftIndent=20, bulletIndent=10))
    styles.add(ParagraphStyle(name='CustomBox', fontSize=12, leading=16, backColor=colors.HexColor('#e6f0ff'), borderPadding=6, spaceAfter=10))

    # Adiciona título principal
    elements.append(Paragraph(title, styles['CustomTitle']))
    elements.append(Spacer(1,12))

    # Quebra o markdown em linhas
    lines = text_md.split('\n')
    buffer_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            if buffer_lines:
                elements.append(Paragraph(' '.join(buffer_lines), styles['CustomBodyText']))
                buffer_lines = []
            elements.append(Spacer(1,6))
            continue
        if line.startswith('###'):
            if buffer_lines:
                elements.append(Paragraph(' '.join(buffer_lines), styles['CustomBodyText']))
                buffer_lines = []
            elements.append(Paragraph(line[3:].strip(), styles['CustomHeading2']))
        elif line.startswith('##'):
            if buffer_lines:
                elements.append(Paragraph(' '.join(buffer_lines), styles['CustomBodyText']))
                buffer_lines = []
            elements.append(Paragraph(line[2:].strip(), styles['CustomHeading2']))
        elif line.startswith('#'):
            if buffer_lines:
                elements.append(Paragraph(' '.join(buffer_lines), styles['CustomBodyText']))
                buffer_lines = []
            elements.append(Paragraph(line[1:].strip(), styles['CustomTitle']))
        elif line.startswith('- '):
            if buffer_lines:
                elements.append(Paragraph(' '.join(buffer_lines), styles['CustomBodyText']))
                buffer_lines = []
            elements.append(Paragraph(line[2:].strip(), styles['CustomBullet'], bulletText='•'))
        else:
            buffer_lines.append(line)

    # Adiciona qualquer buffer restante
    if buffer_lines:
        elements.append(Paragraph(' '.join(buffer_lines), styles['CustomBodyText']))

    # Exemplo de tabela estilizada
    table_data = [['Item', 'Detalhes', 'Custo Estimado']]
    table_style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#004080')),
        ('TEXTCOLOR',(0,0),(-1,0),colors.white),
        ('ALIGN',(0,0),(-1,-1),'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 12),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('BACKGROUND',(0,1),(-1,-1),colors.HexColor('#e6f0ff')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
    ])
    table = Table(table_data, style=table_style, hAlign='LEFT')
    elements.append(Spacer(1,12))
    elements.append(table)

    # Gera PDF
    doc.build(elements)

# --------------------- FORMULÁRIO STREAMLIT ---------------------
with st.form("trip_form"):
    st.subheader("Informe os detalhes da sua viagem")
    from_city = st.text_input("Cidade de origem:")
    destination_city = st.text_input("Cidade de destino:")
    col1, col2 = st.columns(2)
    with col1:
        date_from = st.date_input("Data de partida:")
    with col2:
        date_to = st.date_input("Data de retorno:")
    interests = st.text_area("Interesses e preferências:", placeholder="Ex: viagem romântica, museus, gastronomia local...")
    submitted = st.form_submit_button("Gerar roteiro")

# --------------------- EXECUÇÃO DO ROTEIRO ---------------------
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
                status.update(label="Ocorreu um erro", state="error")
                st.error(f"Erro: {str(e)}")
                st.stop()

        # Converter markdowns para PDF
        for md_file, pdf_file in files.items():
            convert_md_to_pdf(md_file, os.path.join(OUTPUT_DIR, pdf_file))

        st.toast("Arquivos PDFs salvos no diretório", icon="✅")

        # Mover os MDs para pasta
        for src_file in files.keys():
            if os.path.exists(src_file):
                shutil.move(src_file, os.path.join(OUTPUT_DIR, src_file))

# --------------------- EXIBIÇÃO DE RELATÓRIOS ---------------------
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

# --------------------- LINKS DE DOWNLOAD E ABERTURA ---------------------
st.subheader("📂 Seus PDFs gerados")
for md_file, pdf_file in files.items():
    pdf_path = os.path.join(OUTPUT_DIR, pdf_file)
    if os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
            st.download_button(
                label=f"⬇️ Baixar {pdf_file}",
                data=pdf_bytes,
                file_name=pdf_file,
                mime="application/pdf"
            )
        st.markdown(f"[📄 Abrir {pdf_file}](viagem/{pdf_file})", unsafe_allow_html=True)
