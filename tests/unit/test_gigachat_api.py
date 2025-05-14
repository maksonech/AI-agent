"""
Тестовый скрипт для проверки соединения с GigaChat API
"""
import os
import json
import sys
from dotenv import load_dotenv
from langchain_gigachat.chat_models import GigaChat
from langchain_core.messages import HumanMessage

# Добавляем корневую директорию проекта в путь для импортов
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_gigachat_connection():
    """Проверяет соединение с GigaChat API"""
    # Загружаем переменные окружения
    load_dotenv()
    
    # Загружаем настройки из файла
    settings_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config', 'settings.json')
    settings = {}
    try:
        with open(settings_path, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        print(f"Загружены настройки из {settings_path}")
    except Exception as e:
        print(f"Ошибка при загрузке настроек: {str(e)}")
    
    # Получаем параметры из настроек и переменных окружения
    credentials = os.getenv("GIGACHAT_API_CREDENTIALS")
    scope = os.getenv("GIGACHAT_API_SCOPE", "GIGACHAT_API_PERS")
    gigachat_model = settings.get("gigachat_model", "GigaChat-2")
    
    print(f"API ключ существует: {credentials is not None}")
    print(f"Используемая модель GigaChat: {gigachat_model}")
    
    if credentials:
        print(f"Длина API ключа: {len(credentials)}")
    else:
        print("API ключ не найден в .env!")
        return False
    
    try:
        # Инициализация модели GigaChat
        model = GigaChat(
            model=gigachat_model,
            credentials=credentials,
            scope=scope,
            verify_ssl_certs=False
        )
        
        # Тестовый запрос
        message = HumanMessage(content="Привет! Как дела?")
        response = model.invoke([message])
        
        print("\nУспешное соединение с GigaChat API!")
        print(f"Ответ от GigaChat: {response.content}")
        return True
    except Exception as e:
        print(f"\nОшибка соединения с GigaChat API: {str(e)}")
        if "credentials" in str(e).lower():
            print("\nПроблема с API ключом. Убедитесь, что ключ верный и активный.")
        elif "network" in str(e).lower() or "connection" in str(e).lower():
            print("\nПроблема с сетевым соединением. Проверьте доступ к API GigaChat.")
        elif "model" in str(e).lower():
            print(f"\nПроблема с моделью '{gigachat_model}'. Возможно, эта модель недоступна.")
        return False

if __name__ == "__main__":
    result = test_gigachat_connection()
    
    # Выходной код для использования в скриптах
    sys.exit(0 if result else 1) 