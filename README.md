# Комментарии к решению работы

* Был реализован CRUD и предоставление списка для таблицы заказа автомобиля;
* Было реализовано API для получения списка цветов с количеством заказанных авто;
* Было реализовано API для получения списка марок авто с количеством заказанных авто;
* Написаны тесты (pytest). Для контроля синтаксических ошибок использовался flake8

### Комментарии к допущению:

Поскольку поставщик в состоянии поставить любое кол-во авто,
было решено создать ещё одну модель - OrderLine, которая означает конкретное авто

### Окружение проекта:
1. Python 3.10
2. Django 4.1
3. Postgres 14
4. Проект упакован в контейнер докера

#### Решение работы заняло 12 часов