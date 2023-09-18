from flask import current_app
from flask_mail import Message, Mail
from Matcha import mail

"""mail = Mail()"""

def send_email(to, subject, template):
  msg = Message(
      subject,
      recipients=[to],
      html=template,
      sender=current_app.config["MAIL_USERNAME"],
  )
  mail.send(msg)