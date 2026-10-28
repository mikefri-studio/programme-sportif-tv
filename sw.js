const CACHE_NAME = 'sporttv-v4';
const ASSETS_TO_CACHE = [
  './',
  './index.html',
  './player.html',
  './manifest.json',
  './data/schedule.json',
  './web-app-manifest-192x192.png',
  './web-app-manifest-512x512.png',
  './apple-touch-icon.png',
  './favicon.ico',
  './favicon.svg'
];

// Installation : mise en cache des fichiers essentiels
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS_TO_CACHE);
    })
  );
});

// Activation : nettoyage des anciens caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keyList) => {
      return Promise.all(keyList.map((key) => {
        if (key !== CACHE_NAME) {
          return caches.delete(key);
        }
      }));
    })
  );
});

// Interception des requêtes : stratégie "Cache First, then Network"
self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request).then((response) => {
      // Si c'est le fichier JSON, on essaie toujours de le mettre à jour en arrière-plan
      if (event.request.url.includes('schedule.json')) {
        return fetch(event.request).then((networkResponse) => {
          if (networkResponse && networkResponse.status === 200) {
            const responseClone = networkResponse.clone();
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(event.request, responseClone);
            });
          }
          return networkResponse;
        }).catch(() => caches.match(event.request));
      }
      
      // Pour le reste, on sert le cache, ou le réseau si pas en cache
      return response || fetch(event.request);
    })
  );
});
