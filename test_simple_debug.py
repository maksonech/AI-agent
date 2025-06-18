import sys
import io
from src.agents.assistant_agent import get_assistant_agent

# Устанавливаем кодировку вывода
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Получаем экземпляр агента
agent = get_assistant_agent()

# Тестовый запрос
query = "Привет, кто ты?"
print(f"Запрос: {query}", flush=True)

# Обрабатываем запрос
response = agent.process_request(query, "test_thread_id")
print(f"Ответ:", flush=True)
print(f"{response}", flush=True)

# Принудительно удерживаем консоль
input("Нажмите Enter для завершения...") 