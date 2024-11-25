import uuid

def is_valid_uuid(value):
    try:
        uuid.UUID(str(value))

        return True
    except ValueError:
        return False

def check_and_clean_fields(request_fields: dict, fields_needed: set):
  if not fields_needed.issubset(request_fields.keys()):
    return None 
  cleaned_fields = {key: value for key, value in request_fields.items() if key in fields_needed}  
  return cleaned_fields
