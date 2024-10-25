import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from loader import db
from data.config import EMAIL

def send_msg(username: str, cid: int, name:str, address:str, razdels:list, products:str, wish: str, summa, bot_name, bot_username):
    try:
        server_address = "smtp.gmail.com"
        server_port = 587
        login, password = "gamemastertv2018@gmail.com", "ubrc llyt evlq ghhk"
        razdel = razdels[0]
        razdel = db.fetchone("SELECT title FROM razdels WHERE idx = ?", (razdel,))[0]
        res = ''
        for product in products:
            tovar = str(product.split('=')[0]).strip()
            tovar = str(db.fetchone("SELECT title FROM products WHERE idx = ?", (tovar,))[0])
            quantity = str(product.split('=')[1])
            res += tovar+" - "+quantity+"; "
            
        msg = MIMEMultipart()
        msg['From'], msg['To'], msg['Subject'] = login, EMAIL, "Заказ"
        text = f"""{bot_name}
                @{bot_username}

                - СОДЕРЖИМОЕ КОРЗИНЫ


                ИНФОРМАЦИЯ О ТОВАРЕ:
                Раздел: {razdel}
                Товар: {res}
                Общая сумма заказа: {summa}₽.
                Сообщение: {wish}
                
                - ИНФОРМАЦИЯ О ПОЛЬЗОВАТЕЛЕ: 

                id Пользователя - {cid}
                Имя - {name}
                Никнейм в Telegram - @{username}
                Контактные данные - {address}
                """
        msg.attach(MIMEText(text, 'plain'))

        """Отправка файла"""
        # file_path = "path/to/your/file"
        # with open(file_path, "rb") as file:
        #     part = MIMEBase('application', 'octet-stream')
        #     part.set_payload(file.read())
        #     encoders.encode_base64(part)
        #     part.add_header('Content-Disposition', f"attachment; filename={file_path}")

        # msg.attach(part)
        with smtplib.SMTP(server_address, server_port) as server:
            server.starttls()
            server.login(login, password)
            server.send_message(msg)
    except Exception as e:
        logging.error(f"Ошибка при отправке почты - {e}")