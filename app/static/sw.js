const CACHE_NAME = "cableqims-v1";

const urls = [
    "/",
    "/static/css/style.css",
    "/static/js/app.js"
];

self.addEventListener("install", event => {

    event.waitUntil(

        caches.open(CACHE_NAME)

        .then(cache => cache.addAll(urls))

    );

});

self.addEventListener("fetch", event => {

    event.respondWith(

        caches.match(event.request)

        .then(response => {

            return response || fetch(event.request);

        })

    );

});