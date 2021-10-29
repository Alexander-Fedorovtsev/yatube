# hw05_final

[![CI](https://github.com/yandex-praktikum/hw05_final/actions/workflows/python-app.yml/badge.svg?branch=master)](https://github.com/yandex-praktikum/hw05_final/actions/workflows/python-app.yml)

#### Социальная сеть для блогов

### Описание
Социальная сеть, которая позволяет пользователям делится записями, заходить на
чужие страницы, подписываться на других пользователей и комментировать их записи.
Также пользователи могут создавать сообщества по интересам и выкладывать записи в них.
Проект написан в рамках курса Яндекс.Практикум Python-разработчик. 

### О проекте
Проект базируется на следующих технологиях:
1. Python 3.7.9
2. Django 2.2.6
3. Виртуальная среда VENV (для разработки в своем окружении)
4. Git (GitHub) (для сохранения и отслеживания изменений кода)
5. Линтер Flake8 (для проверки соответствия кода стандарту PEP8)
6. UnitTest (для тестирования проекта)

### Установка и запуск проекта:
1. Клонировать репозиторий и перейти в него в командной строке:
```
git clone https://github.com/SvetlanaLogvinova88/hw05_final.git
```
```
cd hw05_final
```

2. Cоздать и активировать виртуальное окружение:
```
python3 -m venv venv
```
```
source venv/bin/activate
```

3. Обновить pip в виртуальном окружении:
```
python3 -m pip install --upgrade pip
```

4. Установить зависимости из файла requirements.txt:
```
pip install -r requirements.txt
```

5. Перейти в папку проекта:
```
cd yatube
```

6. Выполнить миграции:
```
python3 manage.py migrate
```

7. Запустить проект:
```
python3 manage.py runserver
```