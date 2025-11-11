/**
 * Service Worker for Anime/Manga Information Delivery System
 * Provides offline functionality, caching, and background sync
 */

const CACHE_NAME = 'animemanga-cache-v1';
const OFFLINE_URL = '/static/offline.html';

// Resources to cache on install
const CACHE_RESOURCES = [
    '/',
    '/static/css/style.css',
    '/static/js/main.js',
    '/static/manifest.json',
    OFFLINE_URL,
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
    'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js',
    'https://code.jquery.com/jquery-3.7.0.min.js'
];

// Install event - cache resources
self.addEventListener('install', event => {
    console.log('Service Worker installing...');
    
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('Caching app resources');
                return cache.addAll(CACHE_RESOURCES);
            })
            .then(() => {
                // Force activation of this service worker
                return self.skipWaiting();
            })
            .catch(error => {
                console.error('Failed to cache resources during install:', error);
            })
    );
});

// Activate event - cleanup old caches
self.addEventListener('activate', event => {
    console.log('Service Worker activating...');
    
    event.waitUntil(
        caches.keys()
            .then(cacheNames => {
                return Promise.all(
                    cacheNames.map(cacheName => {
                        if (cacheName !== CACHE_NAME) {
                            console.log('Deleting old cache:', cacheName);
                            return caches.delete(cacheName);
                        }
                    })
                );
            })
            .then(() => {
                // Take control of all clients
                return self.clients.claim();
            })
    );
});

// Fetch event - serve from cache or network
self.addEventListener('fetch', event => {
    // Skip non-GET requests
    if (event.request.method !== 'GET') {
        return;
    }
    
    // Skip requests to other origins
    if (!event.request.url.startsWith(self.location.origin)) {
        return;
    }
    
    event.respondWith(handleFetch(event.request));
});

async function handleFetch(request) {
    const url = new URL(request.url);
    
    // Handle API requests
    if (url.pathname.startsWith('/api/')) {
        return handleApiRequest(request);
    }
    
    // Handle static resources
    if (url.pathname.startsWith('/static/')) {
        return handleStaticResource(request);
    }
    
    // Handle navigation requests
    if (request.mode === 'navigate') {
        return handleNavigationRequest(request);
    }
    
    // Default: try network first, then cache
    return networkFirstStrategy(request);
}

async function handleApiRequest(request) {
    try {
        // Try network first for API requests
        const networkResponse = await fetch(request);
        
        // Cache successful GET requests
        if (networkResponse.ok && request.method === 'GET') {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
    } catch (error) {
        // If network fails, try cache
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        
        // Return offline API response
        return new Response(
            JSON.stringify({
                error: 'オフライン',
                message: 'ネットワークに接続されていません',
                offline: true
            }),
            {
                status: 503,
                headers: { 'Content-Type': 'application/json' }
            }
        );
    }
}

async function handleStaticResource(request) {
    // Cache first strategy for static resources
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
        return cachedResponse;
    }
    
    try {
        const networkResponse = await fetch(request);
        
        // Cache successful responses
        if (networkResponse.ok) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
    } catch (error) {
        console.error('Failed to fetch static resource:', request.url);
        throw error;
    }
}

async function handleNavigationRequest(request) {
    try {
        // Try network first
        const networkResponse = await fetch(request);
        return networkResponse;
    } catch (error) {
        // If network fails, serve from cache or offline page
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        
        // Serve offline page
        return caches.match(OFFLINE_URL);
    }
}

async function networkFirstStrategy(request) {
    try {
        const networkResponse = await fetch(request);
        
        // Cache successful responses
        if (networkResponse.ok) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
    } catch (error) {
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        throw error;
    }
}

// Background Sync for offline actions
self.addEventListener('sync', event => {
    console.log('Background sync event:', event.tag);
    
    if (event.tag === 'sync-data') {
        event.waitUntil(syncData());
    }
    
    if (event.tag === 'sync-notifications') {
        event.waitUntil(syncNotifications());
    }
});

async function syncData() {
    try {
        console.log('Syncing data in background...');
        
        // Try to fetch latest data when back online
        const response = await fetch('/api/stats');
        if (response.ok) {
            const data = await response.json();
            
            // Broadcast update to all clients
            const clients = await self.clients.matchAll();
            clients.forEach(client => {
                client.postMessage({
                    type: 'DATA_SYNC_COMPLETE',
                    data: data
                });
            });
        }
    } catch (error) {
        console.error('Background sync failed:', error);
    }
}

async function syncNotifications() {
    try {
        console.log('Syncing notifications in background...');
        
        // Process any pending notifications
        // This would be implemented based on your notification queue system
        
    } catch (error) {
        console.error('Notification sync failed:', error);
    }
}

// Push notifications
self.addEventListener('push', event => {
    console.log('Push event received:', event);
    
    const options = {
        body: 'アニメ・マンガの新しいリリース情報があります',
        icon: '/static/icons/icon-192x192.png',
        badge: '/static/icons/badge-72x72.png',
        tag: 'release-notification',
        requireInteraction: false,
        actions: [
            {
                action: 'view',
                title: '表示',
                icon: '/static/icons/action-view.png'
            },
            {
                action: 'dismiss',
                title: '閉じる',
                icon: '/static/icons/action-dismiss.png'
            }
        ],
        data: {
            url: '/',
            timestamp: Date.now()
        }
    };
    
    if (event.data) {
        try {
            const pushData = event.data.json();
            options.body = pushData.message || options.body;
            options.data.url = pushData.url || options.data.url;
        } catch (error) {
            console.error('Failed to parse push data:', error);
        }
    }
    
    event.waitUntil(
        self.registration.showNotification('アニメ・マンガ配信システム', options)
    );
});

// Notification click handler
self.addEventListener('notificationclick', event => {
    console.log('Notification clicked:', event);
    
    event.notification.close();
    
    const urlToOpen = event.notification.data?.url || '/';
    
    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true })
            .then(clientList => {
                // Check if app is already open
                for (const client of clientList) {
                    if (client.url.includes(self.location.origin) && 'focus' in client) {
                        return client.focus();
                    }
                }
                
                // Open new window if app is not open
                if (clients.openWindow) {
                    return clients.openWindow(urlToOpen);
                }
            })
    );
});

// Message handler for communication with main thread
self.addEventListener('message', event => {
    console.log('Service Worker received message:', event.data);
    
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
    
    if (event.data && event.data.type === 'GET_VERSION') {
        event.ports[0].postMessage({ version: CACHE_NAME });
    }
    
    if (event.data && event.data.type === 'CLEAN_CACHE') {
        caches.delete(CACHE_NAME).then(() => {
            event.ports[0].postMessage({ success: true });
        });
    }
});

// Periodic background sync (if supported)
self.addEventListener('periodicsync', event => {
    console.log('Periodic sync event:', event.tag);
    
    if (event.tag === 'daily-sync') {
        event.waitUntil(performDailySync());
    }
});

async function performDailySync() {
    try {
        console.log('Performing daily background sync...');
        
        // Update cache with fresh data
        const response = await fetch('/api/releases/recent');
        if (response.ok) {
            const cache = await caches.open(CACHE_NAME);
            cache.put('/api/releases/recent', response.clone());
        }
        
    } catch (error) {
        console.error('Daily sync failed:', error);
    }
}