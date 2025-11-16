from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional, List
import json
import os
import base64
from pywebpush import webpush, WebPushException
import py_vapid
from datetime import datetime, timedelta
import supabase
from dotenv import load_dotenv
from cryptography.hazmat.primitives import serialization
from jose import JWTError, jwt
from passlib.context import CryptContext
import secrets

load_dotenv()

app = FastAPI(title="PWA Push Notifications API")

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене укажите конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Инициализация Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if SUPABASE_URL and SUPABASE_KEY:
    supabase_client = supabase.create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    supabase_client = None
    print("Предупреждение: Supabase не настроен. Используется локальное хранилище.")

# VAPID ключи (должны быть в .env файле или переменных окружения Render)
VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY")
VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY")
VAPID_EMAIL = os.getenv("VAPID_EMAIL", "mailto:your-email@example.com")

# JWT настройки
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))  # Генерируем случайный ключ, если не задан
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # 30 дней

# Настройки для хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


def normalize_vapid_private_key(key: str) -> str:
    """Нормализует VAPID приватный ключ из переменной окружения.
    
    Ключ из переменных окружения может иметь потерянные переносы строк
    или литеральные \n вместо реальных переносов строк.
    """
    if not key or not isinstance(key, str):
        return key
    
    # Заменяем литеральные \n на реальные переносы строк
    normalized = key.replace("\\n", "\n")
    
    # Убираем лишние пробелы в начале и конце
    normalized = normalized.strip()
    
    # Проверяем, правильно ли отформатирован ключ
    # Правильный PEM ключ должен иметь минимум 3 строки: BEGIN, содержимое, END
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


# Конвертируем PEM ключ в base64url формат один раз при старте приложения
# Это формат, который ожидает pywebpush
VAPID_PRIVATE_KEY_BASE64URL = None
if VAPID_PRIVATE_KEY:
    try:
        normalized_key = normalize_vapid_private_key(VAPID_PRIVATE_KEY)
        # Загружаем приватный ключ из PEM строки
        private_key = serialization.load_pem_private_key(
            normalized_key.encode('utf-8'),
            password=None,
        )
        # Конвертируем ключ в формат DER
        private_key_der = private_key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        # Конвертируем DER в base64url (формат, который ожидает pywebpush)
        VAPID_PRIVATE_KEY_BASE64URL = base64.urlsafe_b64encode(private_key_der).decode('utf-8').rstrip('=')
        print("VAPID приватный ключ успешно загружен и конвертирован")
    except Exception as e:
        print(f"ОШИБКА: Не удалось загрузить VAPID приватный ключ: {e}")
        import traceback
        traceback.print_exc()


# Если ключи заданы из .env, обрабатываем публичный ключ
if VAPID_PUBLIC_KEY and isinstance(VAPID_PUBLIC_KEY, str) and not VAPID_PUBLIC_KEY.startswith("-----BEGIN"):
    import base64
    try:
        # Добавляем padding если нужно
        padding = '=' * (4 - len(VAPID_PUBLIC_KEY) % 4)
        VAPID_PUBLIC_KEY_BYTES = base64.urlsafe_b64decode(VAPID_PUBLIC_KEY + padding)
        VAPID_PUBLIC_KEY = VAPID_PUBLIC_KEY_BYTES
    except:
        # Если не получилось декодировать, пытаемся использовать py_vapid
        try:
            if VAPID_PRIVATE_KEY and VAPID_PRIVATE_KEY.startswith("-----BEGIN"):
                normalized_private_key = normalize_vapid_private_key(VAPID_PRIVATE_KEY)
                vapid_key = py_vapid.Vapid01()
                vapid_key.from_pem(normalized_private_key)
                VAPID_PUBLIC_KEY = vapid_key.public_key.public_key_bytes
        except:
            pass

# Локальное хранилище подписок (если Supabase не используется)
local_subscriptions = []

# Локальное хранилище пользователей (если Supabase не используется)
local_users = []


# Функции для работы с паролями
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


# Функции для работы с JWT токенами
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


# Зависимость для получения текущего пользователя
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Недействительный токен")
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Недействительный токен")
    return {"user_id": user_id}


# Модели данных
class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class PushSubscription(BaseModel):
    endpoint: str
    keys: dict


