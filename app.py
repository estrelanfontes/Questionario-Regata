from flask import Flask, render_template, request, jsonify
import json
import os
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
import base64
from flask import make_response
import csv
from io import StringIO
# ALTERAÇÃO 1 dia10
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.units import cm, inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
from flask import send_file
import os#

app = Flask(__name__)

# Dados de emissão por transporte (gCO2/km)
EMISSOES_TRANSPORTE = {
    "carro": 9.66,
    "ônibus": 6.7,
    "avião": 4.3,
    "barca": 5.9,
    "bicicleta": 0,
    "moto": 7.5,
    "trem": 2.8,
    "outros": 5.0
}

# NOVO: Lista de tipos de participantes atualizada
TIPOS_PARTICIPANTE = [
    "Velejador/Velejadora",
    "Técnico/Técnica",
    "Acompanhante do atleta", 
    "Comissão de regata",
    "Prestador/Prestadora de serviço",
    "Organização",
    "Outro"
]

# Carregar dados existentes
def carregar_dados():
    if os.path.exists('dados.json'):
        with open('dados.json', 'r') as f:
            return json.load(f)
    return {"respostas": []}

# Salvar dados
def salvar_dados(dados):
    with open('dados.json', 'w') as f:
        json.dump(dados, f, indent=4)

# Gerar gráfico base64 para HTML
def gerar_grafico_base64():
    dados = carregar_dados()
    if not dados["respostas"]:
        return None
    
    # Dados para gráficos - ATUALIZADO para novas categorias
    emissoes_transporte = {transp: 0 for transp in EMISSOES_TRANSPORTE.keys()}
    emissoes_tipo = {tipo: 0 for tipo in TIPOS_PARTICIPANTE}  # NOVO: usa a lista atualizada
    
    for resposta in dados["respostas"]:
        # Emissões por transporte
        transp = resposta["transporte_cidade"]
        if transp in emissoes_transporte:
            emissoes_transporte[transp] += resposta["emissao_total"]
        
        # Emissões por tipo - ATUALIZADO
        tipo = resposta["tipo_participante"]
        if tipo in emissoes_tipo:
            emissoes_tipo[tipo] += resposta["emissao_total"]
    
    # Criar figura com subplots
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(20, 6))  # Aumentado para caber mais categorias
    fig.suptitle('Análise de Emissões de CO2 - Regata', fontsize=16, fontweight='bold')
    
    # Gráfico 1: Emissões por tipo de transporte (Pizza)
    transportes_validos = [t for t in emissoes_transporte.keys() if emissoes_transporte[t] > 0]
    valores_transp = [emissoes_transporte[t] for t in transportes_validos]
    
    if transportes_validos and any(valores_transp):
        cores1 = plt.cm.Set3(np.linspace(0, 1, len(transportes_validos)))
        ax1.pie(valores_transp, labels=transportes_validos, autopct='%1.1f%%', colors=cores1)
        ax1.set_title("Distribuição de Emissões por Tipo de Transporte")
    
    # Gráfico 2: Emissões por tipo de participante (Barras) - ATUALIZADO
    tipos_validos = [t for t in TIPOS_PARTICIPANTE if emissoes_tipo[t] > 0]
    valores_tipos = [emissoes_tipo[t] for t in tipos_validos]
    
    if tipos_validos:
        cores2 = plt.cm.viridis(np.linspace(0, 1, len(tipos_validos)))
        bars = ax2.bar(tipos_validos, valores_tipos, color=cores2)
        ax2.set_title("Emissões por Tipo de Participante")
        ax2.set_ylabel("Emissão de CO2 (g)")
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        for bar, valor in zip(bars, valores_tipos):
            height = bar.get_height()
            if height > 0:  # Só mostra label se valor > 0
                ax2.text(bar.get_x() + bar.get_width()/2., height + 0.05,
                        f'{valor:.2f}g', ha='center', va='bottom', fontsize=8)
    
    # Gráfico 3: Eficiência dos transportes (gCO2/km)
    eficiencias = list(EMISSOES_TRANSPORTE.values())
    transportes_efic = list(EMISSOES_TRANSPORTE.keys())
    
    bars = ax3.bar(transportes_efic, eficiencias, color='#FF9800')
    ax3.set_title("Eficiência de Emissão por Tipo de Transporte")
    ax3.set_ylabel("gCO2 por km")
    ax3.set_xlabel("Tipo de Transporte")
    plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45)
    
    for bar, valor in zip(bars, eficiencias):
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height + 0.05,
                f'{valor:.2f}g', ha='center', va='bottom')
    
    plt.tight_layout()
    
    # Converter gráfico para base64
    buffer = BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    plt.close()
    
    return image_base64

