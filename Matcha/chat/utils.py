from profile.profile_common import find_profile_by_id
from profile.profile_entities import ProfileType
from lib_db.select import select_query
from lib_db.delete import delete_query

def get_chat_dto(chat, user_id):
    chat_dto = {}
    chat_dto['id'] = chat[0]
    if chat[1] == user_id:
        chat_dto['user'] = find_profile_by_id(chat[2], ProfileType.SHORT).__dict__
    else:
        chat_dto['user'] = find_profile_by_id(chat[1], ProfileType.SHORT).__dict__
    return chat_dto

def delete_chat_on_unlike(id, guest_id):
    table_name = "chat"
    fields_needed = "id, userOneId, userTwoId"
    chat = select_query(table_name, fields_needed, {'userOneId': id, 'userTwoId': guest_id})
    if not chat:
        chat = select_query(table_name, fields_needed, {'userOneId': guest_id, 'userTwoId': id})
        if not chat:
            return
    delete_query(table_name, {'id': chat[0][0]})
    delete_query("message", {'chatId': chat[0][0]})