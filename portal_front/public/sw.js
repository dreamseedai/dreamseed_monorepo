self.addEventListener('install', (e) => {
  e.waitUntil(caches.open('ds-static-v1').then((c) => c.addAll(['/','/index.html'])));
});
self.addEventListener('fetch', (e) => {
  const { request } = e;
  if (request.method !== 'GET') return;
  if (new URL(request.url).origin !== location.origin) return;
  e.respondWith(
    caches.match(request).then((cached) => cached || fetch(request).then((res) => {
      const copy = res.clone();
      caches.open('ds-static-v1').then((c) => c.put(request, copy)).catch(()=>{});
      return res;
    }).catch(() => cached))
  );
});


