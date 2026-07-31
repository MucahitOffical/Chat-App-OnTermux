import smtplib
from email.message import EmailMessage
import random as rd 

# Kendi bilgilerin
with open("app_password.txt","r") as f:
    appKod = f.read()

EMAIL = "chatjob280@gmail.com"
APP_PASSWORD = appKod

def sendMail(hedef_mail):
    
    UserKod = rd.randint(100000,999999)

    msg = EmailMessage()
    msg["From"] = EMAIL
    msg["To"] = hedef_mail
    msg["Subject"] = "Doğrulama kodu"
    msg.set_content(f"Merhaba doğrulama kodunuz = {UserKod}")

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL, APP_PASSWORD)
            smtp.send_message(msg)

        return True, UserKod

    except Exception as e:
        print("Hata:", e)
        return False, None
