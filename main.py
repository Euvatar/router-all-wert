import time
import gspread
from google.oauth2.service_account import Credentials
import requests
from datetime import datetime, timedelta
import traceback

# Função para autenticar no Google Sheet
def get_sheet():
    try:
        # Definir as credenciais para acesso ao Google Sheet
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive.readonly"]
        creds = Credentials.from_service_account_file("credentials.json", scopes=scope)
        client = gspread.authorize(creds)
        
        # Acessar a planilha
        sheet = client.open("euvatar").sheet1  # Substitua 'euvatar' pelo nome real da sua planilha
        print("Conexão com a planilha realizada com sucesso!")
        return sheet
    except Exception as e:
        print(f"Erro ao autenticar no Google Sheets: {e}")
        traceback.print_exc()
        raise  # Rethrow para tratamento externo

# Função para enviar a mensagem via WhatsApp
def send_whatsapp_message(whatsapp_number, message):
    api_url = "https://api.audiowhats.com.br/message/sendText/WERTcorretores"
    payload = {
        "number": whatsapp_number,
        "options": {
            "delay": 1200,
            "presence": "composing"
        },
        "textMessage": {"text": message}
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
    except Exception as e:
        print(f"Erro ao fazer requisição para {whatsapp_number}: {e}")
        traceback.print_exc()

# Função principal para monitorar o Google Sheet e enviar mensagens
def monitor_sheet_and_notify():
    try:
        sheet = get_sheet()
    except Exception as e:
        print("Erro crítico ao acessar a planilha. Encerrando aplicação.")
        return

    sent_messages = {}  # Armazena mensagens enviadas

    while True:
        try:
            rows = sheet.get_all_values()  # Pega todas as linhas da planilha
            print(f"Planilha lida com sucesso. {len(rows) - 1} registros encontrados.")

            for row in rows[1:]:  # Ignora a primeira linha (cabeçalho)
                whatsapp_number = row[0].strip() if len(row) > 0 else None
                name = row[1].strip() if len(row) > 1 else None

                # Valida número do WhatsApp e nome
                if not whatsapp_number or not name:
                    print(f"Linha ignorada: número ou nome ausente. {row}")
                    continue

                # Verificando as colunas de "tarefa 2" até "tarefa 4"
                tarefa_2 = row[3].strip() if len(row) > 3 else None
                tarefa_3 = row[4].strip() if len(row) > 4 else None
                tarefa_4 = row[5].strip() if len(row) > 5 else None

                now = datetime.now()

                # Verifica tarefa 2
                if not tarefa_2:
                    task = "tarefa_2"
                    reminders = sent_messages.get(whatsapp_number, {}).get(task, {"last_sent_time": None, "reminder_count": 0})
                    last_sent_time = reminders["last_sent_time"]
                    reminder_count = reminders["reminder_count"]

                    if last_sent_time is None or now - last_sent_time >= timedelta(days=1):
                        message = generate_task_message(name, whatsapp_number, task, reminder_count)
                        send_whatsapp_message(whatsapp_number, message)
                        sent_messages.setdefault(whatsapp_number, {})[task] = {
                            "last_sent_time": now,
                            "reminder_count": reminder_count + 1
                        }

                # Verifica tarefa 3
                elif not tarefa_3:
                    task = "tarefa_3"
                    reminders = sent_messages.get(whatsapp_number, {}).get(task, {"last_sent_time": None, "reminder_count": 0})
                    last_sent_time = reminders["last_sent_time"]
                    reminder_count = reminders["reminder_count"]

                    if last_sent_time is None or now - last_sent_time >= timedelta(days=1):
                        message = generate_task_message(name, whatsapp_number, task, reminder_count)
                        send_whatsapp_message(whatsapp_number, message)
                        sent_messages.setdefault(whatsapp_number, {})[task] = {
                            "last_sent_time": now,
                            "reminder_count": reminder_count + 1
                        }

                # Verifica tarefa 4
                elif not tarefa_4:
                    task = "tarefa_4"
                    if whatsapp_number not in sent_messages or \
                       task not in sent_messages[whatsapp_number] or \
                       now - sent_messages[whatsapp_number][task]["last_sent_time"] >= timedelta(days=1):
                        
                        message = f"Olá {name}, vamos responder ao quiz? >> https://allresort.euvatar.com.br/tarefa4?number={whatsapp_number} <<"
                        send_whatsapp_message(whatsapp_number, message)
                        sent_messages.setdefault(whatsapp_number, {})[task] = {
                            "last_sent_time": now,
                            "reminder_count": 0
                        }

            print("Ciclo concluído. Aguardando próximo ciclo...")
            time.sleep(60)

        except Exception as e:
            print(f"Erro durante a execução: {e}")
            traceback.print_exc()

# Função para gerar mensagens por tarefa
def generate_task_message(name, whatsapp_number, task, reminder_count):
    if task == "tarefa_2":
        messages = [
            f"""
Olá {name}! Seu avatar de acesso ao meeting está pronto. Poste nas redes sociais!

Acesse: https://allresort.euvatar.com.br/tarefa2?number={whatsapp_number}""",
            f"Oi, {name}! Não esqueça de postar seu avatar e enviar o print.",
            f"{name}, lembre-se de que sua postagem do avatar é um passo importante para pontuar!"
        ]
    elif task == "tarefa_3":
        messages = [
            f"""
Olá {name}, que tal visitar o All Resort e postar sua foto?

Acesse: https://allresort.euvatar.com.br/tarefa3?number={whatsapp_number}""",
            f"Oi, {name}! Estamos esperando sua postagem no All Resort.",
            f"{name}, não deixe de postar sua foto no All Resort!"
        ]
    return messages[min(reminder_count, len(messages) - 1)]

if __name__ == "__main__":
    monitor_sheet_and_notify()
