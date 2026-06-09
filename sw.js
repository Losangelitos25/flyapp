// Flight Monitor — Service Worker
// Maneja notificaciones push y cacheo básico

self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil(self.clients.claim()));

// Al tocar una notificación, abre la app en la tab de alertas
self.addEventListener('notificationclick', e => {
  e.notification.close();
  const url = e.notification.data?.url || '/';
  e.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then(clients => {
      for (const c of clients) {
        if (c.url.includes('flight-monitor') || c.url.includes('index.html')) {
          c.focus();
          c.postMessage({ type: 'open-alerts' });
          return;
        }
      }
      self.clients.openWindow(self.registration.scope + 'index.html#alertas');
    })
  );
});
