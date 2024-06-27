import os
import telebot
import imaplib
import email
from email.header import decode_header

TELEGRAM_TOKEN = '7044819146:AAGgMe8n-jEV8vBDNEoHGDKoc5GRX6dFi6M'
EMAIL_USER = 'latiendadsmith@gmail.com'
EMAIL_PASSWORD = 'jhzh'

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Variable global para almacenar los correos
correos_guardados = []

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Hola, bienvenido al bot.")

@bot.message_handler(commands=['codigo'])
def save_email(message):
    if len(message.text.split()) > 1:
        correo = message.text.split()[1]
        correos_guardados.append(correo)
        bot.reply_to(message, "Espere un momento por favor...")
        buscar_mensajes(correo, "Tu código de acceso temporal de Netflix", "[", "]", message)
    else:
        bot.reply_to(message, "Debes ingresar un correo después del comando /codigo.")

@bot.message_handler(commands=['hogar'])
def save_email_hogar(message):
    if len(message.text.split()) > 1:
        correo = message.text.split()[1]
        correos_guardados.append(correo)
        bot.reply_to(message, "Espere un momento por favor...")
        buscar_mensajes(correo, "Importante: Cómo actualizar tu Hogar con Netflix", "Sí, la envié yo", "]", message)
    else:
        bot.reply_to(message, "Debes ingresar un correo después del comando /hogar.")

def decode_subject_header(header):
    decoded_header = decode_header(header)[0]
    subject, encoding = decoded_header
    if isinstance(subject, bytes):
        return subject.decode(encoding if encoding else 'utf-8')
    return subject

def buscar_mensajes(correo, subject_to_search, start_marker, end_marker, message):
    try:
        # Conectar al servidor IMAP de Gmail
        imap = imaplib.IMAP4_SSL("imap.gmail.com")
        imap.login(EMAIL_USER, EMAIL_PASSWORD)
        
        # Seleccionar la bandeja de entrada
        imap.select("INBOX")

        # Buscar los últimos 5 mensajes
        status, messages = imap.search(None, 'ALL')
        mail_ids = messages[0].split()
        latest_5_ids = mail_ids[-20:] if len(mail_ids) >= 20 else mail_ids

        found_message = None

        for i in reversed(latest_5_ids):
            result, data = imap.fetch(i, "(RFC822)")
            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)

            if (decode_subject_header(msg["Subject"]) == subject_to_search and
                    msg["To"].strip().lower() == correo.lower()):
                found_message = msg
                break

        if found_message:
            if found_message.is_multipart():
                for part in found_message.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))
                    if content_type == "text/plain" and "attachment" not in content_disposition:
                        payload = part.get_payload(decode=True)
                        if payload:
                            body = payload.decode("utf-8", errors='replace')
                            start_index = body.find(start_marker)
                            end_index = body.find(end_marker, start_index + len(start_marker))
                            if start_index != -1 and end_index != -1:
                                codigo = body[start_index + len(start_marker):end_index].strip()
                                bot.reply_to(message, f"Código encontrado: {codigo}")
                                break
            else:
                payload = found_message.get_payload(decode=True)
                if payload:
                    body = payload.decode("utf-8", errors='replace')
                    start_index = body.find(start_marker)
                    end_index = body.find(end_marker, start_index + len(start_marker))
                    if start_index != -1 and end_index != -1:
                        codigo = body[start_index + len(start_marker):end_index].strip()
                        bot.reply_to(message, f"Código encontrado: {codigo}")
        else:
            bot.reply_to(message, f"No se encontró ningún mensaje para {correo}")

        imap.close()
        imap.logout()
    except Exception as e:
        bot.reply_to(message, f"Error al buscar mensajes: {str(e)}")

if __name__ == '__main__':
    bot.polling(none_stop=True)
