from flask import current_app
from flask_mail import Message
from main import mail

def send_email(to, subject, template):
  msg = Message(
      subject,
      recipients=[to],
      html=template,
      sender=current_app.config["MAIL_USERNAME"],
  )
  mail.send(msg)