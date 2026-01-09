import os
from flask import Flask, render_template, request, jsonify, send_file
from datetime import datetime
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from flask import make_response
import csv
from io import StringIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.lib.units import cm, mm

# Configuração ROBUSTA com fallback
from flask_sqlalchemy import SQLAlchemy



# Dicionário de traduções (adicionar após as outras constantes)
# NO app.py, atualize o dicionário TRANSLATIONS:
TRANSLATIONS = {

        # Títulos do PDF
    "DADOS DO PARTICIPANTE": "PARTICIPANT DATA",
    "RESUMO DA EMISSÃO": "EMISSIONS SUMMARY", 
    "IMPACTO AMBIENTAL - EQUIVALÊNCIAS": "ENVIRONMENTAL IMPACT - EQUIVALENCES",
    "RECOMENDAÇÕES PARA REDUZIR EMISSÕES": "RECOMMENDATIONS TO REDUCE EMISSIONS",
    
    # Textos da tabela
    "Tipo de Deslocamento": "Trip Type",
    "Transporte": "Transport",
    "Distância": "Distance",
    "Emissão (gCO2)": "Emissions (gCO2)",
    "Até a cidade do evento": "To the event city",
    "Deslocamento local": "Local commute",
    "TOTAL": "TOTAL",
    
    # Recomendações do PDF
    "Escolha acomodações próximas ao local do evento, reduzindo a necessidade de transporte motorizado": 
        "Choose accommodations close to the event venue, reducing the need for motorized transport",
    "Para distâncias curtas, opte por caminhar ou pedalar, formas ativas e sustentáveis de locomoção que também favorecem a saúde e o bem-estar":
        "For short distances, choose walking or cycling, active and sustainable forms of mobility that also promote health and well-being",
    "Prefira transportes públicos ou coletivos para deslocamentos sempre que possível":
        "Prefer public or collective transportation whenever possible",
    "Organize caronas solidárias com outros participantes, otimizando o uso dos veículos e diminuindo o número de deslocamentos individuais":
        "Organize carpooling with other participants, optimizing vehicle use and reducing the number of individual trips",
    "Planeje seus deslocamentos com antecedência para evitar horários de tráfego intenso e, consequentemente, o aumento do consumo de combustível":
        "Plan your trips in advance to avoid peak traffic times and consequently reduce fuel consumption",
    "Dê preferência a veículos elétricos ou híbridos, quando disponíveis, para minimizar o impacto ambiental dos deslocamentos":
        "Prefer electric or hybrid vehicles when available to minimize the environmental impact of travel",
    "Compense emissões participando de programas de reflorestamento ou outras iniciativas ambientais reconhecidas":
        "Compensate emissions by participating in reforestation programs or other recognized environmental initiatives",
    
    # Comparações ambientais
    "Equivalência": "Equivalence",
    "Valor Aproximado": "Approximate Value",
    "Árvores para absorver em 1 ano": "Trees to absorb in 1 year",
    "Horas de lâmpada LED (60W)": "Hours of LED bulb (60W)",
    "Emissão diária média brasileira*": "Average daily Brazilian emission*",
    "Baseado na média brasileira de 4.4 toneladas de CO2 per capita/ano": 
        "Based on the Brazilian average of 4.4 tons of CO2 per capita/year",

    # ========== MENU / TÍTULOS ==========
    "Calculadora de Emissões de CO₂ em Deslocamentos para Eventos Náuticos": 
        "CO₂ Emissions Calculator for Travel to Nautical Events",
    "Faça a diferença pelo planeta": "Make a difference for the planet",
    "Ao preencher o questionário, nossa calculadora conseguirá estimar suas emissões de carbono nos deslocamentos": 
        "By filling out the questionnaire, our calculator can estimate your carbon emissions from travel",
    "Iniciar Questionário": "Start Questionnaire",
    
    # ========== CARTÕES DA PÁGINA INICIAL ==========
    "Por que calcular?": "Why calculate?",
    "O transporte é responsável por cerca de 24% das emissões globais de CO2. Suas escolhas fazem diferença!": 
        "Transportation accounts for about 24% of global CO2 emissions. Your choices matter!",
    "Como funciona?": "How does it work?",
    "Responda algumas perguntas sobre seus deslocamentos e veja gráficos em tempo real": 
        "Answer some questions about your travel and see real-time graphs",
    "Participe da mudança": "Join the change",
    "Seus dados ajudam a entender padrões e promover eventos mais sustentáveis": 
        "Your data helps understand patterns and promote more sustainable events",
    
    # ========== RODAPÉ ==========
    "Uma iniciativa da parceria entre CBVela e ETTA/UFF com o apoio do CNPq e Faperj para promover a conscientização ambiental em eventos esportivos": 
    "An initiative of the partnership between CBVela and ETTA/UFF with support from CNPq and Faperj to promote environmental awareness in sporting events",
    
    # ========== QUESTIONÁRIO (adicione estas) ==========
    "Questionário - Emissão de CO2": "Questionnaire - CO2 Emissions",
    "Questionário de Emissão de CO2": "CO2 Emission Questionnaire",
    "Preencha as informações sobre seus deslocamentos para o evento esportivo": 
    "Please enter your travel details for the sporting event",
    "Informações Pessoais": "Personal Information",
    "Estado de Origem:": "Home State:",
    "Selecione seu estado de origem": " --Select your home state",
    "Selecione 'Não se aplica' caso seja de outro país": "Select 'Does not apply' if you are from another country",
    "Tipo de Participante:": "Participant Type:",
    "Selecione seu tipo de participação": "Select your role",
    "Email:": "Email:",
    
    # ========== TIPOS DE TRANSPORTE ==========
    "Carro": "--Car",
    "Ônibus": "--Bus",
    "Avião": "--Plane",
    "Barca": "--Ferry",
    "Bicicleta/A pé": "--Bicycle/Walking",
    "Moto": "--Motorcycle",
    "Trem": "--Train",
    "Outros": "--Other",
    
    # ========== TIPOS DE PARTICIPANTE ==========
    "Velejador(a)": "--Sailor",
    "Técnico/Técnica": "--Coach",
    "Acompanhante do atleta": "--Athlete Guest ",
    "Comissão de regata": "--Race Committee",
    "Prestador/Prestadora de serviço": "--Service provider",
    "Organização": "--Staff",
    "Outro": "--Other",
    
    # ========== SEÇÕES DO QUESTIONÁRIO ==========
    "Deslocamento da sua residência até o local de hospedagem durante a participação no evento": 
        "Travel from home to your accommodation for the event",
    "(Caso você resida nas proximidades do evento e não tenha realizado viagem, selecione 'Outros' e insira 'zero' na distância percorrida.)": 
        "(If you live locally and did not travel to the host city, select 'Other' and enter 'zero' for the distance)",
    "Principal meio de transporte utilizado:": "Primary Mode of transport:",
    "Selecione...": "Select...",
    "Distância média total percorrida (ida e volta, em km):": 
        "Average total distance traveled (round trip, in km):",
    
    "Trajeto diário durante o evento (casa/hospedagem - clube - casa/hospedagem).": 
        "Daily commute during event (home/accommodation - club - home/accommodation)",
    "Distância média percorrida por dia (ida e volta, em km):": 
        "Average daily distance (round trip, in km):",
    "Quantidade de dias em que realizou esse percurso:": 
        "Number of days with this commute:",
    
    "Calcular Emissão": "Calculate Emissions",
    "Voltar para a página inicial": "Back to home page",
    
    # ========== PÁGINA DE RESULTADOS ==========
    "Resultados - Emissão de CO2": "Results - CO2 Emissions",
    "Resultados da Sua Emissão de CO2": "Your CO2 Emissions Results",
    "Veja o impacto ambiental dos seus deslocamentos": 
        "See the environmental impact of your travel",
    
    "Resumo da Sua Emissão": "Your Emissions Summary",
    "Total de emissões de carbono": "Total carbon emissions",
    
    "Detalhes:": "Details:",
    "Local de Origem:": "Origin:",
    "Tipo:": "Type:",
    "Transporte até a cidade:": "Transport to city:",
    "Transporte local:": "Local transport:",
    "Dias de evento:": "Event days:",
    "Data:": "Date:",
    "Estrangeiro": "International",
    
    "O que isso significa?": "What does this mean?",
    "Sua emissão de": "Your emission of",
    "g CO2 equivale a:": "g CO2 equals:",
    "árvores absorvendo CO2 por um ano": "trees absorbing CO2 for one year",
    
    "Estatísticas Coletivas": "Collective Statistics",
    "Gráficos atualizados com todas as respostas recebidas:": 
        "Updated graphs with all received responses:",
    
    "Dicas para Reduzir Sua Emissão:": "Tips to Reduce Your Emissions:",
    "Prefira transportes públicos sempre que possível": 
        "Prefer public transportation whenever possible",
    "Considere a carona solidária para eventos": 
        "Consider carpooling for events",
    "Para distâncias curtas, use bicicleta ou caminhe": 
        "For short distances, use bicycle or walk",
    "Compense suas emissões com programas de reflorestamento": 
        "Compensate your emissions with reforestation programs",
    
    "Realizar Novo Cálculo": "Perform New Calculation",
    "Página Inicial": "Home Page",
    "Baixar Informações PDF": "Download PDF Report",
    
    "Juntos podemos promover eventos esportivos mais sustentáveis!": 
        "Together we can promote more sustainable sporting events!",
    
    # ========== TEXTOS DO PDF ==========
    "Cada Deslocamento Conta: Seu Impacto em CO2 no Evento": 
    "Every Trip Counts: Your CO2 Impact at the Event",
    "Relatório gerado automaticamente": "Report automatically generated",
    "Calculadora de Emissões - Eventos Sustentáveis": 
        "Emissions Calculator - Sustainable Events",


    "Não se aplica (estrangeiro)": "Not applicable (international)",
    

    "País de Origem:": "Country of Origin:",
    "Selecione seu país de origem": " --Select your country of origin",
    "País": "Country",
    "País de Origem": "Country of Origin",
    "Estrangeiro": "International",

    "Abrir Google Maps": "Open Google Maps",
}

