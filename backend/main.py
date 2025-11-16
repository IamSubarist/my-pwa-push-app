from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import json
import os
from pywebpush import webpush, WebPushException
import py_vapid
from datetime import datetime
import supabase
from dotenv import load_dotenv

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

# VAPID ключи (должны быть в .env файле)
VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY")
VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY")
VAPID_EMAIL = os.getenv("VAPID_EMAIL", "mailto:your-email@example.com")

# Если ключи не заданы, генерируем их
if not VAPID_PRIVATE_KEY or not VAPID_PUBLIC_KEY:
    print("Генерация новых VAPID ключей...")
    import base64
    vapid_key = py_vapid.Vapid01()
    vapid_key.generate_keys()
    # Получаем ключи в правильном формате для Web Push
    VAPID_PRIVATE_KEY = vapid_key.private_key.pem
    # Публичный ключ конвертируем в base64 формат для сохранения в .env
    public_key_bytes = vapid_key.public_key.public_key_bytes
    VAPID_PUBLIC_KEY_BASE64 = base64.urlsafe_b64encode(public_key_bytes).decode('utf-8').rstrip('=')
    print("ВАЖНО: Сохраните эти ключи в .env файле:")
    print(f"VAPID_PRIVATE_KEY={VAPID_PRIVATE_KEY}")
    print(f"VAPID_PUBLIC_KEY={VAPID_PUBLIC_KEY_BASE64}")
    print(f"VAPID_EMAIL={VAPID_EMAIL}")
    print("\nВНИМАНИЕ: Сохраните эти ключи, иначе они будут потеряны при перезапуске!")
    # Используем bytes для внутренней работы
    VAPID_PUBLIC_KEY = public_key_bytes
else:
    # Если ключи заданы из .env
    import base64
    # Если публичный ключ в base64 формате (строка), конвертируем в bytes
    if isinstance(VAPID_PUBLIC_KEY, str) and not VAPID_PUBLIC_KEY.startswith("-----BEGIN"):
        try:
            # Добавляем padding если нужно
            padding = '=' * (4 - len(VAPID_PUBLIC_KEY) % 4)
            VAPID_PUBLIC_KEY_BYTES = base64.urlsafe_b64decode(VAPID_PUBLIC_KEY + padding)
            VAPID_PUBLIC_KEY = VAPID_PUBLIC_KEY_BYTES
        except:
            # Если не получилось декодировать, пытаемся использовать py_vapid
            try:
                vapid_key = py_vapid.Vapid01()
                vapid_key.from_pem(VAPID_PRIVATE_KEY)
                VAPID_PUBLIC_KEY = vapid_key.public_key.public_key_bytes
            except:
                pass

# Локальное хранилище подписок (если Supabase не используется)
local_subscriptions = []


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


@app.get("/")
async def root():
    return {"message": "PWA Push Notifications API", "status": "running"}


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
                vapid_key = py_vapid.Vapid01()
                vapid_key.from_pem(VAPID_PRIVATE_KEY)
                public_key_bytes = vapid_key.public_key.public_key_bytes
                public_key_base64 = base64.urlsafe_b64encode(public_key_bytes).decode('utf-8').rstrip('=')
            except:
                public_key_base64 = VAPID_PUBLIC_KEY
    else:
        public_key_base64 = str(VAPID_PUBLIC_KEY)
    
    return {"publicKey": public_key_base64}


@app.post("/api/subscribe")
async def subscribe(subscription: PushSubscription):
    """Сохраняет подписку пользователя"""
    try:
        subscription_data = {
            "endpoint": subscription.endpoint,
            "keys": subscription.keys,
            "created_at": datetime.now().isoformat()
        }

        if supabase_client:
            # Сохраняем в Supabase
            result = supabase_client.table("push_subscriptions").insert({
                "endpoint": subscription.endpoint,
                "p256dh": subscription.keys.get("p256dh"),
                "auth": subscription.keys.get("auth"),
                "created_at": datetime.now().isoformat()
            }).execute()
            return {"status": "success", "message": "Подписка сохранена"}
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/unsubscribe")
async def unsubscribe(subscription: PushSubscription):
    """Удаляет подписку пользователя"""
    try:
        if supabase_client:
            # Удаляем из Supabase
            result = supabase_client.table("push_subscriptions").delete().eq(
                "endpoint", subscription.endpoint
            ).execute()
            return {"status": "success", "message": "Подписка удалена"}
        else:
            # Удаляем из локального хранилища
            global local_subscriptions
            local_subscriptions = [
                sub for sub in local_subscriptions
                if sub["endpoint"] != subscription.endpoint
            ]
            return {"status": "success", "message": "Подписка удалена"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/send-notification")
async def send_notification(notification: NotificationData):
    """Отправляет push-уведомление всем подписчикам"""
    try:
        # Получаем все подписки
        subscriptions = []
        if supabase_client:
            result = supabase_client.table("push_subscriptions").select("*").execute()
            for row in result.data:
                subscriptions.append({
                    "endpoint": row["endpoint"],
                    "keys": {
                        "p256dh": row["p256dh"],
                        "auth": row["auth"]
                    }
                })
        else:
            # Преобразуем локальные подписки в нужный формат
            subscriptions = [
                {
                    "endpoint": sub["endpoint"],
                    "keys": sub["keys"]
                }
                for sub in local_subscriptions
            ]

        if not subscriptions:
            return {"status": "error", "message": "Нет активных подписок"}

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
                webpush(
                    subscription_info={
                        "endpoint": sub["endpoint"],
                        "keys": sub["keys"]
                    },
                    data=json.dumps(notification_payload),
                    vapid_private_key=VAPID_PRIVATE_KEY,
                    vapid_claims={
                        "sub": VAPID_EMAIL
                    }
                )
                success_count += 1
            except WebPushException as e:
                failed_count += 1
                failed_endpoints.append(sub["endpoint"])
                # Если подписка недействительна, удаляем её
                if hasattr(e, 'response') and e.response and e.response.status_code == 410:  # Gone
                    if supabase_client:
                        supabase_client.table("push_subscriptions").delete().eq(
                            "endpoint", sub["endpoint"]
                        ).execute()
                    else:
                        global local_subscriptions
                        local_subscriptions = [
                            s for s in local_subscriptions
                            if s["endpoint"] != sub["endpoint"]
                        ]
            except Exception as e:
                # Обработка других ошибок при отправке
                failed_count += 1
                failed_endpoints.append(sub["endpoint"])
                print(f"Ошибка при отправке уведомления: {str(e)}")

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

