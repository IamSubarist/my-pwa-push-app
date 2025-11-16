import { useState, useEffect } from "react";
import "./App.css";

// URL бэкенда
const API_URL =
  import.meta.env.VITE_API_URL ||
  "https://my-pwa-push-app-backend.onrender.com";

function App() {
  const [deferredPrompt, setDeferredPrompt] = useState(null);
  const [showInstallButton, setShowInstallButton] = useState(false);
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [subscriptionStatus, setSubscriptionStatus] = useState("checking");
  const [notificationPermission, setNotificationPermission] =
    useState("default");

  useEffect(() => {
    // Обработчик события beforeinstallprompt
    const handleBeforeInstallPrompt = (e) => {
      // Предотвращаем автоматический показ промпта
      e.preventDefault();
      // Сохраняем событие для последующего использования
      setDeferredPrompt(e);
      setShowInstallButton(true);
    };

    // Обработчик успешной установки
    const handleAppInstalled = () => {
      console.log("PWA установлено");
      setDeferredPrompt(null);
      setShowInstallButton(false);
    };

    window.addEventListener("beforeinstallprompt", handleBeforeInstallPrompt);
    window.addEventListener("appinstalled", handleAppInstalled);

    // Проверяем, не установлено ли уже приложение
    if (window.matchMedia("(display-mode: standalone)").matches) {
      setShowInstallButton(false);
    }

    // Проверяем статус подписки на push-уведомления
    checkSubscriptionStatus();

    // Проверяем разрешение на уведомления
    if ("Notification" in window) {
      setNotificationPermission(Notification.permission);
    }

    return () => {
      window.removeEventListener(
        "beforeinstallprompt",
        handleBeforeInstallPrompt
      );
      window.removeEventListener("appinstalled", handleAppInstalled);
    };
  }, []);

  const checkSubscriptionStatus = async () => {
    if (!("serviceWorker" in navigator) || !("PushManager" in window)) {
      setSubscriptionStatus("unsupported");
      return;
    }

    try {
      // Ждем регистрации Service Worker с таймаутом
      let registration;
      try {
        registration = await navigator.serviceWorker.ready;
      } catch (swError) {
        console.error("Service Worker не готов:", swError);
        // Пытаемся зарегистрировать заново
        registration = await navigator.serviceWorker.register("/sw.js");
        await registration.update();
        registration = await navigator.serviceWorker.ready;
      }

      const subscription = await registration.pushManager.getSubscription();
      setIsSubscribed(!!subscription);
      setSubscriptionStatus(subscription ? "subscribed" : "not-subscribed");
    } catch (error) {
      console.error("Ошибка при проверке подписки:", error);
      setSubscriptionStatus("not-subscribed");
    }
  };

  const requestNotificationPermission = async () => {
    if (!("Notification" in window)) {
      alert("Ваш браузер не поддерживает уведомления");
      return;
    }

    const permission = await Notification.requestPermission();
    setNotificationPermission(permission);

    if (permission === "granted") {
      await subscribeToPush();
    } else {
      alert("Разрешение на уведомления не предоставлено");
    }
  };

  const subscribeToPush = async () => {
    try {
      const registration = await navigator.serviceWorker.ready;

      // Получаем VAPID публичный ключ с сервера
      const response = await fetch(`${API_URL}/api/vapid-public-key`);
      const { publicKey } = await response.json();

      // Конвертируем ключ в формат Uint8Array
      const applicationServerKey = urlBase64ToUint8Array(publicKey);

      // Подписываемся на push-уведомления
      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: applicationServerKey,
      });

      // Отправляем подписку на сервер
      const subscribeResponse = await fetch(`${API_URL}/api/subscribe`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          endpoint: subscription.endpoint,
          keys: {
            p256dh: btoa(
              String.fromCharCode(
                ...new Uint8Array(subscription.getKey("p256dh"))
              )
            ),
            auth: btoa(
              String.fromCharCode(
                ...new Uint8Array(subscription.getKey("auth"))
              )
            ),
          },
        }),
      });

      if (!subscribeResponse.ok) {
        let errorText;
        try {
          const errorData = await subscribeResponse.json();
          errorText =
            errorData.detail || errorData.message || JSON.stringify(errorData);
        } catch {
          errorText = await subscribeResponse.text();
        }
        console.error("Ошибка сервера:", {
          status: subscribeResponse.status,
          statusText: subscribeResponse.statusText,
          error: errorText,
        });
        throw new Error(`Ошибка ${subscribeResponse.status}: ${errorText}`);
      }

      const result = await subscribeResponse.json();
      setIsSubscribed(true);
      setSubscriptionStatus("subscribed");
      console.log("Подписка успешно создана:", result);
    } catch (error) {
      console.error("Ошибка при подписке на push-уведомления:", error);
      alert("Не удалось подписаться на уведомления: " + error.message);
    }
  };

  const unsubscribeFromPush = async () => {
    try {
      const registration = await navigator.serviceWorker.ready;
      const subscription = await registration.pushManager.getSubscription();

      if (subscription) {
        // Отправляем запрос на удаление подписки на сервер
        await fetch(`${API_URL}/api/unsubscribe`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(subscription),
        });

        // Отписываемся локально
        await subscription.unsubscribe();
        setIsSubscribed(false);
        setSubscriptionStatus("not-subscribed");
        console.log("Подписка успешно удалена");
      }
    } catch (error) {
      console.error("Ошибка при отписке от push-уведомлений:", error);
      alert("Не удалось отписаться от уведомлений: " + error.message);
    }
  };

  const sendTestNotification = async () => {
    try {
      const response = await fetch(`${API_URL}/api/send-notification`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          title: "Тестовое уведомление",
          body: "Это тестовое push-уведомление!",
          icon: "/vite.svg",
        }),
      });

      if (response.ok) {
        alert("Тестовое уведомление отправлено!");
      } else {
        throw new Error("Ошибка при отправке уведомления");
      }
    } catch (error) {
      console.error("Ошибка при отправке тестового уведомления:", error);
      alert("Не удалось отправить уведомление: " + error.message);
    }
  };

  const handleInstallClick = async () => {
    if (!deferredPrompt) {
      return;
    }

    // Показываем промпт установки
    deferredPrompt.prompt();

    // Ждем ответа пользователя
    const { outcome } = await deferredPrompt.userChoice;

    if (outcome === "accepted") {
      console.log("Пользователь принял установку");
    } else {
      console.log("Пользователь отклонил установку");
    }

    // Очищаем сохраненное событие
    setDeferredPrompt(null);
    setShowInstallButton(false);
  };

  return (
    <div className="app">
      <h1>PWA с Push-уведомлениями</h1>

      {showInstallButton && (
        <button className="install-button" onClick={handleInstallClick}>
          Установить приложение
        </button>
      )}

      <div className="push-section">
        <h2>Push-уведомления</h2>

        {subscriptionStatus === "unsupported" && (
          <p className="status-message">
            Ваш браузер не поддерживает push-уведомления
          </p>
        )}

        {subscriptionStatus === "checking" && (
          <div>
            <p className="status-message">Проверка статуса подписки...</p>
            <p
              style={{
                fontSize: "0.85rem",
                color: "#666",
                marginTop: "0.5rem",
              }}
            >
              Если это сообщение не исчезает, откройте консоль браузера (F12)
              для диагностики
            </p>
          </div>
        )}

        {subscriptionStatus === "error" && (
          <div>
            <p className="status-message error">
              Ошибка при проверке подписки. Откройте консоль браузера (F12) для
              подробностей.
            </p>
            <button
              onClick={checkSubscriptionStatus}
              style={{ marginTop: "1rem" }}
            >
              Попробовать снова
            </button>
          </div>
        )}

        {subscriptionStatus === "not-subscribed" && (
          <div>
            {notificationPermission === "default" && (
              <button onClick={requestNotificationPermission}>
                Включить уведомления
              </button>
            )}
            {notificationPermission === "denied" && (
              <p className="status-message error">
                Разрешение на уведомления заблокировано. Разблокируйте его в
                настройках браузера.
              </p>
            )}
            {notificationPermission === "granted" && (
              <button onClick={subscribeToPush}>
                Подписаться на уведомления
              </button>
            )}
          </div>
        )}

        {subscriptionStatus === "subscribed" && (
          <div>
            <p className="status-message success">
              ✓ Вы подписаны на push-уведомления
            </p>
            <div className="button-group">
              <button onClick={sendTestNotification}>
                Отправить тестовое уведомление
              </button>
              <button onClick={unsubscribeFromPush} className="secondary">
                Отписаться от уведомлений
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// Функция для конвертации VAPID ключа из base64 в Uint8Array
function urlBase64ToUint8Array(base64String) {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding)
    .replace(/\-/g, "+")
    .replace(/_/g, "/");

  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);

  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

export default App;
