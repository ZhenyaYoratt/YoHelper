# YoHelper ![GitHub last commit](https://img.shields.io/github/last-commit/ZhenyaYoratt/YoHelper?style=flat-square)

[![README - English](https://img.shields.io/badge/README-English-blue)
](https://github.com/ZhenyaYoratt/YoHelper/blob/main/README.md)

![Изображение YoHelper](/docs/images/main_window.png)

Эта многофункциональная программа позволит вам удалить вирусы (возможно) и восстановить Windows 10 до идеального состояния. Программа разработана исключительно для [YouTube канала "NEDOHACKERS Lite"](https://youtube.com/@nedohackerslite).

[![СКАЧАТЬ ПОСЛЕДНЮЮ ВЕРСИЮ РЕЛИЗА](https://img.shields.io/badge/СКАЧАТЬ_ПОСЛЕДНЮЮ_ВЕРСИЮ-%231d7c15?style=for-the-badge&logo=github)](https://github.com/ZhenyaYoratt/YoHelper/releases) [![GitHub скачивания (все assets, последний резиз)](https://img.shields.io/github/downloads-pre/ZhenyaYoratt/YoHelper/latest/total?style=flat-square)](https://github.com/ZhenyaYoratt/YoHelper/releases/)

> [!ВНИМАНИЕ]
> Программа нуждается в доработке до идеального состояния. **Используйте ее НА <ins>СВОЙ СТРАХ И РИСК</ins>, тестируйте ТОЛЬКО НА ВИРТУАЛЬНЫХ МАШИНАХ.** Если вы найдете проблемы, не стесняйтесь [создать проблему](/issues) и описать ее!
> 
> ![GitHub Issues or Pull Requests](https://img.shields.io/github/issues/ZhenyaYoratt/YoHelper?style=flat-square)

> [!ВАЖНО]
> Программа разработана на русском языке и пока не имеет международного перевода, включая английский. Пожалуйста, будьте терпеливы!

## Скачать
Скачайте [последнюю версию](https://github.com/ZhenyaYoratt/YoHelper/releases) программы. Также доступны хеши файлов и ссылки на антивирусные сканы.

## Функции
В программу встроены следующие функции:
- Антивирус
- Браузер
- Менеджер рабочего стола
- Менеджер дисков
- Запуск программ
- Восстановление системы
- Диспетчер задач
- Менеджер пользователей

## Известные проблемы
- В данный момент раздел управления точек восстановления не работает.
- Установщик не может запустить программу, для которой требуются права администратора.
<!-- В данный момент проблем нет. Если вы найдете проблемы, не стесняйтесь [создать проблему](github.com/ZhenyaYoratt/YoHelper/issues) и описать ее.-->

## TODO
- [ ] Добавить внешнюю авторизацию в аккаунт NedoTube
- [ ] Перевести программу на английский язык (i18n)

## Сборка
Для сборки программы выполните следующую команду:
```
python build.py
```
Или без использования Python файла:
```
pip install -r requirements.txt --upgrade

python -m ensurepip --upgrade
python -m pip install --upgrade setuptools

pyinstaller .\modules\tts.py --onefile
pyinstaller main.py --onefile -n NedoHelper --add-data dist:tts.exe
pyinstaller installer.py --onefile --add-data dist:NedoHelper.exe
```
> [!ПРИМЕЧАНИЕ]
> Перед запуском без использования Python файла необходимо установить следующие зависимости.

## Руководство по внесению изменений
Пожалуйста, соблюдайте стандарты кодирования и добавляйте комментарии, где это необходимо. Для крупных изменений рекомендуется сначала открыть проблему, чтобы обсудить возможные изменения.

## Используемые зависимости
- `Python` 3.11.9
- `PyQt5` 5.15.11
- `PyQtWebEngine` 5.15

Полный список зависимостей можно найти в файле [requirements.txt](requirements.txt).

## Благодарности
Особая благодарность сообществу с открытым исходным кодом за предоставление библиотек и инструментов, которые способствуют быстрому развитию. Этот проект использует несколько ресурсов сообщества для улучшения своей функциональности.

## Лицензия
Этот проект лицензирован на условиях GNU General Public License версии 3.0 или новее. Полный текст лицензии можно найти в файле [LICENSE](LICENSE).

## История звезд
<a href="https://star-history.com/#ZhenyaYoratt/YoHelper&Date">
 <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=ZhenyaYoratt/YoHelper&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=ZhenyaYoratt/YoHelper&type=Date" />
    <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=ZhenyaYoratt/YoHelper&type=Date" />
 </picture>
</a>

---

Не стесняйтесь обращаться к владельцу репозитория, [ZhenyaYoratt](https://github.com/ZhenyaYoratt), по любым вопросам или за руководством по проекту.