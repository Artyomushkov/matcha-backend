class ShortProfile:
    def __init__(self, data):
        self.id = data[0]
        self.firstName = data[1]
        self.lastName = data[2]
        self.mainImage = data[3]
        self.isOnline = data[4]
        self.lastSeen = data[5]