#ATUALIZAÇAO dia10
def emoji_para_imagem(emoji, tamanho=12):
    """Converte emoji em imagem base64"""
    from reportlab.lib.utils import ImageReader
    from io import BytesIO
    import matplotlib.pyplot as plt
    
    try:
        # CORREÇÃO: Agora usando o parâmetro 'tamanho' que estava sem uso
        fig, ax = plt.subplots(figsize=(tamanho/24, tamanho/24))  # Usa 'tamanho'
        ax.text(0.5, 0.5, emoji, fontsize=tamanho, ha='center', va='center')  # Usa 'tamanho'
        ax.axis('off')
        
        # Converter para imagem
        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', 
                   pad_inches=0, transparent=True, dpi=100)
        buffer.seek(0)
        plt.close()
        
        return ImageReader(buffer)
    except:
        return None

def criar_linha_com_emoji(emoji, texto, estilo, tamanho_emoji=12):
    """Cria uma linha com emoji como imagem"""
    from reportlab.platypus import Table, Paragraph, Image
    from reportlab.lib.units import mm
    
    try:
        img_emoji = emoji_para_imagem(emoji, tamanho_emoji)
        if img_emoji:
            # CORREÇÃO: Criar objeto Image em vez de usar ImageReader diretamente
            img_obj = Image(img_emoji, width=4*mm, height=4*mm)
            
            # Criar tabela com imagem e texto
            dados_linha = [
                [img_obj, Paragraph(texto, estilo)]
            ]
            tabela = Table(dados_linha, colWidths=[6*mm, 150*mm])
            tabela.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 2),
                ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ]))
            return tabela
        else:
            # Fallback: texto simples
            return Paragraph(f"• {texto}", estilo)
    except Exception as e:
        print(f"Erro ao criar linha com emoji: {e}")
        return Paragraph(f"• {texto}", estilo)


