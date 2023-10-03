from enum import Enum
from flask import current_app, render_template, url_for

from itsdangerous import URLSafeTimedSerializer
from Matcha.lib_db.select import select_query
from Matcha.mail_utils import send_email
from Matcha.profile.exceptions import NotFoundError
from Matcha.profile.full_profile_entity import FullProfile
from Matcha.profile.profile_entity import Profile
from Matcha.profile.short_profile_entity import ShortProfile
from flask_mail import Message


TABLE_NAME = 'profile'

class ProfileType(Enum):
  SHORT = 1
  USUAL = 2
  FULL = 3

def find_profile_by_id(id, profileType: ProfileType):
  match profileType:
    case ProfileType.SHORT:
      fields_needed = "id, firstName, lastName, mainImage, isOnline, lastSeen"
    case ProfileType.USUAL:
      fields_needed = """id, firstName, lastName, dateOfBirth, 
        gender, sexPref, biography, tagList, mainImage, pictures,
        gpslat, gpslon, isOnline, lastSeen, fameRating, viewedMe, likedMe"""      
    case ProfileType.FULL:
      fields_needed = """id, username, firstName, lastName, email, dateOfBirth, 
        emailVerified, gender, sexPref, biography, tagList, mainImage, pictures,
        gpslat, gpslon, isOnline, lastSeen, likedMe, viewedMe, liked, viewed, fameRating"""
  condition_args = dict()
  condition_args['id'] = id
  profile = select_query(TABLE_NAME, fields_needed, condition_args)
  if not profile:
    raise NotFoundError("There is no user with such username")
  match profileType:
    case ProfileType.SHORT:
      return ShortProfile(profile[0])
    case ProfileType.USUAL:
      return Profile(profile[0])
    case ProfileType.FULL:
      return FullProfile(profile[0])

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
  
def confirm_email_send(email):
  token = generate_token(email)
  confirm_url = url_for("profile.confirm", token=token, _external=True)
  html = render_template("confirm_email.html", confirm_url=confirm_url)
  subject = "Please confirm your email"
  send_email(email, subject, html)

def send_reset_password(email, id):
  token = generate_token(email)
  reset_url = url_for("profile.mail_reset", token=token, id=id, _external=True)
  html = render_template("reset_password.html", reset_url=reset_url)
  subject = "Reset your password"
  send_email(email, subject, html)