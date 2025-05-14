import os
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from langchain_gigachat.chat_models import GigaChat
from langchain_core.messages import HumanMessage, AIMessage
from dotenv import load_dotenv
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from Source.prompts import system_prompt  # Импортируем наш системный промпт

# Импортируем инструменты из новой модульной структуры
try:
    from Source.tools import get_data_alert, find_endpoint_info, analyze_file_alert, check_token_status
except ImportError:
    # Если не удалось импортировать из старого файла, пробуем импортировать из новой структуры
    from Source.tools.alert_tools import get_data_alert, analyze_file_alert
    from Source.tools.api_tools import find_endpoint_info
    from Source.tools.gigachat_tools import check_token_status

# Импортируем конфигурационные модули
from Source.config import get_settings, CredentialsManager
from Source.config.logging_config import setup_tool_logger

# Загрузка переменных окружения и получение настроек
load_dotenv()
settings = get_settings()

# Инициализация менеджера учетных данных
credentials_manager = CredentialsManager(load_from_env=True)
gigachat_credentials = credentials_manager.get_gigachat_credentials()

# Инициализация модели GigaChat с настройками из централизованной конфигурации
model = GigaChat(
    model=settings.get("gigachat_model", "GigaChat-2"),
    credentials=gigachat_credentials.get("credentials"),
    scope=gigachat_credentials.get("scope"),
    verify_ssl_certs=gigachat_credentials.get("verify_ssl_certs", False)
)

# Настройка логгера для агента
agent_logger = setup_tool_logger("agent")


def get_bot_response(prompt: str, max_tokens: int = None, alert_data: dict = None) -> str:
    """
    Функция для получения ответа от бота на основе переданного промпта с возможным
    использованием структурированных данных алерта для углубленного анализа.
    
    Args:
        prompt: Текст запроса к боту
        max_tokens: Максимальное количество токенов в ответе
        alert_data: Словарь с структурированными данными об алерте (опционально)
        
    Returns:
        Ответ бота с углубленным анализом
    """
    try:
        # Если max_tokens не указан, берем из настроек
        if max_tokens is None:
            max_tokens = settings.get("default_max_tokens", 500)
            
        enhanced_prompt = prompt
        
        # Если предоставлены структурированные данные, дополняем запрос
        if alert_data:
            additional_context = "\n\nКраткая информация об алерте:\n"
            
            # Добавляем только самые важные технические детали
            if alert_data.get('status'):
                additional_context += f"- Статус: {alert_data['status']}\n"
            
            if alert_data.get('http_code'):
                additional_context += f"- HTTP код: {alert_data['http_code']}\n"
                
            if alert_data.get('service'):
                additional_context += f"- Сервис: {alert_data['service']}\n"
                
            # Упрощенный запрос на анализ
            additional_context += "\nКратко опиши проблему и причину (не более 100 слов).\n"
            
            enhanced_prompt += additional_context
        
        agent_logger.info(f"Запрос к боту: {enhanced_prompt[:100]}...")
        
        # Вызываем модель с расширенным промптом
        response = model.invoke([HumanMessage(content=enhanced_prompt)])
        agent_logger.info(f"Получен ответ от бота длиной {len(response.content)} символов")
        
        return response.content
    except Exception as e:
        error_msg = f"Ошибка анализа: {str(e)}"
        agent_logger.error(error_msg, exc_info=True)
        return error_msg


agent = create_react_agent(
    model=model,
    tools=[get_data_alert, find_endpoint_info, analyze_file_alert, check_token_status],
    state_modifier=system_prompt,  # Подключаем системный контекст
    checkpointer=MemorySaver()  # Добавляем объект из библиотеки LangGraph для сохранения памяти агента
)
if __name__ == "__main__":
    chat('SberAX_consultant')
