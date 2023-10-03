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
    self.fameRating = data[14]
    self.viewedMe = data[15]
    self.likedMe = data[16]
