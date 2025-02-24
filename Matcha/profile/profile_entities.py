from enum import Enum

def calculate_fame_rating(viewedMe, likedMe):
  if not likedMe or not viewedMe:
    return 0
  return round(len(likedMe) / len(viewedMe) * 5, 2)

class ProfileType(Enum):
  SHORT = 1
  USUAL = 2
  FULL = 3

class ShortProfile:
  def __init__(self, data):
    self.id = data[0]
    self.firstName = data[1]
    self.lastName = data[2]
    self.mainImage = data[3]
    self.isOnline = data[4]
    self.lastSeen = data[5]

class Profile:
  def __init__(self, data):
    self.id = data[0]
    self.firstName = data[1]
    self.lastName = data[2]
    self.dateOfBirth = data[3]
    self.gender = data[4]
    self.sexPref = data[5]
    self.biography = data[6]
    self.tags = data[7]
    self.mainImage = data[8]
    self.pictures = data[9]
    self.location = { 'lat': data[10], 'lon': data[11] }
    self.isOnline = data[12]
    self.lastSeen = data[13]
    self.fameRating = calculate_fame_rating(data[14], data[15])
    self.viewedMe = data[14]
    self.likedMe = data[15]
    self.isFake = data[16]

class FullProfile:
  def __init__(self, data):
    self.id = data[0]
    self.username = data[1]
    self.firstName = data[2]
    self.lastName = data[3]
    self.email = data[4]
    self.dateOfBirth = data[5]
    self.emailVerified = data[6]
    self.gender = data[7]
    self.sexPref = data[8]
    self.biography = data[9]
    self.tagList = data[10]
    self.mainImage = data[11]
    self.pictures = data[12]
    self.location = { 'lat': data[13], 'lon': data[14] }
    self.isOnline = data[15]
    self.lastSeen = data[16]
    self.likedMe = data[17]
    self.viewedMe = data[18]
    self.liked = data[19]
    self.viewed = data[20]
    self.fameRating = calculate_fame_rating(data[17], data[18])
    self.isFake = data[21]
