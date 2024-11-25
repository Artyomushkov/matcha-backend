from flask import current_app, render_template, url_for
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Message
from main import mail
from lib_db.select import select_query
from profile.exceptions import NotFoundError, BadRequest, FatalError

def send_email(to, subject, template):
  msg = Message(
      subject,
      recipients=[to],
      html=template,
      sender=current_app.config["MAIL_USERNAME"],
  )
  mail.send(msg)

def generate_token(data):
  serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
  return serializer.dumps(data, salt=current_app.config["SECURITY_PASSWORD_SALT"])

def confirm_token(token, expiration=3600):
  serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
  try:
    data = serializer.loads(
      token, salt=current_app.config["SECURITY_PASSWORD_SALT"], max_age=expiration
    )
    return data
  except Exception:
    return False
  
def confirm_email_send(id, email, if_confirm):
  token = generate_token(email)
  if if_confirm:
    url = url_for("profile.mail_confirm", id=id, token=token, _method="GET", _external=True)
    html = render_template("confirm_email.html", confirm_url=url)
    subject = "Please confirm your email"
  else:
    url = url_for("profile.mail_confirm", id=id, token=token, _method="DELETE", _external=True)
    html = render_template("reset_password.html", reset_url=url)
    subject = "Reset your password"
  send_email(email, subject, html)

def check_user_email(id, email):
  fields_needed = "email"
  condition_args = dict()
  condition_args['id'] = id
  try:
    user_email = select_query('profile', fields_needed, condition_args)
  except Exception as err:
    raise FatalError("Database query failed")
  if not user_email:
    raise NotFoundError("There is no user with such id")
  if user_email[0][0] != email:
    raise BadRequest("You can't change email to another one")
