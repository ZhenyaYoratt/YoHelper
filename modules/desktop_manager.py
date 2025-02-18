from ctypes import windll

from .logger import *

def set_wallpaper(image_path):
    """Устанавливает обои рабочего стола."""
    try:
        windll.user32.SystemParametersInfoW(20, 0, image_path, 3)
        msg = "Обои успешно установлены."
        log(msg)
        return msg
    except Exception as e:
        msg = f"Ошибка установки обоев: {e}"
        log(msg, ERROR)
        return log

def reset_wallpaper():
    """Сбрасывает обои рабочего стола на дефолтный цвет."""
    try:
        windll.user32.SystemParametersInfoW(20, 0, "", 3)
        msg = "Обои сброшены."
        log(msg)
        return msg
    except Exception as e:
        msg = f"Ошибка сброса обоев: {e}"
        log(msg, ERROR)
        return msg
