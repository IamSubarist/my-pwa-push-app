import { useState, useEffect } from "react";
import axios from "axios";
import "./App.css";

// URL бэкенда
const API_URL =
  import.meta.env.VITE_API_URL ||
  "https://my-pwa-push-app-backend.onrender.com";

// Создаем экземпляр axios с базовой конфигурацией
const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Interceptor для добавления токена авторизации к каждому запросу
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("auth_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Функция для получения токена из localStorage
const getToken = () => localStorage.getItem("auth_token");
const setToken = (token) => {
  if (token) {
    localStorage.setItem("auth_token", token);
  } else {
    localStorage.removeItem("auth_token");
  }
};

function App() {
  const [deferredPrompt, setDeferredPrompt] = useState(null);
  const [showInstallButton, setShowInstallButton] = useState(false);
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [subscriptionStatus, setSubscriptionStatus] = useState("checking");
  const [notificationPermission, setNotificationPermission] =
    useState("default");

  // Состояния для авторизации
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [showLogin, setShowLogin] = useState(true);
  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [registerUsername, setRegisterUsername] = useState("");
  const [registerEmail, setRegisterEmail] = useState("");
  const [registerPassword, setRegisterPassword] = useState("");
  const [authError, setAuthError] = useState("");

  useEffect(() => {
    // Проверяем, есть ли сохраненный токен
    const token = getToken();
    if (token) {
      checkAuth(token);
    }

    // Обработчик события beforeinstallprompt
    const handleBeforeInstallPrompt = (e) => {
      e.preventDefault();
      setDeferredPrompt(e);
      setShowInstallButton(true);
    };

    const handleAppInstalled = () => {
      console.log("PWA установлено");
      setDeferredPrompt(null);
      setShowInstallButton(false);
    };

    window.addEventListener("beforeinstallprompt", handleBeforeInstallPrompt);
    window.addEventListener("appinstalled", handleAppInstalled);

    if (window.matchMedia("(display-mode: standalone)").matches) {
      setShowInstallButton(false);
    }

    // Проверяем статус подписки на push-уведомления
    if (isAuthenticated) {
      checkSubscriptionStatus();
    }

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
  }, [isAuthenticated]);

  const checkAuth = async (token) => {
    try {
      const response = await api.get("/api/me");
      setUser(response.data.user);
      setIsAuthenticated(true);
    } catch (error) {
      console.error("Ошибка при проверке авторизации:", error);
      // Токен недействителен
      setToken(null);
      setIsAuthenticated(false);
      setUser(null);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setAuthError("");

    try {
      const response = await api.post("/api/register", {
        username: registerUsername,
        email: registerEmail,
        password: registerPassword,
      });

      setToken(response.data.access_token);
      setUser({
        id: response.data.user_id,
        username: response.data.username,
        email: registerEmail,
      });
      setIsAuthenticated(true);
      setShowLogin(true);
      setRegisterUsername("");
      setRegisterEmail("");
      setRegisterPassword("");
    } catch (error) {
      setAuthError(
        error.response?.data?.detail ||
          "Не удалось зарегистрироваться: " + error.message
      );
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setAuthError("");

    try {
      const response = await api.post("/api/login", {
        email: loginEmail,
        password: loginPassword,
      });

      setToken(response.data.access_token);
      setUser({
        id: response.data.user_id,
        username: response.data.username,
        email: loginEmail,
      });
      setIsAuthenticated(true);
      setLoginEmail("");
      setLoginPassword("");
    } catch (error) {
      setAuthError(
        error.response?.data?.detail || "Не удалось войти: " + error.message
      );
    }
  };

  const handleLogout = () => {
    setToken(null);
    setIsAuthenticated(false);
    setUser(null);
    setIsSubscribed(false);
    setSubscriptionStatus("not-subscribed");
  };

  const checkSubscriptionStatus = async () => {
    if (!("serviceWorker" in navigator) || !("PushManager" in window)) {
      setSubscriptionStatus("unsupported");
      return;
    }

    try {
      let registration;
      try {
        registration = await navigator.serviceWorker.ready;
      } catch (swError) {
        console.error("Service Worker не готов:", swError);
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
      const response = await api.get("/api/vapid-public-key");
      const { publicKey } = response.data;

      // Конвертируем ключ в формат Uint8Array
      const applicationServerKey = urlBase64ToUint8Array(publicKey);

      // Подписываемся на push-уведомления
      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: applicationServerKey,
      });

      // Отправляем подписку на сервер с токеном авторизации
      const subscribeResponse = await api.post("/api/subscribe", {
        endpoint: subscription.endpoint,
        keys: {
          p256dh: btoa(
            String.fromCharCode(
              ...new Uint8Array(subscription.getKey("p256dh"))
            )
          ),
          auth: btoa(
            String.fromCharCode(...new Uint8Array(subscription.getKey("auth")))
          ),
        },
      });

      setIsSubscribed(true);
      setSubscriptionStatus("subscribed");
      console.log("Подписка успешно создана:", subscribeResponse.data);
    } catch (error) {
      console.error("Ошибка при подписке на push-уведомления:", error);
      const errorMessage =
        error.response?.data?.detail ||
        error.response?.data?.message ||
        error.message;
      alert("Не удалось подписаться на уведомления: " + errorMessage);
    }
  };

  const unsubscribeFromPush = async () => {
    try {
      const registration = await navigator.serviceWorker.ready;
      const subscription = await registration.pushManager.getSubscription();

      if (subscription) {
        // Отправляем запрос на удаление подписки на сервер с токеном
        await api.post("/api/unsubscribe", {
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
      // Отправляем уведомление текущему пользователю (на все его устройства)
      const response = await api.post("/api/send-notification", {
        title: "Тестовое уведомление",
        body: "Это тестовое push-уведомление!",
        icon: "/vite.svg",
      });

      alert(
        `Тестовое уведомление отправлено на ${response.data.success_count} устройство(а)!`
      );
    } catch (error) {
      console.error("Ошибка при отправке тестового уведомления:", error);
      const errorMessage =
        error.response?.data?.detail ||
        "Не удалось отправить уведомление: " + error.message;
      alert(errorMessage);
    }
  };

  const handleInstallClick = async () => {
    if (!deferredPrompt) {
      return;
    }

    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;

    if (outcome === "accepted") {
      console.log("Пользователь принял установку");
    } else {
      console.log("Пользователь отклонил установку");
    }

    setDeferredPrompt(null);
    setShowInstallButton(false);
  };

  // Если пользователь не авторизован, показываем форму входа/регистрации
  if (!isAuthenticated) {
    return (
      <div className="app">
        <h1>PWA с Push-уведомлениями</h1>
        <div className="auth-section">
          <div className="auth-tabs">
            <button
              className={showLogin ? "active" : ""}
              onClick={() => {
                setShowLogin(true);
                setAuthError("");
              }}
            >
              Вход
            </button>
            <button
              className={!showLogin ? "active" : ""}
              onClick={() => {
                setShowLogin(false);
                setAuthError("");
              }}
            >
              Регистрация
            </button>
          </div>

          {authError && (
            <div className="error-message" style={{ marginTop: "1rem" }}>
              {authError}
            </div>
          )}

          {showLogin ? (
            <form onSubmit={handleLogin} className="auth-form">
              <div>
                <label>Email:</label>
                <input
                  type="email"
                  value={loginEmail}
                  onChange={(e) => setLoginEmail(e.target.value)}
                  required
                />
              </div>
              <div>
                <label>Пароль:</label>
                <input
                  type="password"
                  value={loginPassword}
                  onChange={(e) => setLoginPassword(e.target.value)}
                  required
                  maxLength={70}
                />
              </div>
              <button type="submit">Войти</button>
            </form>
          ) : (
            <form onSubmit={handleRegister} className="auth-form">
              <div>
                <label>Имя пользователя:</label>
                <input
                  type="text"
                  value={registerUsername}
                  onChange={(e) => setRegisterUsername(e.target.value)}
                  required
                />
              </div>
              <div>
                <label>Email:</label>
                <input
                  type="email"
                  value={registerEmail}
                  onChange={(e) => setRegisterEmail(e.target.value)}
                  required
                />
              </div>
              <div>
                <label>Пароль:</label>
                <input
                  type="password"
                  value={registerPassword}
                  onChange={(e) => setRegisterPassword(e.target.value)}
                  required
                  minLength={6}
                  maxLength={70}
                  title="Пароль должен быть от 6 до 70 символов"
                />
              </div>
              <button type="submit">Зарегистрироваться</button>
            </form>
          )}
        </div>
      </div>
    );
  }

  // Основной интерфейс для авторизованных пользователей
  return (
    <div className="app">
      <div className="user-header">
        <div>
          <h1>PWA с Push-уведомлениями</h1>
          <p className="user-info">
            Вы вошли как: <strong>{user?.username}</strong> ({user?.email})
          </p>
        </div>
        <button onClick={handleLogout} className="logout-button">
          Выйти
        </button>
      </div>

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
            <p
              className="status-message"
              style={{ fontSize: "0.9rem", marginTop: "0.5rem" }}
            >
              Уведомления будут приходить на все ваши устройства
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
