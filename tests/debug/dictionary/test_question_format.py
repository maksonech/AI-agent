import sys
import io
from src.agents.assistant_agent import get_assistant_agent

# Устанавливаем кодировку вывода
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Получаем экземпляр агента
agent = get_assistant_agent()

# Тестируем различные форматы вопросов
test_queries = [
    "что это ?/paramsv2/5.0/configuration/get",
    "что такое API",
    "что за эндпоинт /paramsv2/5.0/configuration/get",
    "/paramsv2/5.0/configuration/get что это?",
    "расскажи про /paramsv2/5.0/configuration/get"
]

for i, query in enumerate(test_queries):
    print(f"\nТест #{i+1}:")
    print(f"Запрос: {query}")
    response = agent.process_request(query, f"test_thread_{i}")
    print(f"Ответ:\n{response}")
    print("-" * 50) 