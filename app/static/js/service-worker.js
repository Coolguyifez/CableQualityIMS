self.addEventListener("push", function(event) {

    if (!event.data) {
        return;
    }

    const data = event.data.json();

    const title = data.title || "CQIMS Notification";

    const options = {
        body: data.message || "",
        icon: "/static/icons/cableqims.png",
        badge: "/static/icons/cableqims.png",
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
            }).then(function(clientList) {

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
