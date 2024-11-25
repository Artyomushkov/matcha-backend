from enum import Enum

class NotificationType(Enum):
  LIKE = 1
  VIEW = 2
  MESSAGE = 3
  MATCH = 4
  UNLIKE = 5

class Notification:
  def __init__(self, data):
    self.id = data[0]
    self.recipient = data[1]
    self.actor = data[2]
    self.type = data[3]
    self.date_created = data[4]