def get_translations(texto, translations_dict=TRANSLATIONS):
    """Retorna um dicionário com ambas as línguas"""
    return {
        'pt': texto,  # Texto original em português
        'en': translations_dict.get(texto, texto)  # Tradução em inglês
    }

def traduzir(texto, translations_dict=TRANSLATIONS):
    """Função de compatibilidade para o código do PDF - retorna apenas inglês"""
    return translations_dict.get(texto, texto)

app = Flask(__name__)

#Etapa Render
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # PRODUÇÃO (Render) - Converte postgres:// para postgresql:// se necessário
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    print(f"✅ Usando PostgreSQL: {database_url.split('@')[1] if '@' in database_url else database_url}")
else:
    # DESENVOLVIMENTO (Local) - Tenta .env, depois fallback para SQLite
    try:
        from dotenv import load_dotenv
        load_dotenv()
        env_db_url = os.environ.get('DATABASE_URL')
        if env_db_url:
            app.config['SQLALCHEMY_DATABASE_URI'] = env_db_url
            print("✅ .env carregado com sucesso")
        else:
            app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///calculadora_co2.db'
            print("✅ Usando SQLite (fallback)")
    except Exception as e:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///calculadora_co2.db'
        print(f"⚠️  Erro .env: {e}, usando SQLite")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
# SEU MODELO ORIGINAL (mantenha igual)
class RespostaEmissao(db.Model):
    __tablename__ = 'respostas_emissao'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False)
    pais_origem_pt = db.Column(db.String(100), nullable=False)  # Nome em português
    pais_origem_en = db.Column(db.String(100), nullable=False)  # Nome em inglês
    estado_origem = db.Column(db.String(100), nullable=False)
    tipo_participante = db.Column(db.String(50), nullable=False)
    transporte_cidade = db.Column(db.String(50), nullable=False)
    distancia_cidade = db.Column(db.Numeric(10, 2), nullable=False)
    transporte_local = db.Column(db.String(50), nullable=False)
    distancia_local = db.Column(db.Numeric(10, 2), nullable=False)
    dias_evento = db.Column(db.Integer, nullable=False)
    emissao_total = db.Column(db.Numeric(10, 2), nullable=False)
    data_registro = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'pais_origem_pt': self.pais_origem_pt,
            'pais_origem_en': self.pais_origem_en,
            'estado_origem': self.estado_origem,
            'tipo_participante': self.tipo_participante,
            'transporte_cidade': self.transporte_cidade,
            'distancia_cidade': float(self.distancia_cidade),
            'transporte_local': self.transporte_local,
            'distancia_local': float(self.distancia_local),
            'dias_evento': self.dias_evento,
            'emissao_total': float(self.emissao_total),
            'data': self.data_registro.strftime("%Y-%m-%d %H:%M:%S")
        }

# Dados de emissão por transporte (gCO2/km)
EMISSOES_TRANSPORTE = {
    "Carro": 96.6,
    "Ônibus": 67,
    "Avião": 43,
    "Barca": 59,
    "Bicicleta/A pé": 0,
    "Moto": 80.5,
    "Trem": 21,
    "Outros": 50
}

