const CACHE_NAME = "marketbeacon-cache-v1";
const ASSETS_TO_CACHE = [
  "/",
  "/index.html",
  "/favicon.svg",
  "/manifest.json"
];

// Install Service Worker and Cache Assets
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      logger_log("Caching app shell assets...");
      return cache.addAll(ASSETS_TO_CACHE);
    }).then(() => self.skipWaiting())
  );
});

// Activate and Clean Old Caches
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cache) => {
          if (cache !== CACHE_NAME) {
            logger_log("Clearing old cache:", cache);
            return caches.delete(cache);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Cache-First with Network Fallback
self.addEventListener("fetch", (event) => {
  // Only handle standard HTTP/HTTPS GET requests (e.g. skip Chrome extensions / backend posts)
  if (!event.request.url.startsWith(self.location.origin) || event.request.method !== "GET") {
    return;
  }
  
  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      if (cachedResponse) {
        return cachedResponse;
      }
      return fetch(event.request).then((networkResponse) => {
        // Cache new fetched static assets dynamically
        if (networkResponse && networkResponse.status === 200 && networkResponse.type === "basic") {
          const responseToCache = networkResponse.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseToCache);
          });
        }
        return networkResponse;
      }).catch(() => {
        // Fallback for offline mode if index.html is cached
        return caches.match("/index.html");
      });
    })
  );
});

// Listen for Push Notifications
self.addEventListener("push", (event) => {
  if (event.data) {
    try {
      const payload = event.data.json();
      const title = payload.title || "MarketBeacon AI Notification";
      const options = {
        body: payload.body || "New market intelligence is available.",
        icon: "/favicon.svg",
        badge: "/favicon.svg",
        vibrate: [100, 50, 100],
        data: {
          url: payload.url || "/"
        }
      };
      event.waitUntil(self.registration.showNotification(title, options));
    } catch (e) {
      // Fallback text if data isn't JSON
      const text = event.data.text();
      event.waitUntil(
        self.registration.showNotification("MarketBeacon AI Notification", {
          body: text,
          icon: "/favicon.svg",
          badge: "/favicon.svg",
          data: { url: "/" }
        })
      );
    }
  }
});

// Listen for Notification Clicks (Deep-linking)
self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const targetUrl = event.notification.data ? event.notification.data.url : "/";

  event.waitUntil(
    self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((clientList) => {
      // If a window is already open, focus it and redirect
      for (const client of clientList) {
        const urlObj = new URL(client.url);
        const path = urlObj.pathname + urlObj.search + urlObj.hash;
        if (client.url.includes(targetUrl) && "focus" in client) {
          return client.focus();
        }
      }
      
      // If no window open, launch a new client
      if (self.clients.openWindow) {
        return self.clients.openWindow(targetUrl);
      }
    })
  );
});

function logger_log(...args) {
  // Console logging inside Service Worker
  console.log("[ServiceWorker]", ...args);
}
