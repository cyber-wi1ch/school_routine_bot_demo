import requests

from school_routine_bot.settings import get_settings

settings = get_settings()
TOKEN = (
    settings.vk_bot_token.get_secret_value()
)  # METHOD GET_SECRET_VALUE() NEEDED FOR DE-ANON THE VARIABLE

resp = requests.get(
    "https://api.vk.com/method/groups.getById",
    params={"access_token": TOKEN, "v": "5.131"},
).json()

if "error" in resp:
    print("❌ Ошибка:", resp["error"]["error_msg"])
else:
    # resp["response"] is a list of communities
    groups = resp["response"]
    if groups:
        print("✅ Токен работает, группа:", groups[0]["name"])
    else:
        print("❌ Сообщество не найдено")
