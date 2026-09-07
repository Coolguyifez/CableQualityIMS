const CACHE_NAME = "cableqims-offline-v1";
const OFFLINE_PAGE = "/static/offline.html";


// =====================================================
// PUSH NOTIFICATIONS
// =====================================================

self.addEventListener("push", function(event) {

    if (!event.data) {
        return;
    }

    const data = event.data.json();

    const title = data.title || "CQIMS Notification";

    const options = {
        body: data.message || "",
        icon: "/static/icons/cableqims.png",
        badge: "/static/icons/cableqims2.png",

        data: {
            link: data.link || "/notifications"
        },

        tag: "cqims-notification",
        renotify: true
    };

    event.waitUntil(
        self.registration.showNotification(
            title,
            options
        )
    );

});


// =====================================================
// NOTIFICATION CLICK
// =====================================================

self.addEventListener(
    "notificationclick",
    function(event) {

        event.notification.close();

        const link =
            event.notification.data?.link ||
            "/notifications";

        event.waitUntil(

            clients.matchAll({
                type: "window",
                includeUncontrolled: true
            })

            .then(function(clientList) {

                for (const client of clientList) {

                    if ("focus" in client) {

                        client.navigate(link);

                        return client.focus();

                    }

                }

                if (clients.openWindow) {
                    return clients.openWindow(link);
                }

            })

        );

    }
);


// =====================================================
// INSTALL
// =====================================================

self.addEventListener("install", function(event) {

    event.waitUntil(

        caches.open(CACHE_NAME)

            .then(function(cache) {

                // ONLY save the offline page
                return cache.add(OFFLINE_PAGE);

            })

            .then(function() {

                return self.skipWaiting();

            })

    );

});


// =====================================================
// ACTIVATE
// =====================================================

self.addEventListener("activate", function(event) {

    event.waitUntil(

        caches.keys()

            .then(function(cacheNames) {

                return Promise.all(

                    cacheNames

                        .filter(function(cacheName) {

                            return cacheName !== CACHE_NAME;

                        })

                        .map(function(cacheName) {

                            return caches.delete(cacheName);

                        })

                );

            })

            .then(function() {

                return self.clients.claim();

            })

    );

});


// =====================================================
// OFFLINE / FETCH
// =====================================================

self.addEventListener("fetch", function(event) {

    if (event.request.method !== "GET") {
        return;
    }

    // Only handle normal HTTP/HTTPS requests
    if (
        !event.request.url.startsWith("http://") &&
        !event.request.url.startsWith("https://")
    ) {
        return;
    }

    event.respondWith(

        fetch(event.request)

            .catch(function() {

                // If the request fails because the
                // server/internet is unavailable:

                if (event.request.mode === "navigate") {

                    return caches.match(OFFLINE_PAGE);

                }

                return new Response(
                    "You are currently offline.",
                    {
                        status: 503,
                        statusText: "Service Unavailable",
                        headers: {
                            "Content-Type": "text/plain"
                        }
                    }
                );

            })

    );

});