# Lista de tipos de participantes
TIPOS_PARTICIPANTE = [
    "Velejador/Velejadora",
    "Técnico/Técnica",
    "Acompanhante do atleta", 
    "Comissão de regata",
    "Prestador/Prestadora de serviço",
    "Organização",
    "Outro"
]

# Lista de estados brasileiros + opção para estrangeiros
ESTADOS_BRASIL = [
    "Acre", "Alagoas", "Amapá", "Amazonas", "Bahia", "Ceará", 
    "Distrito Federal", "Espírito Santo", "Goiás", "Maranhão", 
    "Mato Grosso", "Mato Grosso do Sul", "Minas Gerais", "Pará", 
    "Paraíba", "Paraná", "Pernambuco", "Piauí", "Rio de Janeiro", 
    "Rio Grande do Norte", "Rio Grande do Sul", "Rondônia", "Roraima", 
    "Santa Catarina", "São Paulo", "Sergipe", "Tocantins",
    "Não se aplica (estrangeiro)"
]


# Listas de países (português e inglês)
PAISES_PORTUGUES = [
    "Afeganistão", "África do Sul", "Albânia", "Alemanha", "Andorra", "Angola", 
    "Antígua e Barbuda", "Arábia Saudita", "Argélia", "Argentina", "Armênia", 
    "Austrália", "Áustria", "Azerbaijão", "Bahamas", "Bahrein", "Bangladesh", 
    "Barbados", "Bélgica", "Belize", "Benim", "Bielorrússia", "Bolívia", 
    "Bósnia e Herzegovina", "Botsuana", "Brasil", "Brunei", "Bulgária", 
    "Burkina Faso", "Burundi", "Butão", "Cabo Verde", "Camarões", "Camboja", 
    "Canadá", "Catar", "Cazaquistão", "Chade", "Chile", "China", "Chipre", 
    "Colômbia", "Comores", "Congo (Congo-Brazzaville)", "Coreia do Norte", 
    "Coreia do Sul", "Costa do Marfim", "Costa Rica", "Croácia", "Cuba", 
    "Dinamarca", "Djibouti", "Dominica", "Egito", "El Salvador", 
    "Emirados Árabes Unidos", "Equador", "Eritreia", "Eslováquia", "Eslovênia", 
    "Espanha", "Essuatíni", "Estados Unidos", "Estônia", "Etiópia", "Fiji", 
    "Filipinas", "Finlândia", "França", "Gabão", "Gâmbia", "Gana", "Geórgia", 
    "Granada", "Grécia", "Guatemala", "Guiana", "Guiné", "Guiné Equatorial", 
    "Guiné-Bissau", "Haiti", "Holanda (Países Baixos)", "Honduras", "Hungria", 
    "Iêmen", "Ilhas Marshall", "Ilhas Salomão", "Índia", "Indonésia", "Irã", 
    "Iraque", "Irlanda", "Islândia", "Israel", "Itália", "Jamaica", "Japão", 
    "Jordânia", "Kiribati", "Kuwait", "Laos", "Lesoto", "Letônia", "Líbano", 
    "Libéria", "Líbia", "Liechtenstein", "Lituânia", "Luxemburgo", 
    "Macedônia do Norte", "Madagascar", "Malásia", "Malawi", "Maldivas", "Mali", 
    "Malta", "Marrocos", "Maurício", "Mauritânia", "México", "Micronésia", 
    "Moçambique", "Moldávia", "Mônaco", "Mongólia", "Montenegro", 
    "Myanmar (Birmânia)", "Namíbia", "Nauru", "Nepal", "Nicarágua", "Níger", 
    "Nigéria", "Noruega", "Nova Zelândia", "Omã", "Palau", "Palestina (Estado da)", 
    "Panamá", "Papua-Nova Guiné", "Paquistão", "Paraguai", "Peru", "Polônia", 
    "Portugal", "Quênia", "Quirguistão", "Reino Unido", "República Centro-Africana", 
    "República Democrática do Congo", "República Dominicana", "República Tcheca", 
    "Romênia", "Ruanda", "Rússia", "Samoa", "Santa Lúcia", "São Cristóvão e Névis", 
    "São Marinho", "São Tomé e Príncipe", "São Vicente e Granadinas", "Seicheles", 
    "Senegal", "Serra Leoa", "Sérvia", "Singapura", "Síria", "Somália", "Sri Lanka", 
    "Sudão", "Sudão do Sul", "Suécia", "Suíça", "Suriname", "Tailândia", 
    "Tajiquistão", "Tanzânia", "Timor-Leste", "Togo", "Tonga", "Trinidad e Tobago", 
    "Tunísia", "Turcomenistão", "Turquia", "Tuvalu", "Ucrânia", "Uganda", 
    "Uruguai", "Uzbequistão", "Vanuatu", "Vaticano (Santa Sé)", "Venezuela", 
    "Vietnã", "Zâmbia", "Zimbábue"
]

