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
from Source.tools import get_data_alert, find_endpoint_info, analyze_file_alert

# Загрузка переменных окружения
# load_dotenv('proj_v.00001/Config/demo_env.env')


# Инициализация модели GigaChat
#model = GigaChat(
    #credentials=os.getenv("GIGACHAT_API_CREDENTIALS"),
    #scope=os.getenv("GIGACHAT_API_SCOPE"),
    #model=GigaChat-Max,
model = GigaChat(
              model="GigaChat-2",
              credentials ="ZTlkOGQxOTgtYTFlYy00MDkzLWEyNDUtNjlhYThkN2EzZDRkOjYyMmM1OTM2LTc5NDAtNGFkMC1hZDczLTMxMzEwOWNlZjQ1ZQ==",
              scope="GIGACHAT_API_PERS",
              verify_ssl_certs=False
              )


def get_bot_response(prompt: str, max_tokens: int = 500, alert_data: dict = None) -> str:
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
        
        # Вызываем модель с расширенным промптом
        response = model.invoke([HumanMessage(content=enhanced_prompt)])
        return response.content
    except Exception as e:
        return f"Ошибка анализа: {str(e)}"


agent = create_react_agent(
    model=model,
    tools=[get_data_alert, find_endpoint_info, analyze_file_alert],
    state_modifier=system_prompt,  # Подключаем системный контекст
    checkpointer=MemorySaver()  # Добавляем объект из библиотеки LangGraph для сохранения памяти агента
)

def run_agent():
    """
    Функция для запуска агента в интерактивном режиме
    """
    console = Console()
    console.print(Panel.fit("Агент запущен. Введите ваш запрос (или 'выход' для завершения)"))
    
    while True:
        user_input = input("> ")
        if user_input.lower() in ["выход", "exit", "quit"]:
            break
            
        response = agent.invoke({"input": user_input})
        console.print(Panel(response["output"], title="Ответ агента"))

if __name__ == "__main__":
    run_agent()
