"""Этот модуль будет хранить вспомогательный код для агента"""

import os
import json

# Определение корневого пути проекта
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

# Загрузка файла настроек
def load_settings(settings_path: str) -> dict:
    """Загружает файл с настройками из указанного пути."""
    with open(settings_path, 'r', encoding='utf-8', errors='replace') as file:
        return json.load(file)

# Путь к файлу настроек
settings_path = os.path.join(root_dir, 'config/settings.json')
settings = load_settings(settings_path)

# Загрузка базы данных курсов
def load_database(file_path: str) -> list[dict]:
    """Загружает базу данных курсов в формате JSON."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

# Путь к базе данных курсов из settings.json
course_data_path = os.path.join(root_dir, settings.get("course_data_path", "data/courses.json"))
courses_database = load_database(course_data_path)



