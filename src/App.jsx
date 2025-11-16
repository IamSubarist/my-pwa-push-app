import { useState, useEffect } from 'react'
import './App.css'

function App() {
  const [deferredPrompt, setDeferredPrompt] = useState(null)
  const [showInstallButton, setShowInstallButton] = useState(false)

  useEffect(() => {
    // Обработчик события beforeinstallprompt
    const handleBeforeInstallPrompt = (e) => {
      // Предотвращаем автоматический показ промпта
      e.preventDefault()
      // Сохраняем событие для последующего использования
      setDeferredPrompt(e)
      setShowInstallButton(true)
    }

    // Обработчик успешной установки
    const handleAppInstalled = () => {
      console.log('PWA установлено')
      setDeferredPrompt(null)
      setShowInstallButton(false)
    }

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt)
    window.addEventListener('appinstalled', handleAppInstalled)

    // Проверяем, не установлено ли уже приложение
    if (window.matchMedia('(display-mode: standalone)').matches) {
      setShowInstallButton(false)
    }

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt)
      window.removeEventListener('appinstalled', handleAppInstalled)
    }
  }, [])

  const handleInstallClick = async () => {
    if (!deferredPrompt) {
      return
    }

    // Показываем промпт установки
    deferredPrompt.prompt()

    // Ждем ответа пользователя
    const { outcome } = await deferredPrompt.userChoice

    if (outcome === 'accepted') {
      console.log('Пользователь принял установку')
    } else {
      console.log('Пользователь отклонил установку')
    }

    // Очищаем сохраненное событие
    setDeferredPrompt(null)
    setShowInstallButton(false)
  }

  return (
    <div className="app">
      <h1>Это простое PWA</h1>
      {showInstallButton && (
        <button className="install-button" onClick={handleInstallClick}>
          Установить приложение
        </button>
      )}
    </div>
  )
}

export default App
