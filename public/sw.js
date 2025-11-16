const CACHE_NAME = 'pwa-cache-v1';
const urlsToCache = [
  '/',
  '/index.html',
  '/manifest.json',
  '/vite.svg'
];

// Установка service worker
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('Opened cache');
        return cache.addAll(urlsToCache);
      })
  );
  // Активируем новый service worker сразу
  self.skipWaiting();
});

// Активация service worker
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  // Берем контроль над всеми открытыми страницами
  return self.clients.claim();
});

// Перехват запросов
self.addEventListener('fetch', (event) => {
  // Не кэшируем запросы к API
  if (event.request.url.includes('/api/')) {
    return;
  }

  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        // Возвращаем из кэша или делаем сетевой запрос
        return response || fetch(event.request);
      })
      .catch(() => {
        // Если запрос не удался и это навигационный запрос, возвращаем index.html
        if (event.request.mode === 'navigate') {
          return caches.match('/index.html');
        }
      })
  );
});

// Обработка push-уведомлений
self.addEventListener('push', (event) => {
  console.log('Push notification received', event);
  console.log('Event data:', event.data);
  
  let notificationData = {
    title: 'Новое уведомление',
    body: 'У вас новое сообщение',
    icon: '/vite.svg',
    badge: '/vite.svg',
    tag: 'default',
    requireInteraction: false,
    data: {}
  };

  // Если данные пришли с сервера, используем их
  if (event.data) {
    try {
      const data = event.data.json();
      console.log('Parsed notification data:', data);
      notificationData = { ...notificationData, ...data };
    } catch (e) {
      console.log('Failed to parse JSON, using text:', e);
      const text = event.data.text();
      console.log('Text data:', text);
      notificationData.body = text;
    }
  } else {
    console.log('No event data received');
  }

  console.log('Showing notification with data:', notificationData);

  const promiseChain = self.registration.showNotification(
    notificationData.title,
    {
      body: notificationData.body,
      icon: notificationData.icon,
      badge: notificationData.badge,
      tag: notificationData.tag,
      requireInteraction: notificationData.requireInteraction,
      data: notificationData.data,
      actions: notificationData.actions || []
    }
  ).then(() => {
    console.log('Notification shown successfully');
  }).catch((error) => {
    console.error('Error showing notification:', error);
  });

  event.waitUntil(promiseChain);
});

// Обработка клика по уведомлению
self.addEventListener('notificationclick', (event) => {
  console.log('Notification clicked');
  event.notification.close();

  const promiseChain = clients.matchAll({
    type: 'window',
    includeUncontrolled: true
  })
    .then((windowClients) => {
      // Если есть открытое окно, фокусируемся на нем
      for (let i = 0; i < windowClients.length; i++) {
        const client = windowClients[i];
        if (client.url === '/' && 'focus' in client) {
          return client.focus();
        }
      }
      // Если окна нет, открываем новое
      if (clients.openWindow) {
        return clients.openWindow('/');
      }
    });

  event.waitUntil(promiseChain);
});

// Обработка закрытия уведомления
self.addEventListener('notificationclose', (event) => {
  console.log('Notification closed');
});