#ALTERAÇÃO 2
def gerar_pdf(registro):
    """Gera PDF com os resultados do questionário"""
    
    try:
        # Criar buffer para o PDF
        buffer = BytesIO()
        
        # Criar documento
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=A4,
            rightMargin=72, 
            leftMargin=72,
            topMargin=72, 
            bottomMargin=18,
            title=f"Emissão CO2 - {registro['nome']}"
        )
        
        # Container para os elementos do PDF
        elements = []
        styles = getSampleStyleSheet()
        
        # Estilos customizados
        estilo_titulo = ParagraphStyle(
            'TituloPrincipal',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            textColor=colors.HexColor('#2c3e50'),
            alignment=1  # Centralizado
        )
        
        estilo_subtitulo = ParagraphStyle(
            'Subtitulo',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.HexColor('#34495e'),
            borderPadding=5
        )
        
        estilo_normal = ParagraphStyle(
            'NormalCustom',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=6
        )
        
        estilo_destaque = ParagraphStyle(
            'Destaque',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#27ae60'),
            alignment=1
        )

        # ===== CABEÇALHO =====
        titulo = Paragraph("CERTIFICADO DE EMISSÃO DE CARBONO", estilo_titulo)
        elements.append(titulo)
        
        linha_divisoria = Table([[""]], colWidths=[16*cm], rowHeights=[1])
        linha_divisoria.setStyle(TableStyle([
            ('LINEABOVE', (0,0), (-1,-1), 1, colors.HexColor('#3498db')),
            ('LINEBELOW', (0,0), (-1,-1), 1, colors.HexColor('#3498db')),
        ]))
        elements.append(linha_divisoria)
        elements.append(Spacer(1, 20))

        # ===== DADOS DO PARTICIPANTE =====
        elements.append(Paragraph("DADOS DO PARTICIPANTE", estilo_subtitulo))
        
        dados_pessoais = [
            ["Nome:", registro['nome']],
            ["Email:", registro['email']],
            ["Tipo de Participante:", registro['tipo_participante']],
            ["Data do Cálculo:", registro['data']]
        ]
        
        tabela_dados = Table(dados_pessoais, colWidths=[4*cm, 10*cm])
        tabela_dados.setStyle(TableStyle([
            ('FONT', (0,0), (-1,-1), 'Helvetica', 10),
            ('FONT', (0,0), (0,-1), 'Helvetica-Bold', 10),
            ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#ecf0f1')),
            ('TEXTCOLOR', (0,0), (-1,-1), colors.black),
            ('ALIGN', (0,0), (0,-1), 'LEFT'),
            ('ALIGN', (1,0), (1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#bdc3c7')),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        
        elements.append(tabela_dados)
        elements.append(Spacer(1, 25))

        # ===== RESUMO DA EMISSÃO =====
        elements.append(Paragraph("RESUMO DA EMISSÃO", estilo_subtitulo))
        
        # Cálculo detalhado
        emissao_local = EMISSOES_TRANSPORTE.get(registro['transporte_local'], 5.0) * registro['distancia_local'] * registro['dias_evento']
        emissao_principal = registro['emissao_total'] - emissao_local
        
        emissao_total = Paragraph(
            f"<b>TOTAL DE EMISSÕES: {registro['emissao_total']:.2f} gCO2</b>", 
            estilo_destaque
        )
        elements.append(emissao_total)
        elements.append(Spacer(1, 15))

        detalhes_emissao = [
            ["Tipo de Deslocamento", "Transporte", "Distância", "Emissão (gCO2)"],
            [
                "Até a cidade do evento", 
                registro['transporte_cidade'].capitalize(), 
                f"{registro['distancia_cidade']} km", 
                f"{emissao_principal:.2f}"
            ],
            [
                "Deslocamento local", 
                registro['transporte_local'].capitalize(), 
                f"{registro['distancia_local']} km/dia × {registro['dias_evento']} dias", 
                f"{emissao_local:.2f}"
            ],
            ["TOTAL", "", "", f"<b>{registro['emissao_total']:.2f} gCO2</b>"]
        ]
        
        tabela_emissao = Table(detalhes_emissao, colWidths=[5.5*cm, 3*cm, 4*cm, 3.5*cm])
        tabela_emissao.setStyle(TableStyle([
            ('FONT', (0,0), (-1,-1), 'Helvetica', 9),
            ('FONT', (0,0), (-1,0), 'Helvetica-Bold', 10),
            ('FONT', (0,-1), (-1,-1), 'Helvetica-Bold', 10),
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#3498db')),
            ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#27ae60')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('TEXTCOLOR', (0,-1), (-1,-1), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#7f8c8d')),
            ('PADDING', (0,0), (-1,-1), 8),
        ]))
        
        elements.append(tabela_emissao)
        elements.append(Spacer(1, 25))

        # ===== COMPARAÇÕES AMBIENTAIS =====
        elements.append(Paragraph("IMPACTO AMBIENTAL - EQUIVALÊNCIAS", estilo_subtitulo))
        
        arvores = registro['emissao_total'] / 21000  # 1 árvore absorve ~21kg CO2/ano
        km_carro = registro['emissao_total'] / 130   # Carro médio emite ~130g CO2/km
        lâmpadas = registro['emissao_total'] / 450   # 1 lâmpada LED/dia
        
        comparativos = [
            ["Equivalência", "Valor Aproximado"],
            ["Árvores para absorver em 1 ano", f"{arvores:.2f} árvores"],
            ["Quilômetros de carro médio", f"{km_carro:.1f} km"],
            ["Horas de lâmpada LED (60W)", f"{lâmpadas:.1f} horas"],
            ["Emissão diária média brasileira*", "≈ 12.000 gCO2"]
        ]
        
        tabela_comparativo = Table(comparativos, colWidths=[9*cm, 7*cm])
        tabela_comparativo.setStyle(TableStyle([
            ('FONT', (0,0), (-1,-1), 'Helvetica', 9),
            ('FONT', (0,0), (-1,0), 'Helvetica-Bold', 10),
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e67e22')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#d35400')),
            ('PADDING', (0,0), (-1,-1), 8),
        ]))
        
        elements.append(tabela_comparativo)
        elements.append(Spacer(1, 10))
        
        nota = Paragraph(
            "* Baseado na média brasileira de 4.4 toneladas de CO2 per capita/ano",
            ParagraphStyle('Nota', parent=estilo_normal, fontSize=8, textColor=colors.gray)
        )
        elements.append(nota)
        elements.append(Spacer(1, 25))

        # ===== RECOMENDAÇÕES =====
        elements.append(Paragraph("RECOMENDAÇÕES PARA REDUZIR EMISSÕES", estilo_subtitulo))
        
        recomendacoes = [
            "🌱 Prefira transportes públicos ou coletivos para deslocamentos",
            "🚗 Organize caronas solidárias com outros participantes", 
            "🚶 Para distâncias curtas, opte por caminhar ou usar bicicleta",
            "🌳 Compense emissões participando de programas de reflorestamento",
            "🏨 Escolha acomodações próximas ao local do evento",
            "📅 Agende deslocamentos para evitar tráfego intenso",
            "💡 Prefira veículos elétricos ou híbridos quando disponível"
        ]
        
        for rec in recomendacoes:
            elements.append(Paragraph(rec, estilo_normal))
            elements.append(Spacer(1, 6))
        
        elements.append(Spacer(1, 20))

        # ===== RODAPÉ =====
        elements.append(Spacer(1, 10))
        linha_rodape = Table([[""]], colWidths=[16*cm], rowHeights=[1])
        linha_rodape.setStyle(TableStyle([
            ('LINEABOVE', (0,0), (-1,-1), 1, colors.HexColor('#95a5a6')),
        ]))
        elements.append(linha_rodape)
        
        rodape = Paragraph(
            "Calculadora de Emissão de CO2 - Eventos Esportivos Sustentáveis<br/>" +
            "Relatório gerado automaticamente - Juntos por um planeta mais verde!",
            ParagraphStyle(
                'Rodape', 
                parent=estilo_normal, 
                fontSize=9, 
                alignment=1, 
                textColor=colors.HexColor('#7f8c8d'),
                spaceBefore=10
            )
        )
        elements.append(rodape)

        # ===== GERAR PDF =====
        doc.build(elements)
        buffer.seek(0)
        return buffer
        
    except Exception as e:
        print(f"Erro ao gerar PDF: {str(e)}")
        # Fallback: PDF simples em caso de erro
        return gerar_pdf_simples(registro)

def gerar_pdf_simples(registro):
    """Fallback: PDF simples caso a versão detalhada falhe"""
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, 800, "Certificado de Emissão de CO2")
    
    p.setFont("Helvetica", 12)
    p.drawString(100, 770, f"Participante: {registro['nome']}")
    p.drawString(100, 750, f"Email: {registro['email']}")
    p.drawString(100, 730, f"Tipo: {registro['tipo_participante']}")
    
    p.setFont("Helvetica-Bold", 14)
    p.drawString(100, 700, f"Emissão Total: {registro['emissao_total']:.2f} gCO2")
    
    p.setFont("Helvetica", 10)
    p.drawString(100, 670, f"Transporte principal: {registro['transporte_cidade']}")
    p.drawString(100, 650, f"Distância: {registro['distancia_cidade']} km")
    p.drawString(100, 630, f"Transporte local: {registro['transporte_local']}")
    p.drawString(100, 610, f"Dias de evento: {registro['dias_evento']}")
    
    p.drawString(100, 550, "Relatório gerado automaticamente")
    p.drawString(100, 530, "Calculadora de Emissões - Eventos Sustentáveis")
    
    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer#

# Rotas Flask
@app.route('/')
def index():
    return render_template('index.html')

# NOVO: Passa a lista atualizada para o template
@app.route('/questionario')
def questionario():
    return render_template('questionario.html', 
                          transportes=EMISSOES_TRANSPORTE.keys(),
                          tipos_participante=TIPOS_PARTICIPANTE)

@app.route('/submit', methods=['POST'])
def submit():
    # Processar dados do formulário
    dados_form = request.form
    
    # Validar tipo de participante
    tipo_participante = dados_form['tipo_participante']
    if tipo_participante not in TIPOS_PARTICIPANTE:
        tipo_participante = "Outro"  # Fallback seguro
    
    # Calcular emissões
    distancia_principal = float(dados_form['distancia_cidade'])
    transporte_principal = dados_form['transporte_cidade']
    emissao_principal = EMISSOES_TRANSPORTE.get(transporte_principal, 5.0) * distancia_principal
    
    distancia_local = float(dados_form['distancia_local'])
    transporte_local = dados_form['transporte_local']
    dias_evento = int(dados_form['dias_evento'])
    emissao_local = EMISSOES_TRANSPORTE.get(transporte_local, 5.0) * distancia_local * dias_evento
    
    emissao_total = emissao_principal + emissao_local
    
    # Criar registro - ATUALIZADO com nova categoria
    registro = {
        "nome": dados_form['nome'],
        "email": dados_form['email'],
        "tipo_participante": tipo_participante,  # NOVA CATEGORIA
        "transporte_cidade": transporte_principal,
        "distancia_cidade": distancia_principal,
        "transporte_local": transporte_local,
        "distancia_local": distancia_local,
        "dias_evento": dias_evento,
        "emissao_total": emissao_total,
        "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Salvar dados
    dados = carregar_dados()
    dados["respostas"].append(registro)
    salvar_dados(dados)
    
    resposta_id = len(dados["respostas"]) - 1
    
    # Gerar gráfico atualizado
    grafico_base64 = gerar_grafico_base64()
    
    return render_template('resultados.html', 
                          registro=registro, 
                          grafico_base64=grafico_base64,
                          emissoes_transporte=EMISSOES_TRANSPORTE,
                          resposta_id=resposta_id,  #atualização
                          mostrar_download=len(dados["respostas"]) > 0)

@app.route('/dados')
def get_dados():
    dados = carregar_dados()
    return jsonify(dados)

@app.route('/download', methods=['GET'])
def download_dados():
    # Carregar dados
    dados = carregar_dados()
    
    # Criar arquivo CSV em memória
    si = StringIO()
    cw = csv.writer(si)
    
    # Escrever cabeçalho - ATUALIZADO
    cw.writerow(['Nome', 'Email', 'Tipo Participante', 'Transporte até a Cidade', 
                 'Distância até a Cidade (km)', 'Transporte Local', 'Distância Local (km)', 
                 'Dias de Evento', 'Emissão Total (gCO2)', 'Data'])
    
    # Escrever dados
    for resposta in dados["respostas"]:
        cw.writerow([
            resposta['nome'],
            resposta['email'],
            resposta['tipo_participante'],  # NOVA CATEGORIA
            resposta['transporte_cidade'],
            resposta['distancia_cidade'],
            resposta['transporte_local'],
            resposta['distancia_local'],
            resposta['dias_evento'],
            resposta['emissao_total'],
            resposta['data']
        ])
    
    # Preparar resposta para download
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=emissoes_co2_regata.csv"
    output.headers["Content-type"] = "text/csv"
    
    return output

@app.route('/download-json', methods=['GET'])
def download_dados_json():
    # Carregar dados
    dados = carregar_dados()
    
    # Preparar resposta para download
    output = make_response(json.dumps(dados, indent=4, ensure_ascii=False))
    output.headers["Content-Disposition"] = "attachment; filename=emissoes_co2_regata.json"
    output.headers["Content-type"] = "application/json"
    
    return output

#ALTERAÇÃO 3

@app.route('/download-pdf/<int:resposta_id>')
def download_pdf(resposta_id):
    """Faz download do PDF com os resultados"""
    dados = carregar_dados()
    
    if 0 <= resposta_id < len(dados["respostas"]):
        registro = dados["respostas"][resposta_id]
        
        try:
            pdf_buffer = gerar_pdf(registro)
            
            return send_file(
                pdf_buffer,
                as_attachment=True,
                download_name=f"emissao_co2_{registro['nome'].replace(' ', '_')}_{registro['data'][:10]}.pdf",
                mimetype='application/pdf'
            )
        except Exception as e:
            return f"Erro ao gerar PDF: {str(e)}", 500
    else:
        return "Registro não encontrado", 404

@app.route('/download-pdf-ultimo')
def download_pdf_ultimo():
    """Faz download do PDF do último registro"""
    dados = carregar_dados()
    
    if dados["respostas"]:
        registro = dados["respostas"][-1]
        pdf_buffer = gerar_pdf(registro)
        
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=f"emissao_co2_{registro['nome'].replace(' ', '_')}.pdf",
            mimetype='application/pdf'
        )
    else:
        return "Nenhum registro encontrado", 404#


if __name__ == '__main__':
    app.run(debug=True)
