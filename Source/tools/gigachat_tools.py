"""
Модуль для работы с GigaChat API.
Содержит инструменты для проверки статуса токенов и других операций с GigaChat.
"""
import base64
import json
import urllib3
import requests
from langchain.tools import Tool
from typing import Dict, Any, Optional

# Импортируем конфигурационные модули
from Source.config import get_settings, CredentialsManager
from Source.config.logging_config import setup_tool_logger
from Source.config.exceptions import (
    GigaChatAPIError, AuthenticationError, CredentialsError,
    exception_handler, format_exception
)

# Инициализируем логгер
tool_logger = setup_tool_logger("gigachat")

@exception_handler(
    error_message="Ошибка при проверке токена GigaChat",
    logger=tool_logger,
    expected_exceptions=[GigaChatAPIError, AuthenticationError, CredentialsError, requests.RequestException]
)
def check_gigachat_token_status(input_text: str = "") -> str:
    """
    Проверяет состояние токена GigaChat и возвращает информацию о количестве оставшихся токенов.
    
    Args:
        input_text: Любой текстовый ввод (игнорируется)
        
    Returns:
        str: Информация о состоянии токена и оставшихся токенах
        
    Raises:
        CredentialsError: Если учетные данные не найдены или некорректны
        AuthenticationError: Если не удалось аутентифицироваться в API
        GigaChatAPIError: Если возникла ошибка при работе с API GigaChat
    """
    tool_logger.info("Проверка состояния токена GigaChat")
    
    # Отключаем предупреждения о небезопасных запросах
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # Получаем учетные данные из менеджера учетных данных
    credentials_manager = CredentialsManager(load_from_env=True)
    
    # Проверяем наличие необходимых учетных данных
    try:
        credentials_manager.validate_gigachat_credentials()
    except CredentialsError as e:
        tool_logger.error(f"Ошибка валидации учетных данных: {e.message}")
        raise
    
    gigachat_creds = credentials_manager.get_gigachat_credentials()
    credentials = gigachat_creds.get("credentials")
    scope = gigachat_creds.get("scope", "GIGACHAT_API_PERS")
    
    # Загружаем настройки
    settings = get_settings()
    
    # Базовый URL для API GigaChat
    base_url = "https://gigachat.devices.sberbank.ru/api/v1"
    
    # Поскольку credentials может быть в формате Base64, мы попробуем его декодировать
    try:
        # Пробуем декодировать base64 и получить client_id:client_secret
        decoded_credentials = base64.b64decode(credentials).decode('utf-8')
        if ':' in decoded_credentials:
            client_id, client_secret = decoded_credentials.split(':', 1)
        else:
            # Если не удалось найти разделитель, используем исходные креды
            client_id = credentials
            client_secret = ""
    except Exception as e:
        tool_logger.warning(f"Не удалось декодировать учетные данные: {str(e)}")
        # Пробуем разделить исходные креды, если они в формате id:secret
        if ':' in credentials:
            client_id, client_secret = credentials.split(':', 1)
        else:
            # Если не удалось найти разделитель, используем исходные креды в качестве ID
            client_id = credentials
            client_secret = ""
    
    # Получаем токен авторизации
    auth_url = settings.get("gigachat_auth_url", f"{base_url}/oauth/token")
    auth_headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "RqUID": "e1895bdc-de6f-46f0-89f6-65df5ed71b61"
    }
    auth_data = {
        "scope": scope,
        "grant_type": "client_credentials"
    }
    
    tool_logger.info(f"Выполняем запрос к {auth_url}")
    try:
        # Выполняем запрос на авторизацию
        auth_response = requests.post(
            auth_url,
            headers=auth_headers,
            data=auth_data,
            auth=(client_id, client_secret) if client_secret else None,
            timeout=10,
            verify=gigachat_creds.get("verify_ssl_certs", False)  # Используем настройку из учетных данных
        )
    except requests.RequestException as e:
        error_message = f"Ошибка запроса авторизации: {str(e)}"
        tool_logger.error(error_message)
        raise GigaChatAPIError(error_message, details={"url": auth_url})
    
    if auth_response.status_code != 200:
        error_message = f"Ошибка аутентификации: {auth_response.status_code}"
        tool_logger.error(f"{error_message}, {auth_response.text}")
        
        raise AuthenticationError(
            error_message,
            status_code=auth_response.status_code,
            api_response=auth_response.text,
            details={"url": auth_url}
        )
    
    token_data = auth_response.json()
    access_token = token_data.get("access_token")
    
    if not access_token:
        error_message = "Токен доступа не найден в ответе"
        tool_logger.error(error_message)
        raise AuthenticationError(error_message, details={"response": token_data})
    
    # Получаем информацию о лимитах токенов
    info_url = settings.get("gigachat_info_url", f"{base_url}/accounts/info")
    info_headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }
    
    try:
        info_response = requests.get(
            info_url, 
            headers=info_headers, 
            timeout=10, 
            verify=gigachat_creds.get("verify_ssl_certs", False)
        )
    except requests.RequestException as e:
        error_message = f"Ошибка запроса информации: {str(e)}"
        tool_logger.error(error_message)
        raise GigaChatAPIError(error_message, details={"url": info_url})
    
    if info_response.status_code != 200:
        error_message = f"Ошибка получения информации: {info_response.status_code}"
        tool_logger.error(f"{error_message}, {info_response.text}")
        
        raise GigaChatAPIError(
            error_message,
            status_code=info_response.status_code,
            api_response=info_response.text,
            details={"url": info_url}
        )
    
    try:
        account_info = info_response.json()
    except json.JSONDecodeError as e:
        error_message = f"Ошибка при разборе JSON ответа: {str(e)}"
        tool_logger.error(error_message)
        raise GigaChatAPIError(error_message, details={"response": info_response.text})
    
    # Формируем информацию о токене и лимитах
    result = f"## 🔑 Информация о токене GigaChat\n\n"
    
    # Выводим информацию о токене
    if token_data.get("expires_in"):
        expires_in = token_data.get("expires_in")
        result += f"**Токен действителен:** {expires_in} секунд\n\n"
    
    # Выводим информацию о лимитах
    if "limits" in account_info and account_info["limits"]:
        limits = account_info["limits"]
        result += "### Текущие лимиты:\n\n"
        result += "| 📊 Тип | ✅ Использовано | 🔄 Лимит | 💯 Осталось |\n"
        result += "|:------|:--------------|:--------|:-----------|\n"
        
        for limit in limits:
            limit_type = limit.get("intervalType", "Неизвестно")
            current_usage = limit.get("currentUsage", 0)
            max_limit = limit.get("maxLimit", 0)
            remaining = max_limit - current_usage if max_limit > current_usage else 0
            percent = round((current_usage / max_limit) * 100, 2) if max_limit > 0 else 0
            
            result += f"| **{limit_type}** | {current_usage} | {max_limit} | {remaining} ({percent}%) |\n"
    else:
        result += "❓ Информация о лимитах недоступна\n\n"
    
    # Добавляем информацию о статусе токена
    if "status" in account_info:
        status = account_info["status"]
        result += f"\n### Статус аккаунта: **{status}**\n\n"
    
    # Дополнительная информация о токене
    result += "\n### Информация об использовании:\n\n"
    result += "- Используйте токены экономно, распределяя их равномерно\n"
    result += "- При приближении к лимиту, система может начать отклонять запросы\n"
    result += "- Рекомендуется обновлять токен при необходимости\n"
    
    # Выводим всю полученную информацию для отладки
    tool_logger.debug(f"Полученная информация о токене: {json.dumps(account_info, indent=2)}")
    
    tool_logger.info("Проверка токена GigaChat выполнена успешно")
    return result

# Создаем инструмент для проверки токена GigaChat
check_gigachat_token_status_tool = Tool(
    name="GigaChat Token Status",
    func=check_gigachat_token_status,
    description="Проверяю состояние токена GigaChat и информацию о лимитах токенов."
)

# Экспортируем инструмент
check_token_status = check_gigachat_token_status_tool 