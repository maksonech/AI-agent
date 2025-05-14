"""
Тестовый скрипт для проверки функции get_bot_response
"""
import os
import sys
import traceback
import logging
from langchain_gigachat.chat_models import GigaChat
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('test_bot_response')

def main():
    try:
        # Загрузка переменных окружения
        load_dotenv()
        print(f"Загружены переменные окружения из {os.path.abspath('.env')}")
        
        # Получение учетных данных GigaChat
        gigachat_credentials = os.getenv('GIGACHAT_API_CREDENTIALS')
        gigachat_scope = os.getenv('GIGACHAT_API_SCOPE')
        
        if not gigachat_credentials:
            print("ОШИБКА: Не найдены учетные данные GIGACHAT_API_CREDENTIALS в переменных окружения")
            return
            
        if not gigachat_scope:
            print("ПРЕДУПРЕЖДЕНИЕ: Не найден scope GIGACHAT_API_SCOPE в переменных окружения")
            gigachat_scope = "GIGACHAT_API_PERS"
            print(f"Используется scope по умолчанию: {gigachat_scope}")
            
        cred_length = len(gigachat_credentials)
        print(f"Учетные данные GigaChat: {gigachat_credentials[:5]}...{gigachat_credentials[-5:]} (длина: {cred_length})")
        print(f"Scope GigaChat: {gigachat_scope}")
        
        # Загрузка настроек из настроек проекта
        try:
            from config import get_settings
            settings = get_settings()
            gigachat_model = settings.get("gigachat_model", "GigaChat-2")
            print(f"Используемая модель GigaChat: {gigachat_model}")
        except Exception as e:
            print(f"Ошибка при загрузке настроек: {str(e)}")
            gigachat_model = "GigaChat-2"
            print(f"Используется модель по умолчанию: {gigachat_model}")
        
        # Настройка клиента GigaChat
        print("Инициализация клиента GigaChat...")
        model = GigaChat(
            model=gigachat_model,
            credentials=gigachat_credentials,
            scope=gigachat_scope,
            verify_ssl_certs=False
        )
        print("Клиент GigaChat успешно инициализирован")
        
        # Тестовый запрос
        test_prompt = "Привет! Как ты можешь мне помочь с анализом алертов?"
        print(f"\nТестовый запрос: {test_prompt}")
        
        print("Отправка запроса к GigaChat API...")
        try:
            # Прямой вызов модели
            response = model.invoke([HumanMessage(content=test_prompt)])
            print(f"Получен ответ от API, длина: {len(response.content)} символов")
            print("\nОтвет от GigaChat:")
            print(response.content)
            
            # Теперь тестируем функцию get_bot_response
            print("\n=== Тестирование функции get_bot_response ===")
            
            try:
                from src.core.agent import get_bot_response
                test_response = get_bot_response(test_prompt, max_tokens=500)
                print(f"Получен ответ от get_bot_response, длина: {len(test_response)} символов")
                print("\nОтвет от get_bot_response:")
                print(test_response)
            except Exception as e:
                print(f"Ошибка при вызове get_bot_response: {str(e)}")
                print(f"Трассировка: {traceback.format_exc()}")
        
        except Exception as e:
            print(f"Ошибка при вызове GigaChat API: {str(e)}")
            print(f"Трассировка: {traceback.format_exc()}")
    
    except Exception as e:
        print(f"Общая ошибка: {str(e)}")
        print(f"Трассировка: {traceback.format_exc()}")

if __name__ == "__main__":
    main()
    print("\nТестирование завершено.") 