class NotificationData(BaseModel):
    title: str
    body: str
    icon: Optional[str] = None
    badge: Optional[str] = None
    tag: Optional[str] = None
    data: Optional[dict] = None
    requireInteraction: Optional[bool] = False
    user_id: Optional[str] = None  # Если указан, отправляем на все устройства этого пользователя


@app.get("/")
async def root():
    return {"message": "PWA Push Notifications API", "status": "running"}


@app.post("/api/register")
async def register(user_data: UserRegister):
    """Регистрация нового пользователя"""
    try:
        # Проверяем, существует ли пользователь с таким email
        if supabase_client:
            existing = supabase_client.table("users").select("*").eq("email", user_data.email).execute()
            if existing.data and len(existing.data) > 0:
                raise HTTPException(status_code=400, detail="Пользователь с таким email уже существует")
            
            # Создаем нового пользователя
            hashed_password = get_password_hash(user_data.password)
            result = supabase_client.table("users").insert({
                "username": user_data.username,
                "email": user_data.email,
                "hashed_password": hashed_password,
                "created_at": datetime.now().isoformat()
            }).execute()
            
            if result.data and len(result.data) > 0:
                user_id = result.data[0]["id"]
                # Создаем токен
                access_token = create_access_token(data={"sub": str(user_id)})
                return {
                    "status": "success",
                    "access_token": access_token,
                    "token_type": "bearer",
                    "user_id": str(user_id),
                    "username": user_data.username
                }
            else:
                raise HTTPException(status_code=500, detail="Не удалось создать пользователя")
        else:
            # Локальное хранилище
            global local_users
            # Проверяем, существует ли пользователь
            for user in local_users:
                if user["email"] == user_data.email:
                    raise HTTPException(status_code=400, detail="Пользователь с таким email уже существует")
            
            # Создаем нового пользователя
            user_id = str(len(local_users) + 1)
            hashed_password = get_password_hash(user_data.password)
            new_user = {
                "id": user_id,
                "username": user_data.username,
                "email": user_data.email,
                "hashed_password": hashed_password,
                "created_at": datetime.now().isoformat()
            }
            local_users.append(new_user)
            
            # Создаем токен
            access_token = create_access_token(data={"sub": user_id})
            return {
                "status": "success",
                "access_token": access_token,
                "token_type": "bearer",
                "user_id": user_id,
                "username": user_data.username
            }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Ошибка при регистрации: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка при регистрации: {str(e)}")


