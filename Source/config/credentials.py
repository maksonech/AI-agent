"""
Модуль для централизованного управления учетными данными API.
Обеспечивает безопасное хранение и доступ к ключам API и другим чувствительным данным.
"""
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import json
from .settings import CONFIG_DIR
from .exceptions import CredentialsError, FileOperationError, safe_execute, exception_handler
from .logging_config import setup_tool_logger

# Настройка логгера
credentials_logger = setup_tool_logger("credentials")


class CredentialsManager:
    """
    Класс для управления учетными данными API.
    Поддерживает загрузку данных из переменных окружения и из файла.
    """
    
    def __init__(self, load_from_env: bool = True, credentials_file: Optional[str] = None):
        """
        Инициализирует менеджер учетных данных.
        
        Args:
            load_from_env: Загружать ли данные из переменных окружения
            credentials_file: Путь к файлу с учетными данными (опционально)
        """
        self._credentials = {}
        
        # Загружаем из .env если требуется
        if load_from_env:
            load_dotenv()
            self._load_from_env()
        
        # Загружаем из файла если указан
        if credentials_file:
            self._load_from_file(credentials_file)
    
    def _load_from_env(self) -> None:
        """Загружает учетные данные из переменных окружения."""
        # GigaChat API credentials
        gigachat_credentials = os.getenv("GIGACHAT_API_CREDENTIALS")
        gigachat_scope = os.getenv("GIGACHAT_API_SCOPE")
        
        if gigachat_credentials:
            self._credentials["gigachat"] = {
                "credentials": gigachat_credentials,
                "scope": gigachat_scope or "GIGACHAT_API_PERS"
            }
            credentials_logger.info("Учетные данные GigaChat успешно загружены из переменных окружения")
        else:
            credentials_logger.warning("Учетные данные GigaChat не найдены в переменных окружения")
    
    @exception_handler(
        error_message="Ошибка при загрузке учетных данных из файла",
        logger=credentials_logger,
        expected_exceptions=[FileNotFoundError, json.JSONDecodeError, PermissionError]
    )
    def _load_from_file(self, file_path: str) -> None:
        """
        Загружает учетные данные из файла JSON.
        
        Args:
            file_path: Путь к файлу с учетными данными
            
        Raises:
            FileOperationError: Если возникла ошибка при работе с файлом
        """
        if not os.path.isabs(file_path):
            file_path = os.path.join(CONFIG_DIR, file_path)
                
        if not os.path.exists(file_path):
            credentials_logger.warning(f"Файл учетных данных не найден: {file_path}")
            return
                
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Обновляем существующие учетные данные
            for key, value in data.items():
                self._credentials[key] = value
                
            credentials_logger.info(f"Учетные данные успешно загружены из файла: {file_path}")
        except FileNotFoundError:
            raise FileOperationError(f"Файл не найден: {file_path}")
        except json.JSONDecodeError:
            raise FileOperationError(f"Ошибка при разборе JSON из файла: {file_path}")
        except PermissionError:
            raise FileOperationError(f"Нет доступа к файлу: {file_path}")
        except Exception as e:
            raise FileOperationError(f"Ошибка при загрузке учетных данных из файла: {str(e)}")
    
    @exception_handler(
        error_message="Ошибка при сохранении учетных данных в файл",
        logger=credentials_logger,
        expected_exceptions=[PermissionError]
    )
    def save_to_file(self, file_path: str, include_keys: Optional[list] = None) -> bool:
        """
        Сохраняет учетные данные в файл JSON.
        
        Args:
            file_path: Путь к файлу для сохранения
            include_keys: Список ключей для сохранения (если None, сохраняются все)
            
        Returns:
            bool: True, если сохранение успешно, иначе False
            
        Raises:
            FileOperationError: Если возникла ошибка при работе с файлом
        """
        if not os.path.isabs(file_path):
            file_path = os.path.join(CONFIG_DIR, file_path)
                
        # Создаем директорию, если она не существует
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
        # Фильтруем данные, если указаны ключи
        data_to_save = {}
        if include_keys:
            for key in include_keys:
                if key in self._credentials:
                    data_to_save[key] = self._credentials[key]
        else:
            data_to_save = self._credentials
                
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=4)
                
            credentials_logger.info(f"Учетные данные успешно сохранены в файл: {file_path}")
            return True
        except PermissionError:
            raise FileOperationError(f"Нет доступа для записи в файл: {file_path}")
        except Exception as e:
            raise FileOperationError(f"Ошибка при сохранении учетных данных в файл: {str(e)}")
    
    def get(self, provider: str, key: Optional[str] = None) -> Any:
        """
        Получает учетные данные для указанного провайдера API.
        
        Args:
            provider: Имя провайдера API (например, 'gigachat')
            key: Конкретный ключ в данных провайдера (если None, возвращаются все данные)
            
        Returns:
            Значение учетных данных или None, если данные не найдены
        """
        if provider not in self._credentials:
            return None
            
        if key is None:
            return self._credentials[provider]
            
        return self._credentials[provider].get(key)
    
    def set(self, provider: str, data: Dict[str, Any]) -> None:
        """
        Устанавливает учетные данные для указанного провайдера API.
        
        Args:
            provider: Имя провайдера API (например, 'gigachat')
            data: Словарь с учетными данными
        """
        self._credentials[provider] = data
        credentials_logger.info(f"Установлены новые учетные данные для провайдера: {provider}")
    
    def update(self, provider: str, key: str, value: Any) -> None:
        """
        Обновляет конкретное значение в учетных данных провайдера.
        
        Args:
            provider: Имя провайдера API
            key: Ключ для обновления
            value: Новое значение
        """
        if provider not in self._credentials:
            self._credentials[provider] = {}
            
        self._credentials[provider][key] = value
        credentials_logger.info(f"Обновлены учетные данные {key} для провайдера: {provider}")
    
    def validate_gigachat_credentials(self) -> bool:
        """
        Проверяет наличие и валидность учетных данных GigaChat.
        
        Returns:
            bool: True, если учетные данные валидны, иначе False
        
        Raises:
            CredentialsError: Если учетные данные неверны или отсутствуют
        """
        gigachat_data = self.get("gigachat") or {}
        
        if not gigachat_data.get("credentials"):
            credentials_logger.error("Отсутствуют учетные данные для GigaChat API")
            raise CredentialsError("Отсутствуют учетные данные для GigaChat API", 
                                  details={"provider": "gigachat", "field": "credentials"})
        
        # В будущем можно добавить проверку валидности токена
        
        return True
    
    def get_gigachat_credentials(self) -> Dict[str, str]:
        """
        Получает учетные данные для GigaChat API.
        
        Returns:
            Словарь с учетными данными GigaChat или пустой словарь
        """
        gigachat_data = self.get("gigachat") or {}
        
        # Добавляем параметры по умолчанию, если их нет
        result = {
            "credentials": gigachat_data.get("credentials"),
            "scope": gigachat_data.get("scope", "GIGACHAT_API_PERS"),
            "verify_ssl_certs": gigachat_data.get("verify_ssl_certs", False)
        }
        
        return result 