## Разработка адаптивной обучающей системы по дисциплине «Программирование и основы алгоритмизации» (ВКР)

### Оглавление
* [Основная информация](#основная-информация)
* [Адаптивность и подбор заданий](#адаптивность-и-подбор-заданий)
* [Схема базы данных](#схема-базы-данных)
* [**Проверка кода**](#проверка-кода)
* [Интерфейс системы](#интерфейс-системы)
* [Симуляция](#симуляция)

### Основная информация
Система предоставляет возможность зарегистрироваться и изучать курс по программированию на Python. Прогресс изучения определяется баллами по темам, которые можно получить, решая задания.

Каждая тема включает ряд теоретических и практических заданий. Доступ к практическим заданиям открывается после набора 24,4 баллов по теории.

Задания имеют 4 типа:
1. Выбор одного правильного варианта
2. Выбор нескольких правильных вариантов
3. Свободный ответ
4. Написание кода

Первые три типа относятся к теоретическим заданиям, написание кода — к практическим. 
Задания имеют несколько параметров:
* Основная тема
* Подтемы
* Сложность
* Оценочное время на решение

### Адаптивность и подбор заданий
[Подбор заданий](https://github.com/Azen0n/thesis/blob/main/backend/algorithm/problem_selector/problem_selector.py) осуществляется в двух режимах: вручную (выбор из списка) и с помощью алгоритма. Подбор основан на коэффициенте знаний: у каждого пользователя по каждой теме имеется значение, которое при подборе определяет сложность доступных заданий по вероятности правильного решения задания по однопараметрической модели Раша-Бирнбаума.

Подбор заданий по теории осуществляется в рамках одной темы, тогда как практические задания подбираются из банка заданий по всем темам.

#### Подбор заданий по теории
Подбор теоретических заданий начинается с калибровки начального значения коэффициента знаний, после чего задания подбираются по ценности. Ценность задания определяется отношением получаемых баллов к затраченному на решение времени.

![Подбор заданий по теории](https://i.imgur.com/u7kCZRj.png)

#### Подбор заданий по практике
В подборе практических заданий отсутствует калибровка — пользователю сразу предлагается самое ценное задание. Отличительной особенностью является алгоритм поиска проблемных тем: в случае допуска ошибки в двух похожих заданиях система определяет темы, в которых у пользователя могут быть проблемы.

![Подбор заданий по практике](https://i.imgur.com/lM0LMm7.png)

#### Алгоритм поиска проблемных тем
Группы двух похожих заданий объединяются в общий список, который делится на две группы. В каждую группу тем подбирается по 3 задания. В зависимости от успешности решения заданий группа объявляется проблемной, после чего по каждой теме понижается коэффициент знаний.

![Алгоритм поиска проблемных тем](https://i.imgur.com/E55br44.png)

### Схема базы данных
Каждый тип задания хранится в отдельной таблице.

![Схема базы данных](https://i.imgur.com/MfiFvix.png)

### Проверка кода
Песочница для запуска небезопасного кода [реализована](https://github.com/Azen0n/thesis_sandbox) с помощью Docker-контейнеров и вынесена на отдельный сервер. Из основного веб-приложения поступает запрос на сервер FastAPI, после чего создается контейнер, куда передается код и где он выполняется.
Запуск происходит с помощью [bash-скрипта](https://github.com/Azen0n/thesis_sandbox/blob/main/data/run.sh), который последовательно запускает код на парах значений входных и выходных данных.

![Архитектура песочницы](https://i.imgur.com/fOES63S.png)

### Интерфейс системы

#### Страница курса
![Интерфейс страницы курса](https://i.imgur.com/iyMVTJG.png)

#### Страница первой темы курса
![Интерфейс страницы первой темы курса](https://i.imgur.com/Is7kQtf.png)

#### Страница теоретического задания (выбор одного правильного ответа)
![Интерфейс страницы теоретического задания](https://i.imgur.com/yzgruwi.png)

#### Страница практического задания (написание кода)
![Интерфейс страницы практического задания](https://i.imgur.com/Er6FQLA.png)

### Симуляция
[Алгоритм симуляции полного прохождения курса](https://github.com/Azen0n/thesis/blob/main/backend/algorithm/pattern_simulator/pattern_simulator.py) работает на основе паттернов поведения студентов. Паттерн определяет вероятность успешного решения заданий. Например, паттерн «всплески мотивации» изменяет вероятность по синусоиде. Пример результата симуляции, целью которой является набор 91 балла по каждой теме курса:
```
user: test_user semester: Test Course, 06.2023 - 07.2023  
Topic 1 - 40.00 / 60.00 / 100.00  
Topic 2 - 40.00 / 57.00 / 97.00  
Topic 3 - 40.00 / 57.00 / 97.00  
Topic 4 - 40.00 / 57.00 / 97.00  
Topic 5 - 40.00 / 57.00 / 97.00  
Topic 6 - 40.00 / 57.00 / 97.00  
Topic 7 - 40.00 / 57.00 / 97.00  
Topic 8 - 40.00 / 57.00 / 97.00  
Topic 9 - 40.00 / 57.00 / 97.00  
Topic 10 - 40.00 / 55.67 / 95.67  
Topic 11 - 40.00 / 60.00 / 100.00  
Topic 12 - 40.00 / 60.00 / 100.00  
Topic 13 - 40.00 / 57.00 / 97.00  
Topic 14 - 40.00 / 57.00 / 97.00  
Topic 15 - 39.83 / 54.67 / 94.50  
Topic 16 - 40.00 / 57.00 / 97.00  
Topic 17 - 40.00 / 57.00 / 97.00  
Topic 18 - 39.00 / 57.00 / 96.00  
Topic 19 - 39.00 / 57.00 / 96.00  
  
Всего заданий: 230  
Теория всего: 125  
Решено: 107 (85.60%)  
- легких: 26  
- нормальных: 81  
- сложных: 0  
  
Не решено: 18 (14.40%)  
- легких: 4  
- нормальных: 14  
- сложных: 0  
  
  
Практика всего: 105  
Решено: 86 (81.90%)  
- легких: 24  
- нормальных: 24  
- сложных: 38  
  
Не решено: 19 (18.10%)  
- легких: 8  
- нормальных: 5  
- сложных: 6
```
