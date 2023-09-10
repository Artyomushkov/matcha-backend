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
        self.fameRating = data[21]

