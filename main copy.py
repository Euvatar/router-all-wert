from flask import Flask, request, jsonify
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
from googleapiclient.discovery import build
from dotenv import load_dotenv
import json
import requests  # Biblioteca para requisições HTTP
import base64
from io import BytesIO
from googleapiclient.http import MediaIoBaseUpload  # Para upload de dados em memória

load_dotenv()

app = Flask(__name__)

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

credentials_dict = {
    "type": os.getenv("GOOGLE_TYPE"),
    "project_id": os.getenv("GOOGLE_PROJECT_ID"),
    "private_key_id": os.getenv("GOOGLE_PRIVATE_KEY_ID"),
    "private_key": os.getenv("GOOGLE_PRIVATE_KEY").replace("\\n", "\n"),
    "client_email": os.getenv("GOOGLE_CLIENT_EMAIL"),
    "client_id": os.getenv("GOOGLE_CLIENT_ID"),
    "auth_uri": os.getenv("GOOGLE_AUTH_URI"),
    "token_uri": os.getenv("GOOGLE_TOKEN_URI"),
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": os.getenv("GOOGLE_CLIENT_CERT_URL"),
    "universe_domain": "googleapis.com"
}

creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
client = gspread.authorize(creds)

spreadsheet = client.open("euvatar").sheet1

# URL do webhook configurável via variável de ambiente
WEBHOOK_URL = "https://api.zaia.app/v1/webhook/agent-incoming-webhook-event/create?agentIncomingWebhookId=1696&key=e03d9545-a65f-4761-9558-82a0817af9ea"

# Criar o cliente para a API do Google Drive
drive_service = build('drive', 'v3', credentials=creds)

# Definir o ID da pasta do Google Drive onde as imagens serão armazenadas
FOLDER_ID = '14fCcrB5U3IpjiYsdX_NSceiSLI5z-x7Y'  # Substitua pelo seu ID de pasta

@app.route('/upload_image', methods=['POST'])
def upload_image():
    try:
        # Extrair dados do corpo da requisição
        data = request.json
        
        # Navegar até o campo base64 dentro da estrutura complexa
        base64_string = data.get('data', {}).get('message', {}).get('base64')

        # Verificar se o base64 foi encontrado
        if not base64_string:
            return jsonify({"error": "A string base64 é obrigatória."}), 400

        # Extrair o remoteJid (número de telefone ou ID remoto) da requisição
        remote_jid = data.get('data', {}).get('key', {}).get('remoteJid')

        # Verificar se o remoteJid foi fornecido
        if not remote_jid:
            return jsonify({"error": "O remoteJid é obrigatório."}), 400

        # Remover o sufixo '@s.whatsapp.net' do remoteJid
        phone_number = remote_jid.split('@')[0]

        # Nome do arquivo será o número de telefone com extensão '.png'
        file_name = f"{phone_number}.png"

        # Converter a string base64 em um arquivo em memória usando BytesIO
        image_data = base64.b64decode(base64_string)
        image_file = BytesIO(image_data)

        # Criação do MediaIoBaseUpload diretamente do arquivo em memória
        media = MediaIoBaseUpload(image_file, mimetype='image/png', resumable=True)

        # Definir a metadata do arquivo (nome e pasta)
        file_metadata = {
            'name': file_name,
            'parents': [FOLDER_ID]  # Defina o ID da pasta para armazenar o arquivo
        }

        # Criação do arquivo no Google Drive
        uploaded_file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()

        # Obter o ID do arquivo para construir a URL
        file_id = uploaded_file['id']
        file_url = f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"

        # Atualizar o Google Sheets após o upload da imagem
        # Buscar a linha com o número de telefone
        cell = spreadsheet.find(phone_number)

        if cell:
            # Atualizar a célula correspondente à coluna 'Foto Enviada' (coluna 3) e 'Imagem1' (coluna 4)
            row = cell.row
            spreadsheet.update_cell(row, 3, "yes")  # Atualiza a coluna Foto Enviada para 'yes'
            spreadsheet.update_cell(row, 4, file_url)  # Atualiza a coluna Imagem1 com a URL
        else:
            # Se o número não for encontrado, adicionar uma nova linha
            spreadsheet.append_row([None, phone_number, "yes", file_url])  # Adiciona nova linha com o status 'yes' e URL

        return jsonify({"message": f"A imagem foi salva com sucesso no Google Drive com ID {file_id}."}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/adicionar', methods=['POST'])
def adicionar():
    data = request.get_json()
    if not data or 'nome' not in data or 'contato' not in data:
        response = {"phone": None, "message": "Dados inválidos"}
        if WEBHOOK_URL:
            requests.post(WEBHOOK_URL, json=response)  # Envia ao webhook
        return jsonify(response), 400
    
    nome = data['nome']
    contato = data['contato']

    try:
        # Buscar a linha com o contato
        cell = spreadsheet.find(contato)
        
        if cell:
            # Se o contato já existir, atualiza o nome
            row = cell.row
            spreadsheet.update_cell(row, 1, nome)  # Atualiza o nome na primeira coluna
            response = {"phone": contato, "message": "yes"}
        else:
            # Caso não exista, adiciona uma nova linha
            spreadsheet.append_row([nome, contato])
            response = {"phone": contato, "message": "Yes"}
        
        # Envia o resultado ao webhook
        if WEBHOOK_URL:
            requests.post(WEBHOOK_URL, json=response)

        return jsonify(response), 200

    except Exception as e:
        error_response = {"phone": contato, "message": str(e)}
        if WEBHOOK_URL:
            requests.post(WEBHOOK_URL, json=error_response)  # Envia erro ao webhook
        return jsonify(error_response), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
