import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))
SMTP_USER = os.getenv("SMTP_USER")
APP_FRONTEND_URL = os.getenv("APP_FRONTEND_URL")


def send_reset_email(para_email: str, token: str):
    reset_url = f"{APP_FRONTEND_URL}/reset-password?token={token}"

    html = f"""
    <div style="font-family: Arial, sans-serif; color: #333;">
      <h2 style="color:#fbba00;">Redefinição de Senha - Sistema de Triagem</h2>
      <p>Olá,</p>
      <p>Você solicitou uma redefinição de senha para sua conta.</p>
      <p>Clique no link abaixo para criar uma nova senha:</p>
      <p style="margin: 25px 0;">
        <a href="{reset_url}" 
           style="background-color:#fbba00; color:#000; padding:12px 24px; 
                  border-radius:6px; text-decoration:none; font-weight:bold;">
           Redefinir Senha
        </a>
      </p>
      <hr>
      <p style="font-size:12px; color:#999;">Link válido por 1 hora.</p>
    </div>
    """

    msg = MIMEMultipart()
    msg['From'] = SMTP_USER
    msg['To'] = para_email
    msg['Subject'] = "Redefinição de Senha - Sistema de Triagem"
    msg.attach(MIMEText(html, 'html'))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)            
        server.sendmail(SMTP_USER, para_email, msg.as_string())
        server.quit()
        print(f"E-mail de redefinição enviado para {para_email}")
        return True
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")
        return False
    