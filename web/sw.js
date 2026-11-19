// NanuPanda Service Worker for PWA Desktop & Mobile App
self.addEventListener('install', (e) => {
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(clients.claim());
});

self.addEventListener('fetch', (e) => {
  // Let network handle dynamic API calls and jobs
  e.respondWith(fetch(e.request).catch(() => caches.match(e.request)));
});
