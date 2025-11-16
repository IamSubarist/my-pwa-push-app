"""
Простой генератор VAPID ключей без py-vapid
Использует только cryptography библиотеку
"""
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
import base64

def generate_vapid_keys():
    """Генерирует VAPID ключи используя только cryptography"""
    print("Генерация VAPID ключей...")
    
    # Генерируем приватный ключ
    private_key = ec.generate_private_key(ec.SECP256R1())
    
    # Получаем публичный ключ
    public_key = private_key.public_key()
    
    # Конвертируем приватный ключ в PEM формат
    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode('utf-8')
    
    # Конвертируем публичный ключ в формат для Web Push (uncompressed point)
    public_key_numbers = public_key.public_numbers()
    
    # Формат для Web Push: 04 + x + y (uncompressed point)
    x_bytes = public_key_numbers.x.to_bytes(32, 'big')
    y_bytes = public_key_numbers.y.to_bytes(32, 'big')
    public_key_bytes = b'\x04' + x_bytes + y_bytes
    
    # Конвертируем в base64
    public_key_base64 = base64.urlsafe_b64encode(public_key_bytes).decode('utf-8').rstrip('=')
    
    print("\n" + "="*70)
    print("VAPID ключи успешно сгенерированы!")
    print("="*70)
    print("\nСКОПИРУЙТЕ ЭТИ КЛЮЧИ В RENDER:")
    print("\n1. VAPID_PRIVATE_KEY (скопируйте ВЕСЬ текст):")
    print("-"*70)
    print(private_key_pem)
    print("-"*70)
    print("\n2. VAPID_PUBLIC_KEY:")
    print(public_key_base64)
    print("\n3. VAPID_EMAIL:")
    print("mailto:your-email@example.com")
    print("="*70)
    
    return private_key_pem, public_key_base64

if __name__ == "__main__":
    generate_vapid_keys()

