class NotFoundError(Exception):
    "Raised when the information not found in the table"
    pass

class BadRequest(Exception):
    "Raised when the request is invalid"
    pass

class FatalError(Exception):
    "Raised when the error is fatal"
    pass