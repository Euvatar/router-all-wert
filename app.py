import time
import gspread
from google.oauth2.service_account import Credentials
import requests
from datetime import datetime, timedelta

# Função para autenticar no Google Sheet
def get_sheet():
    # Definir as credenciais para acesso ao Google Sheet
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive.readonly"]
    creds = Credentials.from_service_account_file("credentials.json", scopes=scope)
    client = gspread.authorize(creds)
    
    # Acessar a planilha
    sheet = client.open("euvatar").sheet1  # Substitua 'euvatar' pelo nome real da sua planilha
    return sheet

# Função para enviar a mensagem via WhatsApp
def send_whatsapp_message(whatsapp_number, message):
    api_url = "https://api.audiowhats.com.br/message/sendText/WERTcorretores"
    
    payload = {
        "number": whatsapp_number,
        "options": {
            "delay": 1200,
            "presence": "composing"
        },
        "textMessage": {
            "text": message
        }
    }

    headers = {
        "apikey": "3224c361720733e80b36ed8669f0997c",  # Substitua pela sua chave de API
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(api_url, json=payload, headers=headers)
        if response.status_code == 200:
            print(f"Mensagem enviada para {whatsapp_number}: {response.json()}")
        else:
            print(f"Erro ao enviar mensagem para {whatsapp_number}: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Erro ao fazer requisição: {e}")

# Função principal para monitorar o Google Sheet e enviar mensagens
def monitor_sheet_and_notify():
    sheet = get_sheet()
    sent_messages = {}  # Armazena {whatsapp_number: {task: {"last_sent_time": datetime, "reminder_count": int}}}

    while True:
        rows = sheet.get_all_values()  # Pega todas as linhas da planilha
        
        for row in rows[1:]:  # Ignora a primeira linha (cabeçalho)
            whatsapp_number = row[0]  # Número de WhatsApp está na primeira coluna
            name = row[1]  # Nome está na segunda coluna
            
            # Ignora linhas onde o número do WhatsApp ou nome estão vazios
            if not whatsapp_number or not name:
                print(f"Linha ignorada: número ou nome ausente. {row}")
                continue
            
            # Verificando as colunas de "tarefa 2" até "tarefa 4" (Índices 3 a 5)
            tarefa_2 = row[3]
            tarefa_3 = row[4]
            tarefa_4 = row[5]
            
            now = datetime.now()

            # Tarefa 2: Mensagens de lembrete após 24 e 48 horas
            if not tarefa_2:
                task = "tarefa_2"
                reminders = sent_messages.get(whatsapp_number, {}).get(task, {"last_sent_time": None, "reminder_count": 0})
                last_sent_time = reminders["last_sent_time"]
                reminder_count = reminders["reminder_count"]

                if last_sent_time is None or now - last_sent_time >= timedelta(days=1):
                    if reminder_count == 0:
                        message = f"""
Olá {name}! Seu avatar de acesso ao meeting está pronto.
                    
Ele vale 25 pontos! Poste nas redes sociais e marque @allwert. 

Assim, você fará parte oficial do lançamento e garantirá o segundo prêmio no dia 11 de dezembro. 

Para pontuar, nos envie um print do post que realizou nas redes sociais no link abaixo!

>>  https://allresort.euvatar.com.br/tarefa2?number={whatsapp_number} <<"""
                    elif reminder_count == 1:
                        message = f"""
Oi, {name}! Não esqueça de postar seu avatar e enviar o print. Cada ponto conta para garantir seus benefícios exclusivos!"""
                    elif reminder_count == 2:
                        message = f"""
{name}, lembre-se de que sua postagem do avatar é um passo importante para pontuar! Envie o print assim que fizer."""
                    
                    send_whatsapp_message(whatsapp_number, message)
                    sent_messages.setdefault(whatsapp_number, {})[task] = {
                        "last_sent_time": now,
                        "reminder_count": reminder_count + 1
                    }

            # Tarefa 3: Mensagens de lembrete após 24 e 48 horas
            elif not tarefa_3:
                task = "tarefa_3"
                reminders = sent_messages.get(whatsapp_number, {}).get(task, {"last_sent_time": None, "reminder_count": 0})
                last_sent_time = reminders["last_sent_time"]
                reminder_count = reminders["reminder_count"]

                if last_sent_time is None or now - last_sent_time >= timedelta(days=1):
                    if reminder_count == 0:
                        message = f"""
Olá {name}, as pessoas se conectam com histórias. 

Nosso penúltimo desafio envolve seu posicionamento digital.

Que tal fazer uma visita ao All Resort? Tire uma foto no local e poste, marcando @allwert.

Na legenda, conte como acredita que o esporte e o contato com a natureza melhoram a qualidade de vida. 

Essa postagem vale 55 pontos. Não se esqueça de nos enviar o print no link abaixo! 

>>  https://allresort.euvatar.com.br/tarefa3?number={whatsapp_number} <<"""
                    elif reminder_count == 1:
                        message = f"""
Oi, {name}! Estamos esperando sua postagem no All Resort. É a última etapa para acumular pontos e estamos ansiosos por sua participação!"""
                    elif reminder_count == 2:
                        message = f"""
{name}, não deixe de postar sua foto no All Resort! Essa é a última chance de garantir sua pontuação e os prêmios no meeting."""
                    
                    send_whatsapp_message(whatsapp_number, message)
                    sent_messages.setdefault(whatsapp_number, {})[task] = {
                        "last_sent_time": now,
                        "reminder_count": reminder_count + 1
                    }

            # Tarefa 4: Sem lembretes adicionais
            elif not tarefa_4:
                task = "tarefa_4"
                if whatsapp_number not in sent_messages or \
                   task not in sent_messages[whatsapp_number] or \
                   now - sent_messages[whatsapp_number][task]["last_sent_time"] >= timedelta(days=1):
                    
                    message = f"""Olá {name}, vamos responder ao quiz? >> https://allresort.euvatar.com.br/tarefa4?number={whatsapp_number} <<"""
                    send_whatsapp_message(whatsapp_number, message)
                    sent_messages.setdefault(whatsapp_number, {})[task] = {
                        "last_sent_time": now,
                        "reminder_count": 0
                    }

        time.sleep(60)  # Aguarda 1 minuto antes de verificar novamente

if __name__ == "__main__":
    monitor_sheet_and_notify()
