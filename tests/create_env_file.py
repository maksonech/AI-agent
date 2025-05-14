"""
Скрипт для создания файла .env с учетными данными GigaChat.
"""

def create_env_file():
    """Создает файл .env с учетными данными GigaChat."""
    try:
        with open('.env', 'w', encoding='utf-8') as f:
            f.write('GIGACHAT_API_CREDENTIALS=ваш_api_ключ_здесь\n')
            f.write('GIGACHAT_API_SCOPE=GIGACHAT_API_PERS\n')
        print("Файл .env успешно создан.")
        print("Теперь откройте его и замените 'ваш_api_ключ_здесь' на ваш реальный API ключ GigaChat.")
    except Exception as e:
        print(f"Ошибка при создании файла .env: {e}")

if __name__ == "__main__":
    create_env_file() 