PAISES_INGLES = [
"--Afghanistan", "--South Africa", "--Albania", "--Germany", "--Andorra", "--Angola", "--Antigua and Barbuda", 
"--Saudi Arabia", "--Algeria", "--Argentina", "--Armenia", "--Australia", "--Austria", "--Azerbaijan", "--Bahamas", 
"--Bahrain", "--Bangladesh", "--Barbados", "--Belgium", "--Belize", "--Benin", "--Belarus", "--Bolivia",
 "--Bosnia and Herzegovina", "--Botswana", "--Brazil", "--Brunei", "--Bulgaria", "--Burkina Faso", "--Burundi",
   "--Bhutan", "--Cabo Verde", "--Cameroon", "--Cambodia", "--Canada", "--Qatar", "--Kazakhstan", "--Chad", "--Chile",
 "--China", "--Cyprus", "--Colombia", "--Comoros", "--Congo (Congo-Brazzaville)", "--North Korea", "--South Korea",
"--Côte d'Ivoire", "--Costa Rica", "--Croatia", "--Cuba", "--Denmark", "--Djibouti", "--Dominica", "--Egypt", "--El Salvador",
"--United Arab Emirates", "--Ecuador", "--Eritrea", "--Slovakia", "--Slovenia", "--Spain", "--Eswatini", "--United States", 
"--Estonia", "--Ethiopia", "--Fiji", "--Philippines", "--Finland", "--France", "--Gabon", "--Gambia", "--Ghana", "--Georgia", 
"--Grenada", "--Greece", "--Guatemala", "--Guyana", "--Guinea", "--Equatorial Guinea", "--Guinea-Bissau", "--Haiti", 
"--Netherlands", "--Honduras", "--Hungary", "--Yemen", "--Marshall Islands", "--Solomon Islands", "--India", "--Indonesia", 
"--Iran", "--Iraq", "--Ireland", "--Iceland", "--Israel", "--Italy", "--Jamaica", "--Japan", "--Jordan", "--Kiribati", 
"--Kuwait", "--Laos", "--Lesotho", "--Latvia", "--Lebanon", "--Liberia", "--Libya", "--Liechtenstein", "--Lithuania", 
"--Luxembourg", "--North Macedonia", "--Madagascar", "--Malaysia", "--Malawi", "--Maldives", "--Mali", "--Malta", "--Morocco", 
"--Mauritius", "--Mauritania", "--Mexico", "--Micronesia", "--Mozambique", "--Moldova", "--Monaco", "--Mongolia", 
"--Montenegro", "--Myanmar (Burma)", "--Namibia", "--Nauru", "--Nepal", "--Nicaragua", "--Niger", "--Nigeria", "--Norway", 
"--New Zealand", "--Oman", "--Palau", "--Palestine (State of)", "--Panama", "--Papua New Guinea", "--Pakistan", "--Paraguay", 
"--Peru", "--Poland", "--Portugal", "--Kenya", "--Kyrgyzstan", "--United Kingdom", "--Central African Republic", 
"--Democratic Republic of the Congo", "--Dominican Republic", "--Czechia (Czech Republic)", "--Romania", "--Rwanda", "--Russia", 
"--Samoa", "--Saint Lucia", "--Saint Kitts and Nevis", "--San Marino", "--Sao Tome and Principe", 
"--Saint Vincent and the Grenadines", "--Seychelles", "--Senegal", "--Sierra Leone", "--Serbia", "--Singapore", "--Syria", 
"--Somalia", "--Sri Lanka", "--Sudan", "--South Sudan", "--Sweden", "--Switzerland", "--Suriname", "--Thailand", "--Tajikistan", 
"--Tanzania", "--Timor-Leste", "--Togo", "--Tonga", "--Trinidad and Tobago", "--Tunisia", "--Turkmenistan", "--Turkey", 
"--Tuvalu", "--Ukraine", "--Uganda", "--Uruguay", "--Uzbequistão", "--Vanuatu", "--Holy See (Vatican City)", "--Venezuela", 
"--Vietnam", "--Zambia", "--Zimbabwe"
]

# Criar dicionário de correspondência entre português e inglês
PAISES_DICT = dict(zip(PAISES_PORTUGUES, PAISES_INGLES))

# Atualizar TRANSLATIONS com as traduções dos países
for pt, en in PAISES_DICT.items():
    TRANSLATIONS[pt] = en

# Função para gerar gráfico
def gerar_grafico_base64():
    try:
        with app.app_context():
            respostas = RespostaEmissao.query.all()
        
        if not respostas:
            return None
        
        emissoes_transporte = {transp: 0 for transp in EMISSOES_TRANSPORTE.keys()}
        emissoes_tipo = {tipo: 0 for tipo in TIPOS_PARTICIPANTE}
        
        for resposta in respostas:
            transp = resposta.transporte_cidade
            if transp in emissoes_transporte:
                emissoes_transporte[transp] += float(resposta.emissao_total)
            
            tipo = resposta.tipo_participante
            if tipo in emissoes_tipo:
                emissoes_tipo[tipo] += float(resposta.emissao_total)
        
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(20, 6))
        fig.suptitle('Análise de Emissões de CO2 - Regata', fontsize=16, fontweight='bold')
        
        # Gráfico 1: Emissões por tipo de transporte
        transportes_validos = [t for t in emissoes_transporte.keys() if emissoes_transporte[t] > 0]
        valores_transp = [emissoes_transporte[t] for t in transportes_validos]
        
        if transportes_validos and any(valores_transp):
    # Cores manualmente distribuídas
            num_cores = len(transportes_validos)
            cores1 = [plt.cm.Set3(i / max(num_cores, 1)) for i in range(num_cores)]
            ax1.pie(valores_transp, labels=transportes_validos, autopct='%1.1f%%', colors=cores1)
            ax1.set_title("Distribuição de Emissões por Tipo de Transporte")
        
        # Gráfico 2: Emissões por tipo de participante
        tipos_validos = [t for t in TIPOS_PARTICIPANTE if emissoes_tipo[t] > 0]
        valores_tipos = [emissoes_tipo[t] for t in tipos_validos]
        
        if tipos_validos:
            num_cores = len(tipos_validos)
            cores2 = [plt.cm.viridis(i / max(num_cores, 1)) for i in range(num_cores)]
            bars = ax2.bar(tipos_validos, valores_tipos, color=cores2)
            ax2.set_title("Emissões por Tipo de Participante")
            ax2.set_ylabel("Emissão de CO2 (g)")
            plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
            
            for bar, valor in zip(bars, valores_tipos):
                height = bar.get_height()
                if height > 0:
                    ax2.text(bar.get_x() + bar.get_width()/2., height + 0.05,
                            f'{valor:.2f}g', ha='center', va='bottom', fontsize=8)
        
        # Gráfico 3: Eficiência dos transportes
        eficiencias = list(EMISSOES_TRANSPORTE.values())
        transportes_efic = list(EMISSOES_TRANSPORTE.keys())
        
        bars = ax3.bar(transportes_efic, eficiencias, color='#FF9800')
        ax3.set_title("Emissão Fixa por Tipo de Transporte")
        ax3.set_ylabel("gCO2 por km")

        plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45)
        
        for bar, valor in zip(bars, eficiencias):
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height + 0.05,
                    f'{valor:.2f}g', ha='center', va='bottom')
        
        plt.tight_layout()
        
        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close()
        
        return image_base64
        
    except Exception as e:
        print(f"Erro ao gerar gráfico: {e}")
        return None

# Funções de PDF
def emoji_para_imagem(emoji, tamanho=12):
    """Converte emoji em imagem base64"""
    try:
        fig, ax = plt.subplots(figsize=(tamanho/24, tamanho/24))
        ax.text(0.5, 0.5, emoji, fontsize=tamanho, ha='center', va='center')
        ax.axis('off')
        
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
    try:
        img_emoji = emoji_para_imagem(emoji, tamanho_emoji)
        if img_emoji:
            img_obj = Image(img_emoji, width=4*mm, height=4*mm)
            
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
            return Paragraph(f"• {texto}", estilo)
    except Exception as e:
        print(f"Erro ao criar linha com emoji: {e}")
        return Paragraph(f"• {texto}", estilo)

