# Проект парсинга pep

В проекте реализованно 4 парсера:
* Парсер новостей с офицального сайта Python;
* Парсер версий и статусов версий Python;
* Парсер последней документации Python;
* Парсер статусов и количества PEP.

## Технологии
* Python 3.9
* Beautiful Soup 4
* TQDM 4.61

## Установка и запуск проекта:
Клонировать репозиторий и перейти в него в командной строке:
```
git clone git@github.com:MPolskov/bs4_parser_pep.git
```
```
cd bs4_parser_pep
```
Cоздать и активировать виртуальное окружение:
```
# для Windows:
py -3.9 -m venv venv
# для Linux:
python3.9 -m venv venv
```
```
# для Windows:
source venv/Scripts/activate
# для Linux:
sourse venv/bin/activate
```
Установить зависимости из файла requirements.txt:
```
python -m pip install -r requirements.txt
```
Запуск парсера:
```
python src/main.py <positional argument> <optional arguments>
```
Режимы работы парсера (positional arguments):
* whats-new
* latest-versions
* download
* pep

optional arguments:

  -h, --help                               Подсказка

  -c, --clear-cache                        Очистка кеша

  -o {pretty,file}, --output {pretty,file} Дополнительные способы вывода данных

Результат вывода в файл сохраняется в папке src/results.

Результат работы парсера download сохраняется в папке src/downloads.

Логи работы программы сохраняются в папке src/logs.

## Автор:
Полшков Михаил