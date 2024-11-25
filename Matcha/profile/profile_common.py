from profile.profile_entities import FullProfile, Profile, ShortProfile, ProfileType
from lib_db.select import select_query
from profile.exceptions import NotFoundError

TABLE_NAME = 'profile'

def find_profile_by_id(id, profileType: ProfileType):
  match profileType:
    case ProfileType.SHORT:
      fields_needed = "id, firstName, lastName, mainImage, isOnline, lastSeen"
    case ProfileType.USUAL:
      fields_needed = """id, firstName, lastName, dateOfBirth, 
        gender, sexPref, biography, tagList, mainImage, pictures,
        gpslat, gpslon, isOnline, lastSeen, viewedMe, likedMe"""      
    case ProfileType.FULL:
      fields_needed = """id, username, firstName, lastName, email, dateOfBirth, 
        emailVerified, gender, sexPref, biography, tagList, mainImage, pictures,
        gpslat, gpslon, isOnline, lastSeen, likedMe, viewedMe, liked, viewed"""
  profile = select_query(TABLE_NAME, fields_needed, {'id': id})
  if not profile:
    raise NotFoundError("There is no user with such id")
  match profileType:
    case ProfileType.SHORT:
      return ShortProfile(profile[0])
    case ProfileType.USUAL:
      return Profile(profile[0])
    case ProfileType.FULL:
      return FullProfile(profile[0])