def gerar_pdf(registro):
    """Gera PDF com os resultados do questionário - TABELAS SEPARADAS PT/EN"""
    try:
        buffer = BytesIO()
        
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=A4,
            rightMargin=72, 
            leftMargin=72,
            topMargin=72, 
            bottomMargin=18,
            title=f"Emissão CO2 - {registro['email']} | CO2 Emissions - {registro['email']}"
        )
        
        elements = []
        styles = getSampleStyleSheet()
        
        # ===== ESTILOS PERSONALIZADOS =====
        estilo_titulo = ParagraphStyle(
            'TituloPrincipal',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=15,
            textColor=colors.HexColor('#2c3e50'),
            alignment=1
        )
        
        estilo_titulo_en = ParagraphStyle(
            'TituloIngles',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#666666'),
            alignment=1,
            fontName='Helvetica-Oblique'
        )
        
        estilo_subtitulo = ParagraphStyle(
            'Subtitulo',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=8,
            textColor=colors.HexColor('#34495e')
        )
        
        estilo_subtitulo_en = ParagraphStyle(
            'SubtituloIngles',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#666666'),
            spaceAfter=10,
            fontName='Helvetica-Oblique'
        )
        
        estilo_normal = ParagraphStyle(
            'NormalCustom',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=6
        )
        
        estilo_normal_en = ParagraphStyle(
            'NormalIngles',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#666666'),
            spaceAfter=8,
            fontName='Helvetica-Oblique'
        )
        
        estilo_destaque = ParagraphStyle(
            'Destaque',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#27ae60'),
            alignment=1,
            spaceAfter=15
        )
        
        estilo_destaque_en = ParagraphStyle(
            'DestaqueIngles',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#666666'),
            alignment=1,
            spaceAfter=20,
            fontName='Helvetica-Oblique'
        )

        # ===== CABEÇALHO BILINGUE =====
        titulo_pt = "Cada Deslocamento Conta: Seu Impacto em CO2 no Evento"
        titulo_en = traduzir(titulo_pt)
        
        elements.append(Paragraph(titulo_pt, estilo_titulo))
        elements.append(Paragraph(titulo_en, estilo_titulo_en))
        elements.append(Spacer(1, 15))
        # Linha divisória
        linha_divisoria = Table([[""]], colWidths=[16*cm], rowHeights=[1])
        linha_divisoria.setStyle(TableStyle([
            ('LINEABOVE', (0,0), (-1,-1), 1, colors.HexColor('#3498db')),
            ('LINEBELOW', (0,0), (-1,-1), 1, colors.HexColor('#3498db')),
        ]))
        elements.append(linha_divisoria)
        elements.append(Spacer(1, 20))

        # ===== DADOS DO PARTICIPANTE - SEPARADO PT/EN =====
        
        # TÍTULO PORTUGUÊS+++++++
        elements.append(Paragraph("DADOS DO PARTICIPANTE", estilo_subtitulo))
        
        # Traduzir dados
        tipo_traduzido = traduzir(registro['tipo_participante'])
        estado_origem = registro['estado_origem']
        
        if estado_origem == "Não se aplica (estrangeiro)":
            estado_pt = "Estrangeiro"
            estado_en = traduzir("Estrangeiro") or "International"
        else:
            estado_pt = estado_origem
            estado_en = estado_origem
        
        # TABELA EM PORTUGUÊS
        dados_pessoais_pt = [
            ["País de Origem:", registro['pais_origem_pt']],  # Nova linha
            ["Local de Origem:", estado_pt],
            ["Tipo de Participante:", registro['tipo_participante']],
            ["Email:", registro['email']],
            ["Data do Cálculo:", registro['data']]
        ]
        
        tabela_dados_pt = Table(dados_pessoais_pt, colWidths=[4*cm, 10*cm])
        tabela_dados_pt.setStyle(TableStyle([
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
        
        elements.append(tabela_dados_pt)
        elements.append(Spacer(1, 10))
        
        # TÍTULO INGLÊS
        elements.append(Paragraph("PARTICIPANT DATA", estilo_subtitulo_en))
        
        # TABELA EM INGLÊS
        dados_pessoais_en = [
            ["Country of Origin:", registro['pais_origem_en']],
            ["Origin:", estado_en],
            ["Participant Type:", tipo_traduzido],
            ["Email:", registro['email']],
            ["Calculation Date:", registro['data']]
        ]
        
        tabela_dados_en = Table(dados_pessoais_en, colWidths=[4*cm, 10*cm])
        tabela_dados_en.setStyle(TableStyle([
            ('FONT', (0,0), (-1,-1), 'Helvetica-Oblique', 9),
            ('FONT', (0,0), (0,-1), 'Helvetica-BoldOblique', 9),
            ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#f9f9f9')),
            ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor('#666666')),
            ('ALIGN', (0,0), (0,-1), 'LEFT'),
            ('ALIGN', (1,0), (1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#d5dbdb')),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        
        elements.append(tabela_dados_en)
        elements.append(Spacer(1, 25))

        # ===== RESUMO DA EMISSÃO - SEPARADO PT/EN =====
        
        # Cálculo detalhado
        emissao_local = EMISSOES_TRANSPORTE.get(registro['transporte_local'], 5.0) * registro['distancia_local'] * registro['dias_evento']
        emissao_principal = registro['emissao_total'] - emissao_local
        
        # TÍTULO E TOTAL EM PORTUGUÊS
        elements.append(Paragraph("RESUMO DA EMISSÃO", estilo_subtitulo))
        elements.append(Paragraph(f"<b>TOTAL DE EMISSÕES: {registro['emissao_total']:.2f} gCO2</b>", estilo_destaque))
        
        # Traduzir tipos de transporte
        transporte_cidade_pt = registro['transporte_cidade'].capitalize()
        transporte_cidade_en = traduzir(registro['transporte_cidade']).capitalize()
        
        transporte_local_pt = registro['transporte_local'].capitalize()
        transporte_local_en = traduzir(registro['transporte_local']).capitalize()
        
        # TABELA EM PORTUGUÊS
        detalhes_emissao_pt = [
            ["Tipo de Deslocamento", "Transporte", "Distância", "Emissão (gCO2)"],
            [
                "Até a cidade do evento", 
                transporte_cidade_pt, 
                f"{registro['distancia_cidade']} km", 
                f"{emissao_principal:.2f}"
            ],
            [
                "Deslocamento local", 
                transporte_local_pt, 
                f"{registro['distancia_local']} km/dia × {registro['dias_evento']} dias", 
                f"{emissao_local:.2f}"
            ],
            ["TOTAL", "", "", f"<b>{registro['emissao_total']:.2f} gCO2</b>"]
        ]
        
        tabela_emissao_pt = Table(detalhes_emissao_pt, colWidths=[5.5*cm, 3*cm, 4*cm, 3.5*cm])
        tabela_emissao_pt.setStyle(TableStyle([
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
        
        elements.append(tabela_emissao_pt)
        elements.append(Spacer(1, 15))
        
        # TÍTULO E TOTAL EM INGLÊS
        elements.append(Paragraph("EMISSIONS SUMMARY", estilo_subtitulo_en))
        elements.append(Paragraph(f"<font color='#666666'><i><b>TOTAL EMISSIONS: {registro['emissao_total']:.2f} gCO2</b></i></font>", estilo_destaque_en))
        
        # TABELA EM INGLÊS
        detalhes_emissao_en = [
            ["Trip Type", "Transport", "Distance", "Emissions (gCO2)"],
            [
                "To the event city", 
                transporte_cidade_en, 
                f"{registro['distancia_cidade']} km", 
                f"{emissao_principal:.2f}"
            ],
            [
                "Local commute", 
                transporte_local_en, 
                f"{registro['distancia_local']} km/day × {registro['dias_evento']} days", 
                f"{emissao_local:.2f}"
            ],
            ["TOTAL", "", "", f"<b>{registro['emissao_total']:.2f} gCO2</b>"]
        ]
        
        tabela_emissao_en = Table(detalhes_emissao_en, colWidths=[5.5*cm, 3*cm, 4*cm, 3.5*cm])
        tabela_emissao_en.setStyle(TableStyle([
            ('FONT', (0,0), (-1,-1), 'Helvetica-Oblique', 9),
            ('FONT', (0,0), (-1,0), 'Helvetica-BoldOblique', 10),
            ('FONT', (0,-1), (-1,-1), 'Helvetica-BoldOblique', 10),
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#5dade2')),
            ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#58d68d')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('TEXTCOLOR', (0,-1), (-1,-1), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#aab7b8')),
            ('PADDING', (0,0), (-1,-1), 8),
        ]))
        
        elements.append(tabela_emissao_en)
        elements.append(Spacer(1, 25))

        # ===== COMPARAÇÕES AMBIENTAIS - SEPARADO PT/EN =====
        
        arvores = registro['emissao_total'] / 7000000  # 1 árvore absorve ~7.000.000g CO2/ano
        lampadas = registro['emissao_total'] / 450   # 1 lâmpada LED/dia
        
        # TÍTULO PORTUGUÊS
        elements.append(Paragraph("IMPACTO AMBIENTAL - EQUIVALÊNCIAS", estilo_subtitulo))
        
        # TABELA EM PORTUGUÊS
        comparativos_pt = [
            ["Equivalência", "Valor Aproximado"],
            ["Árvores para absorver em 1 ano", f"{arvores:.2f} árvores"],
            ["Horas de lâmpada LED (60W)", f"{lampadas:.1f} horas"],
            ["Emissão diária média brasileira*", "≈ 12.000 gCO2"]
        ]
        
        tabela_comparativo_pt = Table(comparativos_pt, colWidths=[9*cm, 7*cm])
        tabela_comparativo_pt.setStyle(TableStyle([
            ('FONT', (0,0), (-1,-1), 'Helvetica', 9),
            ('FONT', (0,0), (-1,0), 'Helvetica-Bold', 10),
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e67e22')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#d35400')),
            ('PADDING', (0,0), (-1,-1), 8),
        ]))
        
        elements.append(tabela_comparativo_pt)
        
        # Nota de rodapé em português
        nota_pt = Paragraph(
            "* Baseado na média brasileira de 4.4 toneladas de CO2 per capita/ano",
            ParagraphStyle('Nota', parent=estilo_normal, fontSize=8, textColor=colors.gray)
        )
        elements.append(nota_pt)
        elements.append(Spacer(1, 15))
        
        # TÍTULO INGLÊS
        elements.append(Paragraph("ENVIRONMENTAL IMPACT - EQUIVALENCES", estilo_subtitulo_en))
        
        # TABELA EM INGLÊS
        comparativos_en = [
            ["Equivalence", "Approximate Value"],
            ["Trees to absorb in 1 year", f"{arvores:.2f} trees"],
            ["Hours of LED bulb (60W)", f"{lampadas:.1f} hours"],
            ["Average daily Brazilian emission*", "≈ 12,000 gCO2"]
        ]
        
        tabela_comparativo_en = Table(comparativos_en, colWidths=[9*cm, 7*cm])
        tabela_comparativo_en.setStyle(TableStyle([
            ('FONT', (0,0), (-1,-1), 'Helvetica-Oblique', 9),
            ('FONT', (0,0), (-1,0), 'Helvetica-BoldOblique', 10),
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f39c12')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#e67e22')),
            ('PADDING', (0,0), (-1,-1), 8),
        ]))
        
        elements.append(tabela_comparativo_en)
        
        # Nota de rodapé em inglês
        nota_en = Paragraph(
            "<font color='#666666'><i>* Based on the Brazilian average of 4.4 tons of CO2 per capita/year</i></font>",
            ParagraphStyle('Nota', parent=estilo_normal, fontSize=8, textColor=colors.gray)
        )
        elements.append(nota_en)
        elements.append(Spacer(1, 25))

        # ===== RECOMENDAÇÕES - LISTAS SEPARADAS PT/EN =====
        
        # TÍTULO PORTUGUÊS
        elements.append(Paragraph("RECOMENDAÇÕES PARA REDUZIR EMISSÕES", estilo_subtitulo))
        
        # Lista em português
        recomendacoes_pt = [
            " Escolha acomodações próximas ao local do evento, reduzindo a necessidade de transporte motorizado",
            " Para distâncias curtas, opte por caminhar ou pedalar, formas ativas e sustentáveis de locomoção que também favorecem a saúde e o bem-estar",
            " Prefira transportes públicos ou coletivos para deslocamentos sempre que possível",
            " Organize caronas solidárias com outros participantes, otimizando o uso dos veículos e diminuindo o número de deslocamentos individuais",
            " Planeje seus deslocamentos com antecedência para evitar horários de tráfego intenso e, consequentemente, o aumento do consumo de combustível",
            " Dê preferência a veículos elétricos ou híbridos, quando disponíveis, para minimizar o impacto ambiental dos deslocamentos", 
            " Compense emissões participando de programas de reflorestamento ou outras iniciativas ambientais reconhecidas"
        ]
        
        for rec_pt in recomendacoes_pt:
            elements.append(Paragraph(f"• {rec_pt}", estilo_normal))
            elements.append(Spacer(1, 4))
        
        elements.append(Spacer(1, 15))
        
        # TÍTULO INGLÊS
        elements.append(Paragraph("RECOMMENDATIONS TO REDUCE EMISSIONS", estilo_subtitulo_en))
        
        # Lista em inglês (traduções)
        recomendacoes_en = [
            " Choose accommodations close to the event venue, reducing the need for motorized transport",
            " For short distances, choose walking or cycling, active and sustainable forms of mobility that also promote health and well-being",
            " Prefer public or collective transportation whenever possible",
            " Organize carpooling with other participants, optimizing vehicle use and reducing the number of individual trips",
            " Plan your trips in advance to avoid peak traffic times and consequently reduce fuel consumption",
            " Prefer electric or hybrid vehicles when available to minimize the environmental impact of travel", 
            " Compensate emissions by participating in reforestation programs or other recognized environmental initiatives"
        ]
        
        for rec_en in recomendacoes_en:
            elements.append(Paragraph(f"<font color='#666666'><i>• {rec_en}</i></font>", estilo_normal_en))
            elements.append(Spacer(1, 6))
        
        elements.append(Spacer(1, 20))

        # ===== RODAPÉ SEPARADO PT/EN =====
        elements.append(Spacer(1, 10))
        linha_rodape = Table([[""]], colWidths=[16*cm], rowHeights=[1])
        linha_rodape.setStyle(TableStyle([
            ('LINEABOVE', (0,0), (-1,-1), 1, colors.HexColor('#95a5a6')),
        ]))
        elements.append(linha_rodape)
        
        # Português
        rodape_pt = Paragraph(
            "Calculadora de Emissão de CO2 - Eventos Esportivos Sustentáveis<br/>" +
            "Uma iniciativa da parceria entre CBVela e ETTA/UFF com o apoio do CNPq e Faperj para promover a conscientização ambiental em eventos esportivos",
            ParagraphStyle(
                'Rodape', 
                parent=estilo_normal, 
                fontSize=9, 
                alignment=1, 
                textColor=colors.HexColor('#7f8c8d'),
                spaceBefore=10
            )
        )
        elements.append(rodape_pt)
        
        elements.append(Spacer(1, 10))
        
        # Inglês
        rodape_en = Paragraph(
            "<font color='#666666'><i>CO2 Emissions Calculator - Sustainable Sporting Events<br/>" +
            "An initiative of the partnership between CBVela and ETTA/UFF with support from CNPq and Faperj to promote environmental awareness in sporting events</i></font>",
            ParagraphStyle(
                'RodapeEn', 
                parent=estilo_normal, 
                fontSize=8, 
                alignment=1, 
                textColor=colors.HexColor('#95a5a6'),
                spaceBefore=5
            )
        )
        elements.append(rodape_en)

        # ===== GERAR PDF =====
        doc.build(elements)
        buffer.seek(0)
        return buffer
        
    except Exception as e:
        print(f"Erro ao gerar PDF detalhado: {str(e)}")
        return gerar_pdf_simples(registro)

def gerar_pdf_simples(registro):
    """Fallback: PDF simples caso a versão detalhada falhe"""
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    
    # Usar função traduzir() para todos os textos
    p.setFont("Helvetica-Bold", 12)
    titulo_pt = "Cada Deslocamento Conta: Seu Impacto em CO2 no Evento"
    titulo_en = TRANSLATIONS.get(titulo_pt, titulo_pt) 
    p.drawString(100, 800, titulo_pt)
    p.setFont("Helvetica-Italic", 10)
    p.setFillColorRGB(0.4, 0.4, 0.4)
    p.drawString(100, 785, titulo_en)
    
    p.setFont("Helvetica", 12)
    p.setFillColorRGB(0, 0, 0)
    
    # Traduzir tipo de participante
    tipo_pt = f"Tipo: {registro['tipo_participante']}"
    tipo_en = f"Type: {traduzir(registro['tipo_participante'])}"
    
    p.drawString(100, 770, f"Email: {registro['email']}")
    p.setFont("Helvetica-Italic", 9)
    p.setFillColorRGB(0.4, 0.4, 0.4)
    p.drawString(100, 760, f"Email: {registro['email']}")
    
    p.setFont("Helvetica", 12)
    p.setFillColorRGB(0, 0, 0)
    p.drawString(100, 750, tipo_pt)
    p.setFont("Helvetica-Italic", 9)
    p.setFillColorRGB(0.4, 0.4, 0.4)
    p.drawString(100, 740, tipo_en)
    
    # Emissão total
    p.setFont("Helvetica-Bold", 14)
    p.setFillColorRGB(0, 0, 0)
    emissao_pt = f"Emissão Total: {registro['emissao_total']:.2f} gCO2"
    emissao_en = f"Total Emissions: {registro['emissao_total']:.2f} gCO2"
    p.drawString(100, 700, emissao_pt)
    p.setFont("Helvetica-Italic", 10)
    p.setFillColorRGB(0.4, 0.4, 0.4)
    p.drawString(100, 690, emissao_en)
    
    # Detalhes do transporte - com traduções
    p.setFont("Helvetica", 10)
    p.setFillColorRGB(0, 0, 0)
    
    # Transporte principal traduzido
    transporte_cidade_pt = traduzir(registro['transporte_cidade'])
    transporte_local_pt = traduzir(registro['transporte_local'])
    
    p.drawString(100, 670, f"Transporte principal: {transporte_cidade_pt}")
    p.setFont("Helvetica-Italic", 8)
    p.setFillColorRGB(0.4, 0.4, 0.4)
    p.drawString(100, 662, f"Main transport: {transporte_cidade_pt}")
    
    p.setFont("Helvetica", 10)
    p.setFillColorRGB(0, 0, 0)
    p.drawString(100, 650, f"Distância: {registro['distancia_cidade']} km")
    p.setFont("Helvetica-Italic", 8)
    p.setFillColorRGB(0.4, 0.4, 0.4)
    p.drawString(100, 642, f"Distance: {registro['distancia_cidade']} km")
    
    p.setFont("Helvetica", 10)
    p.setFillColorRGB(0, 0, 0)
    p.drawString(100, 630, f"Transporte local: {transporte_local_pt}")
    p.setFont("Helvetica-Italic", 8)
    p.setFillColorRGB(0.4, 0.4, 0.4)
    p.drawString(100, 622, f"Local transport: {transporte_local_pt}")
    
    p.setFont("Helvetica", 10)
    p.setFillColorRGB(0, 0, 0)
    p.drawString(100, 610, f"Dias de evento: {registro['dias_evento']}")
    p.setFont("Helvetica-Italic", 8)
    p.setFillColorRGB(0.4, 0.4, 0.4)
    p.drawString(100, 602, f"Event days: {registro['dias_evento']}")
    
    # Rodapé traduzido
    rodape1_pt = "Relatório gerado automaticamente"
    rodape1_en = traduzir(rodape1_pt)
    rodape2_pt = "Calculadora de Emissões - Eventos Sustentáveis"
    rodape2_en = traduzir(rodape2_pt)
    
    p.setFont("Helvetica", 10)
    p.setFillColorRGB(0, 0, 0)
    p.drawString(100, 550, rodape1_pt)
    p.setFont("Helvetica-Italic", 8)
    p.setFillColorRGB(0.4, 0.4, 0.4)
    p.drawString(100, 542, rodape1_en)
    
    p.setFont("Helvetica", 10)
    p.setFillColorRGB(0, 0, 0)
    p.drawString(100, 530, rodape2_pt)
    p.setFont("Helvetica-Italic", 8)
    p.setFillColorRGB(0.4, 0.4, 0.4)
    p.drawString(100, 522, rodape2_en)
    
    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

app.jinja_env.globals.update(get_translations=get_translations)

# Rotas Flask
@app.route('/')
def index():
    return render_template('index.html', translations=TRANSLATIONS)

@app.route('/questionario')
def questionario():
    return render_template('questionario.html', 
                          transportes=EMISSOES_TRANSPORTE.keys(),
                          tipos_participante=TIPOS_PARTICIPANTE,
                          estados_brasil=ESTADOS_BRASIL,
                          paises_portugues=PAISES_PORTUGUES,  # Nova
                          paises_ingles=PAISES_INGLES,        # Nova
                          paises_dict=PAISES_DICT,            # Nova
                          translations=TRANSLATIONS)

@app.route('/submit', methods=['POST'])
def submit():
    try:
        dados_form = request.form
        
        pais_pt = dados_form['pais_origem']
        
        pais_en = PAISES_DICT.get(pais_pt, pais_pt)


        # Validações e cálculos
        tipo_participante = dados_form['tipo_participante']
        if tipo_participante not in TIPOS_PARTICIPANTE:
            tipo_participante = "Outro"
        
        distancia_principal = float(dados_form['distancia_cidade'])
        transporte_principal = dados_form['transporte_cidade']
        emissao_principal = EMISSOES_TRANSPORTE.get(transporte_principal, 5.0) * distancia_principal
        
        distancia_local = float(dados_form['distancia_local'])
        transporte_local = dados_form['transporte_local']
        dias_evento = int(dados_form['dias_evento'])
        emissao_local = EMISSOES_TRANSPORTE.get(transporte_local, 5.0) * distancia_local * dias_evento
        
        emissao_total = emissao_principal + emissao_local
        
        # Criar registro no banco
        with app.app_context():
            nova_resposta = RespostaEmissao(
                email=dados_form['email'],
                pais_origem_pt=pais_pt,
                pais_origem_en=pais_en,
                estado_origem=dados_form['estado_origem'],
                tipo_participante=tipo_participante,
                transporte_cidade=transporte_principal,
                distancia_cidade=distancia_principal,
                transporte_local=transporte_local,
                distancia_local=distancia_local,
                dias_evento=dias_evento,
                emissao_total=emissao_total
            )
            
            db.session.add(nova_resposta)
            db.session.commit()
            
            resposta_id = nova_resposta.id
        
        # Gerar gráfico atualizado
        grafico_base64 = gerar_grafico_base64()
        
        return render_template('resultados.html', 
                              registro=nova_resposta.to_dict(), 
                              grafico_base64=grafico_base64,
                              resposta_id=resposta_id,
                              translations=TRANSLATIONS)
                              
    except Exception as e:
        print(f"Erro no submit: {e}")
        return f"Erro ao salvar dados: {str(e)}", 500

@app.route('/dados')
def get_dados():
    with app.app_context():
        respostas = RespostaEmissao.query.all()
        dados = {"respostas": [resposta.to_dict() for resposta in respostas]}
    return jsonify(dados)

@app.route('/download')
def download_dados():
    try:
        with app.app_context():
            respostas = RespostaEmissao.query.all()
        
        # Criar CSV com cabeçalhos bilingues
        si = StringIO()
        cw = csv.writer(si)
        cw.writerow([
            'ID / ID', 
            'Email / Email', 
            'País Origem (PT) / Country of Origin (EN)',
            'Estado Origem / Home State', 
            'Tipo Participante / Participant Type', 
            'Transporte até a Cidade / Transport to City', 
            'Distância até a Cidade (km) / Distance to City (km)', 
            'Transporte Local / Local Transport', 
            'Distância Local (km) / Local Distance (km)', 
            'Dias de Evento / Event Days', 
            'Emissão Total (gCO2) / Total Emissions (gCO2)', 
            'Data Registro / Registration Date'
        ])
        
        for resposta in respostas:
            cw.writerow([
                resposta.id,
                resposta.email,
                f"{resposta.pais_origem_pt} / {resposta.pais_origem_en}",
                resposta.estado_origem,
                resposta.tipo_participante,
                resposta.transporte_cidade,
                float(resposta.distancia_cidade),
                resposta.transporte_local,
                float(resposta.distancia_local),
                resposta.dias_evento,
                float(resposta.emissao_total),
                resposta.data_registro.strftime("%Y-%m-%d %H:%M:%S")
            ])
        
        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = "attachment; filename=emissoes_co2_regata_pt_en.csv"
        output.headers["Content-type"] = "text/csv; charset=utf-8"
        return output
        
    except Exception as e:
        return f"Erro ao gerar CSV: {str(e)}", 500

@app.route('/download-pdf/<int:resposta_id>')
def download_pdf(resposta_id):
    try:
        with app.app_context():
            resposta = RespostaEmissao.query.get_or_404(resposta_id)
        
        # Tenta gerar PDF detalhado primeiro
        try:
            pdf_buffer = gerar_pdf(resposta.to_dict())
        except Exception as e:
            print(f"PDF detalhado falhou, usando simples: {e}")
            pdf_buffer = gerar_pdf_simples(resposta.to_dict())
        
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=f"emissao_co2_{resposta.email.split('@')[0]}_{resposta.data_registro.strftime('%Y-%m-%d')}.pdf",
            mimetype='application/pdf'
        )
    except Exception as e:
        return f"Erro ao gerar PDF: {str(e)}", 500

# Teste rápido no Python para verificar as traduções
testes = ["Carro", "Ônibus", "Avião", "Bicicleta/A pé"]
for teste in testes:
    print(f"{teste} -> {TRANSLATIONS.get(teste, 'NÃO TRADUZIDO')}")

# Inicialização SEGURA
def init_database():
    with app.app_context():
        try:
            db.create_all()
            print("✅ Banco de dados inicializado com sucesso!")
            print(f"✅ Usando banco: {app.config['SQLALCHEMY_DATABASE_URI']}")
        except Exception as e:
            print(f"❌ Erro ao inicializar banco: {e}")

if __name__ == '__main__':
    init_database()
    print("🚀 Servidor iniciando em http://127.0.0.1:5000")
    app.run(debug=True)


