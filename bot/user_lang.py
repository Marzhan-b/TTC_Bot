user_languages = {}

def get_lang(chat_id: int) -> str:
    return user_languages.get(chat_id, "ru")

def set_lang(chat_id: int, lang: str):
    user_languages[chat_id] = lang