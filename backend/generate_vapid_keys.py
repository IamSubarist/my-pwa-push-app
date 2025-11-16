"""
Скрипт для генерации VAPID ключей для Web Push API
"""
import py_vapid
import base64

def generate_vapid_keys():
    """Генерирует пару VAPID ключей"""
    print("Генерация VAPID ключей...")
    vapid_key = py_vapid.Vapid01()
    vapid_key.generate_keys()
    
    private_key = vapid_key.private_key.pem
    # Получаем публичный ключ в правильном формате
    public_key_bytes = vapid_key.public_key.public_key_bytes
    public_key_base64 = base64.urlsafe_b64encode(public_key_bytes).decode('utf-8').rstrip('=')
    
    print("\n" + "="*60)
    print("VAPID ключи успешно сгенерированы!")
    print("="*60)
    print("\nДобавьте следующие строки в ваш .env файл:\n")
    print(f"VAPID_PRIVATE_KEY={private_key}")
    print(f"VAPID_PUBLIC_KEY={public_key_base64}")
    print(f"VAPID_EMAIL=mailto:your-email@example.com")
    print("\n" + "="*60)
    print("\nПубличный ключ (для использования в коде):")
    print(public_key_base64)
    print("\n" + "="*60)
    
    return private_key, public_key_base64

if __name__ == "__main__":
    generate_vapid_keys()

