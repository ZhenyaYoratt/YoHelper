from subprocess import run
from modules.logger import *
try:
    from psutil import users

    def list_users():
        """Получает список пользователей в системе."""
        try:
            return users()
        except Exception as e:
            msg = f"Ошибка получения списка пользователей: {e}"
            log(msg, ERROR)
            return None
except ImportError:
    class suser:
        name = 'Модуль psutil недоступен.'
        terminal = None
        host = None
        started = 0
        pid = 0
    def list_users():
        return suser()
        
def add_user(username, password):
    """Добавляет нового пользователя с паролем."""
    try:
        run(["net", "user", username, password, "/add"], check=True)
        msg = f"Пользователь {username} успешно добавлен."
        log(msg)
        return True, msg
    except Exception as e:
        msg = f"Ошибка добавления пользователя {username}: {e}"
        log(msg, ERROR)
        return False, msg

def delete_user(username):
    """Удаляет пользователя из системы."""
    try:
        run(["net", "user", username, "/delete"], check=True)
        msg = f"Пользователь {username} успешно удалён."
        log(msg)
        return True, msg
    except Exception as e:
        msg = f"Ошибка удаления пользователя {username}: {e}"
        log(msg, ERROR)
        return False, msg

def set_password(username, password):
    """Устанавливает пароль для пользователя."""
    try:
        run(["net", "user", username, password], check=True)
        msg = f"Пароль для пользователя {username} успешно установлен."
        log(msg)
        return True, msg
    except Exception as e:
        msg = f"Ошибка установки пароля для пользователя {username}: {e}"
        log(msg, ERROR)
        return False, msg

def remove_password(username):
    """Удаляет пароль у пользователя."""
    try:
        run(["net", "user", username, "*"], input="\n", text=True, check=True)
        msg = f"Пароль для пользователя {username} успешно удалён."
        log(msg)
        return msg
    except Exception as e:
        msg = f"Ошибка удаления пароля для пользователя {username}: {e}"
        log(msg, ERROR)
        return msg
