"""
Простой скрипт для локального тестирования нормализации VAPID ключа
Запуск: python test_local.py
"""
import py_vapid
import base64


def normalize_vapid_private_key(key: str) -> str:
    """Нормализует VAPID приватный ключ из переменной окружения."""
    if not key or not isinstance(key, str):
        return key
    
    # Заменяем литеральные \n на реальные переносы строк
    normalized = key.replace("\\n", "\n")
    
    # Убираем лишние пробелы в начале и конце
    normalized = normalized.strip()
    
    # Проверяем, правильно ли отформатирован ключ
    line_count = normalized.count("\n") + 1 if "\n" in normalized else 1
    
    # Если ключ уже правильно отформатирован (есть переносы строк), возвращаем как есть
    if normalized.startswith("-----BEGIN") and line_count >= 3:
        # Убеждаемся, что в конце есть перенос строки
        if not normalized.endswith("\n"):
            normalized += "\n"
        return normalized
    
    # Если переносы строк потеряны (ключ в одну строку), восстанавливаем их
    if normalized.startswith("-----BEGIN"):
        # Извлекаем содержимое ключа без заголовков
        key_content = normalized.replace("-----BEGIN PRIVATE KEY-----", "").replace("-----END PRIVATE KEY-----", "").strip().replace(" ", "").replace("\n", "").replace("\r", "")
        # Разбиваем на строки по 64 символа (стандартный формат PEM)
        key_lines = [key_content[i:i+64] for i in range(0, len(key_content), 64)]
        normalized = "-----BEGIN PRIVATE KEY-----\n" + "\n".join(key_lines) + "\n-----END PRIVATE KEY-----\n"
    
    return normalized


def main():
    """Основная функция для тестирования"""
    print("\n" + "=" * 70)
    print("ЛОКАЛЬНОЕ ТЕСТИРОВАНИЕ НОРМАЛИЗАЦИИ VAPID КЛЮЧА")
    print("=" * 70 + "\n")
    
    # Ваш ключ из Render (в правильном формате)
    test_key = """-----BEGIN PRIVATE KEY-----
MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQguQzEToxcoi1JAk+w
Uzhr6yKaNQGWTbpcCCVu/82O4wihRANCAAQaalrlFw1tW2Uya14SX0DyrMmEvj2L
2ZT6plnD4ntI6kjrykbIThEpSG0F+3Oko2pIJttOdpXWCIV4EIudZTDY
-----END PRIVATE KEY-----"""
    
    print("1. Тестируем ключ в правильном формате (как вы вставили в Render):")
    print("-" * 70)
    print(f"Исходный ключ имеет {test_key.count(chr(10)) + 1} строк(и)")
    
    try:
        normalized = normalize_vapid_private_key(test_key)
        print(f"После нормализации: {normalized.count(chr(10)) + 1} строк(и)")
        
        # Пытаемся загрузить в py_vapid
        # Используем from_string вместо from_pem для лучшей совместимости
        vapid = py_vapid.Vapid01()
        # Проверяем, есть ли метод from_string
        if hasattr(vapid, 'from_string'):
            vapid.from_string(private_key=normalized)
        else:
            vapid.from_pem(normalized)
        print("[OK] УСПЕХ: Ключ успешно загружен в py_vapid!")
        
        # Получаем публичный ключ
        public_key_bytes = vapid.public_key.public_key_bytes
        public_key_base64 = base64.urlsafe_b64encode(public_key_bytes).decode('utf-8').rstrip('=')
        print(f"[OK] Публичный ключ (base64): {public_key_base64}")
        
    except Exception as e:
        print(f"[ERROR] ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n" + "=" * 70)
    print("2. Тестируем ключ БЕЗ переносов строк (как может быть в переменной окружения):")
    print("-" * 70)
    
    # Ключ без переносов строк
    single_line_key = "-----BEGIN PRIVATE KEY-----MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQguQzEToxcoi1JAk+wUzhr6yKaNQGWTbpcCCVu/82O4wihRANCAAQaalrlFw1tW2Uya14SX0DyrMmEvj2L2ZT6plnD4ntI6kjrykbIThEpSG0F+3Oko2pIJttOdpXWCIV4EIudZTDY-----END PRIVATE KEY-----"
    
    print(f"Исходный ключ имеет {single_line_key.count(chr(10)) + 1} строку (все в одной строке)")
    
    try:
        normalized2 = normalize_vapid_private_key(single_line_key)
        print(f"После нормализации: {normalized2.count(chr(10)) + 1} строк(и)")
        
        # Пытаемся загрузить в py_vapid
        vapid2 = py_vapid.Vapid01()
        if hasattr(vapid2, 'from_string'):
            vapid2.from_string(private_key=normalized2)
        else:
            vapid2.from_pem(normalized2)
        print("[OK] УСПЕХ: Ключ успешно нормализован и загружен в py_vapid!")
        
    except Exception as e:
        print(f"[ERROR] ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n" + "=" * 70)
    print("[OK] ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
    print("=" * 70)
    print("\nФункция normalize_vapid_private_key работает корректно!")
    print("Теперь можно использовать её в main.py для обработки ключей из Render.\n")


if __name__ == "__main__":
    main()

