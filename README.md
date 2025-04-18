Анализ проекта AI-agent
Общее описание
Проект представляет собой AI-агента на основе модели GigaChat от Сбера, который выполняет функции помощника по интерпретации и обработке алертов от автоматизированных систем мониторинга, а также предоставляет информацию об API-эндпоинтах.
Структура проекта
Apply to main.py
Основные компоненты:
1. AI-агент (Source/agent.py)
Использует модель GigaChat-Max для обработки запросов пользователя
Настроен с использованием библиотеки LangGraph для создания реактивного агента
Имеет доступ к трем инструментам: анализ данных алертов, поиск информации об API-эндпоинтах и анализ алертов из файла
2. Инструменты (Source/tools.py)
get_data_alert: Получает текст алерта и разбирает его на составные части
find_endpoint_info: Ищет информацию об API-эндпоинтах по запросу пользователя
analyze_file_alert: Анализирует алерт из файла (по умолчанию из TestAlerts/one_line_alert.txt)
3. Консольный интерфейс (main.py)
Организует диалог между пользователем и AI-агентом
Настраивает логирование для сохранения истории диалогов
Обрабатывает специальные команды (например, выход из приложения или прямой анализ файла)
4. Данные (Data/)
integration_endpoints.json: База данных API-эндпоинтов с информацией о URL-путях, хостах, направлениях и описаниях
Функциональность:
Анализ алертов:
Разбор текста алерта на составные части (время, сервис, ошибка и т.д.)
Интерпретация кодов HTTP ошибок
Выделение информации о проектах OpenShift
Определение периода для проверки логов
Работа с API-эндпоинтами:
Поиск эндпоинтов по URL-пути, описанию или хосту
Предоставление подробной информации о найденных эндпоинтах
Анализ алертов из файла:
Разбор содержимого файла алерта
Извлечение ключевой информации (сервис, тип алерта, период, запрос, хосты)
Формирование рекомендаций по действиям
Технологии:
LangChain + GigaChat: Фреймворк для работы с языковыми моделями
LangGraph: Библиотека для создания реактивных агентов
Логирование: Подробное логирование всех действий для дальнейшего анализа
Особенности:
Проект ориентирован на работу с корпоративной инфраструктурой Сбербанка
Поддерживает работу с алертами системы мониторинга Рефлекс
Облегчает работу оператора/администратора при анализе инцидентов
Использует систему персистентной памяти для сохранения контекста диалога
