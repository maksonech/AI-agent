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
from Source.tools import get_data_alert

# Загрузка переменных окружения
load_dotenv('proj_v.00001/Config/demo_env.env')


# Инициализация модели GigaChat
#model = GigaChat(
    #credentials=os.getenv("GIGACHAT_API_CREDENTIALS"),
    #scope=os.getenv("GIGACHAT_API_SCOPE"),
    #model=GigaChat-Max,
model = GigaChat(
              model="GigaChat-Max",
#ТУТ КРЕД ДЛЯ ПОДКЛЮЧЕНИЯ
              scope="GIGACHAT_API_PERS",
              verify_ssl_certs=False
              )




agent = create_react_agent(
    model=model,
    tools=[get_data_alert],
    state_modifier=system_prompt,  # Подключаем системный контекст
    checkpointer=MemorySaver()  # Добавляем объект из библиотеки LangGraph для сохранения памяти агента
)
if __name__ == "__main__":
    chat('SberAX_consultant')