@app.post("/api/login")
async def login(user_data: UserLogin):
    """Авторизация пользователя"""
    try:
        user = None
        if supabase_client:
            result = supabase_client.table("users").select("*").eq("email", user_data.email).execute()
            if result.data and len(result.data) > 0:
                user = result.data[0]
        else:
            # Локальное хранилище
            global local_users
            for u in local_users:
                if u["email"] == user_data.email:
                    user = u
                    break
        
        if not user:
            raise HTTPException(status_code=401, detail="Неверный email или пароль")
        
        # Проверяем пароль
        if not verify_password(user_data.password, user["hashed_password"]):
            raise HTTPException(status_code=401, detail="Неверный email или пароль")
        
        # Создаем токен
        user_id = str(user["id"])
        access_token = create_access_token(data={"sub": user_id})
        return {
            "status": "success",
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user_id,
            "username": user["username"]
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Ошибка при авторизации: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка при авторизации: {str(e)}")


@app.get("/api/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Получить информацию о текущем пользователе"""
    try:
        user_id = current_user["user_id"]
        if supabase_client:
            result = supabase_client.table("users").select("id, username, email, created_at").eq("id", user_id).execute()
            if result.data and len(result.data) > 0:
                return {"status": "success", "user": result.data[0]}
            else:
                raise HTTPException(status_code=404, detail="Пользователь не найден")
        else:
            global local_users
            for user in local_users:
                if str(user["id"]) == user_id:
                    return {
                        "status": "success",
                        "user": {
                            "id": user["id"],
                            "username": user["username"],
                            "email": user["email"],
                            "created_at": user["created_at"]
                        }
                    }
            raise HTTPException(status_code=404, detail="Пользователь не найден")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/vapid-public-key")
async def get_vapid_public_key():
    """Возвращает публичный VAPID ключ для подписки"""
    # Конвертируем публичный ключ в base64 формат для фронтенда
    import base64
    if isinstance(VAPID_PUBLIC_KEY, bytes):
        public_key_base64 = base64.urlsafe_b64encode(VAPID_PUBLIC_KEY).decode('utf-8').rstrip('=')
    elif isinstance(VAPID_PUBLIC_KEY, str):
        # Если это уже base64 строка, используем как есть
        if not VAPID_PUBLIC_KEY.startswith("-----BEGIN"):
            public_key_base64 = VAPID_PUBLIC_KEY
        else:
            # Если это PEM, конвертируем через py_vapid
            try:
                normalized_private_key = normalize_vapid_private_key(VAPID_PRIVATE_KEY)
                vapid_key = py_vapid.Vapid01()
                vapid_key.from_pem(normalized_private_key)
                public_key_bytes = vapid_key.public_key.public_key_bytes
                public_key_base64 = base64.urlsafe_b64encode(public_key_bytes).decode('utf-8').rstrip('=')
            except:
                public_key_base64 = VAPID_PUBLIC_KEY
    else:
        public_key_base64 = str(VAPID_PUBLIC_KEY)
    
    return {"publicKey": public_key_base64}


@app.post("/api/subscribe")
async def subscribe(subscription: PushSubscription, current_user: dict = Depends(get_current_user)):
    """Сохраняет подписку пользователя"""
    try:
        user_id = current_user["user_id"]
        
        # Проверяем наличие обязательных полей
        if not subscription.endpoint:
            raise HTTPException(status_code=400, detail="Endpoint отсутствует")
        
        if not subscription.keys or not subscription.keys.get("p256dh") or not subscription.keys.get("auth"):
            raise HTTPException(status_code=400, detail="Ключи подписки отсутствуют или неполные")
        
        subscription_data = {
            "endpoint": subscription.endpoint,
            "keys": subscription.keys,
            "user_id": user_id,
            "created_at": datetime.now().isoformat()
        }

        if supabase_client:
            # Сохраняем в Supabase
            try:
                # Проверяем, существует ли уже подписка с таким endpoint
                existing = supabase_client.table("push_subscriptions").select("*").eq("endpoint", subscription.endpoint).execute()
                
                if existing.data and len(existing.data) > 0:
                    # Обновляем существующую подписку
                    result = supabase_client.table("push_subscriptions").update({
                        "p256dh": subscription.keys.get("p256dh"),
                        "auth": subscription.keys.get("auth"),
                        "user_id": user_id,
                        "created_at": datetime.now().isoformat()
                    }).eq("endpoint", subscription.endpoint).execute()
                else:
                    # Создаем новую подписку
                    result = supabase_client.table("push_subscriptions").insert({
                        "endpoint": subscription.endpoint,
                        "p256dh": subscription.keys.get("p256dh"),
                        "auth": subscription.keys.get("auth"),
                        "user_id": user_id,
                        "created_at": datetime.now().isoformat()
                    }).execute()
                return {"status": "success", "message": "Подписка сохранена"}
            except Exception as supabase_error:
                import traceback
                error_trace = traceback.format_exc()
                print(f"Ошибка Supabase: {str(supabase_error)}")
                print(f"Traceback: {error_trace}")
                raise HTTPException(status_code=500, detail=f"Ошибка Supabase: {str(supabase_error)}")
        else:
            # Сохраняем локально (проверяем на дубликаты)
            global local_subscriptions
            # Удаляем существующую подписку с таким же endpoint, если есть
            local_subscriptions = [
                sub for sub in local_subscriptions
                if sub["endpoint"] != subscription.endpoint
            ]
            local_subscriptions.append(subscription_data)
            return {"status": "success", "message": "Подписка сохранена"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Ошибка при сохранении подписки: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка при сохранении подписки: {str(e)}")


@app.post("/api/unsubscribe")
async def unsubscribe(subscription: PushSubscription, current_user: dict = Depends(get_current_user)):
    """Удаляет подписку пользователя"""
    try:
        user_id = current_user["user_id"]
        if supabase_client:
            # Удаляем из Supabase (только подписки текущего пользователя)
            result = supabase_client.table("push_subscriptions").delete().eq(
                "endpoint", subscription.endpoint
            ).eq("user_id", user_id).execute()
            return {"status": "success", "message": "Подписка удалена"}
        else:
            # Удаляем из локального хранилища
            global local_subscriptions
            local_subscriptions = [
                sub for sub in local_subscriptions
                if not (sub["endpoint"] == subscription.endpoint and str(sub.get("user_id")) == user_id)
            ]
            return {"status": "success", "message": "Подписка удалена"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/send-notification")
async def send_notification(notification: NotificationData, current_user: dict = Depends(get_current_user)):
    """Отправляет push-уведомление конкретному пользователю (на все его устройства)"""
    global local_subscriptions
    try:
        # Определяем, какому пользователю отправлять уведомление
        target_user_id = notification.user_id or current_user["user_id"]
        
        # Получаем подписки для указанного пользователя
        subscriptions = []
        if supabase_client:
            result = supabase_client.table("push_subscriptions").select("*").eq("user_id", target_user_id).execute()
            for row in result.data:
                subscriptions.append({
                    "endpoint": row["endpoint"],
                    "keys": {
                        "p256dh": row["p256dh"],
                        "auth": row["auth"]
                    }
                })
        else:
            # Локальное хранилище
            subscriptions = [
                {
                    "endpoint": sub["endpoint"],
                    "keys": sub["keys"]
                }
                for sub in local_subscriptions
                if str(sub.get("user_id")) == target_user_id
            ]

        if not subscriptions:
            return {"status": "error", "message": f"У пользователя {target_user_id} нет активных подписок"}

        # Проверяем наличие VAPID ключа
        if not VAPID_PRIVATE_KEY_BASE64URL:
            raise HTTPException(status_code=500, detail="VAPID_PRIVATE_KEY не настроен или не удалось загрузить")

        # Подготавливаем данные уведомления
        notification_payload = {
            "title": notification.title,
            "body": notification.body,
            "icon": notification.icon or "/vite.svg",
            "badge": notification.badge or "/vite.svg",
            "tag": notification.tag or "default",
            "data": notification.data or {},
            "requireInteraction": notification.requireInteraction
        }

        # Отправляем уведомление всем подписчикам
        success_count = 0
        failed_count = 0
        failed_endpoints = []

        for sub in subscriptions:
            try:
                print(f"Отправка уведомления на endpoint: {sub['endpoint']}")
                print(f"Данные уведомления: {notification_payload}")
                
                # Проверяем, что ключ загружен
                if not VAPID_PRIVATE_KEY_BASE64URL:
                    raise ValueError("VAPID приватный ключ не загружен. Проверьте конфигурацию.")
                
                # Используем готовый ключ в формате base64url (конвертирован при старте приложения)
                webpush(
                    subscription_info={
                        "endpoint": sub["endpoint"],
                        "keys": sub["keys"]
                    },
                    data=json.dumps(notification_payload),
                    vapid_private_key=VAPID_PRIVATE_KEY_BASE64URL,
                    vapid_claims={
                        "sub": VAPID_EMAIL
                    }
                )
                print(f"Уведомление успешно отправлено на {sub['endpoint']}")
                success_count += 1
            except WebPushException as e:
                print(f"Ошибка WebPushException при отправке на {sub['endpoint']}: {str(e)}")
                if hasattr(e, 'response') and e.response:
                    print(f"Response status: {e.response.status_code}")
                    print(f"Response text: {e.response.text if hasattr(e.response, 'text') else 'N/A'}")
                failed_count += 1
                failed_endpoints.append(sub["endpoint"])
                # Если подписка недействительна, удаляем её
                if hasattr(e, 'response') and e.response and e.response.status_code == 410:  # Gone
                    if supabase_client:
                        supabase_client.table("push_subscriptions").delete().eq(
                            "endpoint", sub["endpoint"]
                        ).execute()
                    else:
                        local_subscriptions = [
                            s for s in local_subscriptions
                            if s["endpoint"] != sub["endpoint"]
                        ]
            except Exception as e:
                # Обработка других ошибок при отправке
                import traceback
                print(f"Ошибка при отправке уведомления на {sub['endpoint']}: {str(e)}")
                print(f"Traceback: {traceback.format_exc()}")
                failed_count += 1
                failed_endpoints.append(sub["endpoint"])

        return {
            "status": "success",
            "message": f"Уведомления отправлены",
            "success_count": success_count,
            "failed_count": failed_count,
            "failed_endpoints": failed_endpoints
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/subscriptions")
async def get_subscriptions():
    """Возвращает список всех подписок (для администрирования)"""
    global local_subscriptions
    try:
        if supabase_client:
            result = supabase_client.table("push_subscriptions").select("*").execute()
            return {"subscriptions": result.data, "count": len(result.data)}
        else:
            return {"subscriptions": local_subscriptions, "count": len(local_subscriptions)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

