
const input = document.getElementById("globalSearch");
const results = document.getElementById("searchResults");

input.addEventListener("keyup", async function () {

    const q = input.value.trim();

    if (q.length < 2) {

        results.classList.add("d-none");
        return;

    }

    const response = await fetch(`/search/live?q=${encodeURIComponent(q)}`);

    const data = await response.json();

    results.innerHTML = "";

    if (data.length === 0) {

        results.innerHTML = `
            <div class="list-group-item text-muted">
                No results found
            </div>
        `;

    } else {

        data.forEach(item => {

            results.innerHTML += `
                <a href="${item.url}"
                   class="list-group-item list-group-item-action">

                    <strong>${item.type}</strong><br>

                    <small>${item.title}</small>

                </a>
            `;

        });

    }

    results.classList.remove("d-none");

});

document.addEventListener("click", function(e){

    if(!results.contains(e.target) && e.target!==input){

        results.classList.add("d-none");

    }

});
document.addEventListener("DOMContentLoaded", function () {

    function setupTableSearch(searchId, tableId) {

        const search = document.getElementById(searchId);

        if (!search) return;

        search.addEventListener("keyup", function () {

            const filter = this.value.toLowerCase();

            const rows = document.querySelectorAll(`#${tableId} tbody tr`);

            rows.forEach(function (row) {

                row.style.display = row.innerText.toLowerCase().includes(filter)
                    ? ""
                    : "none";

            });

        });

    }

    // Customers
    setupTableSearch("customerSearch", "customerTable");

    // Cable Types
    setupTableSearch("cableTypeSearch", "cableTypeTable");

    // Production Lines
    setupTableSearch("productionLineSearch", "productionLineTable");

    // batch
    setupTableSearch("batchSearch", "batchTable");

    //inspection

    setupTableSearch("inspectionSearch", "inspectionTable");

    //quality metrics

    setupTableSearch("qualityMetricSearch", "qualityMetricTable");

    //quality specifications

    setupTableSearch("specificationSearch", "specificationTable");

    //deviations
    setupTableSearch("deviationSearch", "deviationTable");

    //CAPA
    setupTableSearch("capaSearch", "capaTable");

    //Users

    setupTableSearch("userSearch", "userTable");

    //batches

    setupTableSearch("batchSearch", "batchTable");


});


document.addEventListener("DOMContentLoaded", function () {

    const metric = document.getElementById("metric_name");
    const unit = document.getElementById("unit");

    if (!metric || !unit) return;

    const units = {

        "Length": "m",

        "Conductor Design": "mm",

        "Conductor Elongation @ break": "%",

        "DC Conductor Resistance @ 20°C": "Ω/km",

        "Core Colour": "",

        "Insulation Thickness": "mm",

        "Spark Test On Insulation": "",

        "Inner Sheath Thickness": "mm",

        "Diameter Over Inner Sheath": "mm",

        "Nominal Armor Diameter": "mm",

        "Diameter Over Armouring": "mm",

        "Outer Sheath Thickness": "mm",

        "Diameter Over Sheathing": "mm",

        "Hot Set Test @ 200°C For 15 Minutes": "%",

        "Insulation Resistance @ 20°C Measured @ 1000 Vdc For 1 Minute": "MΩ/km",

        "Water Absorption Test @ 90°C": "MΩ/km",

        "Water Penetration Test For 6m Cable Sample For 24 Hours": "",

        "Sheath Elongation": "%",

        "Sheath Tensile Strength": "N/mm²",

        "Flame Retardant Test": "mm/sec",

        "Continuity": "",

        "HVT Test @ 1.5KV For 5 Minutes": "kV"

    };

    function updateUnit() {

        unit.value = units[metric.value] || "";

    }

    metric.addEventListener("change", updateUnit);

    updateUnit();




});


document.addEventListener("DOMContentLoaded", function () {

    const specification = document.getElementById("specification_id");

    if (!specification) return;

    function loadSpecification() {

        const id = specification.value;

        if (!id) return;

        fetch(`/quality-specification/${id}/details`)

        .then(response => response.json())

        .then(data => {

            document.getElementById("unit").value =
                data.unit;

            document.getElementById("minimum_value").value =
                data.minimum_value;

            document.getElementById("maximum_value").value =
                data.maximum_value;

            document.getElementById("expected_text").value =
                data.expected_result;

        });

    }

    specification.addEventListener("change", loadSpecification);

    loadSpecification();

});



document.addEventListener("DOMContentLoaded", function () {

    const metric = document.getElementById("specification_id");

    if (!metric) return;

    function toggleFields(validation) {

        document.getElementById("minimum_box").style.display = "none";
        document.getElementById("maximum_box").style.display = "none";
        document.getElementById("expected_box").style.display = "none";

        switch (validation) {

            case "minimum":
                document.getElementById("minimum_box").style.display = "";
                break;

            case "maximum":
                document.getElementById("maximum_box").style.display = "";
                break;

            case "range":
                document.getElementById("minimum_box").style.display = "";
                document.getElementById("maximum_box").style.display = "";
                break;

            case "text":
                document.getElementById("expected_box").style.display = "";
                break;

            case "any":
            default:
                break;
        }
    }

    function loadSpecification() {

        fetch("/quality-specifications/" + metric.value + "/json")

            .then(response => response.json())

            .then(data => {

                document.getElementById("unit").value = data.unit || "";

                document.getElementById("minimum_value").value =
                    data.minimum_value ?? "";

                document.getElementById("maximum_value").value =
                    data.maximum_value ?? "";

                document.getElementById("expected_text").value =
                    data.expected_result || "";

                document.getElementById("validation_type").value =
                    data.validation_type;

                toggleFields(data.validation_type);

            });

    }

    metric.addEventListener("change", loadSpecification);

    loadSpecification();

});


async function registerPushNotifications() {

    if (!("serviceWorker" in navigator)) {

        console.log(
            "Service workers are not supported."
        );

        return null;
    }


    if (!("PushManager" in window)) {

        console.log(
            "Push notifications are not supported."
        );

        return null;
    }


    try {

        const registration =
            await navigator.serviceWorker.register(
                "/static/js/service-worker.js"
            );

        console.log(
            "Service worker registered:",
            registration
        );

        return registration;

    } catch (error) {

        console.error(
            "Service worker registration failed:",
            error
        );

        return null;
    }
}


/*
|--------------------------------------------------------------------------
| Automatically request notification permission
|--------------------------------------------------------------------------
*/

async function setupAutomaticPushNotifications() {

    try {

        // Register service worker first
        const registration =
            await registerPushNotifications();


        if (!registration) {

            return;
        }


        /*
        Check current notification permission.
        */

        let permission =
            Notification.permission;


        /*
        If user previously blocked notifications,
        don't keep asking.
        */

        if (permission === "denied") {

            console.log(
                "CQIMS notifications are blocked."
            );

            return;
        }


        /*
        If permission has not been decided yet,
        ask the browser.
        */

        if (permission === "default") {

            permission =
                await Notification.requestPermission();
        }


        /*
        User allowed notifications.
        */

        if (permission === "granted") {

            await subscribeToPush(
                registration
            );

        } else {

            console.log(
                "CQIMS notification permission was not granted."
            );
        }

    } catch (error) {

        console.error(
            "Automatic push setup failed:",
            error
        );

    }
}


/*
|--------------------------------------------------------------------------
| Subscribe device to push notifications
|--------------------------------------------------------------------------
*/

async function subscribeToPush(registration) {

    try {

        /*
        Check whether the device is already subscribed.
        */

        let subscription =
            await registration.pushManager.getSubscription();


        /*
        If not subscribed, create a new subscription.
        */

        if (!subscription) {

            const response =
                await fetch(
                    "/push/public-key"
                );


            if (!response.ok) {

                throw new Error(
                    "Could not retrieve VAPID public key."
                );
            }


            const data =
                await response.json();


            const publicKey =
                data.publicKey;


            if (!publicKey) {

                throw new Error(
                    "VAPID public key was not returned."
                );
            }


            const applicationServerKey =
                urlBase64ToUint8Array(
                    publicKey
                );


            subscription =
                await registration.pushManager.subscribe({

                    userVisibleOnly: true,

                    applicationServerKey:
                        applicationServerKey

                });

        }


        /*
        Convert subscription to JSON.
        */

        const subscriptionJSON =
            subscription.toJSON();


        /*
        Send subscription to Flask.
        */

        const response =
            await fetch(
                "/push/subscribe",
                {

                    method: "POST",

                    headers: {

                        "Content-Type":
                            "application/json"

                    },

                    body: JSON.stringify({

                        endpoint:
                            subscriptionJSON.endpoint,

                        keys:
                            subscriptionJSON.keys

                    })

                }
            );


        const result =
            await response.json();


        if (!response.ok || !result.success) {

            throw new Error(
                result.message ||
                "Failed to save push subscription."
            );
        }


        console.log(
            "CQIMS push notifications enabled."
        );

    } catch (error) {

        console.error(
            "Push subscription failed:",
            error
        );

    }
}


/*
|--------------------------------------------------------------------------
| Base64 → Uint8Array
|--------------------------------------------------------------------------
*/

function urlBase64ToUint8Array(base64String) {

    const padding =
        "=".repeat(
            (4 - base64String.length % 4) % 4
        );


    const base64 =
        (
            base64String + padding
        )
        .replace(/-/g, "+")
        .replace(/_/g, "/");


    const rawData =
        window.atob(base64);


    return Uint8Array.from(
        [...rawData].map(
            char => char.charCodeAt(0)
        )
    );
}


/*
|--------------------------------------------------------------------------
| Start automatic notification setup
|--------------------------------------------------------------------------
*/

document.addEventListener(
    "DOMContentLoaded",
    function () {

        /*
        Small delay gives CQIMS time to finish
        loading the authenticated page.
        */

        setTimeout(
            setupAutomaticPushNotifications,
            1500
        );

    }
);



document.addEventListener("DOMContentLoaded", function () {

    document.querySelectorAll(".local-time").forEach(function (element) {

        const utcString = element.dataset.utc;

        if (!utcString) return;

        // Tell JavaScript that the database timestamp is UTC
        const utcDate = new Date(
            utcString.endsWith("Z")
                ? utcString
                : utcString + "Z"
        );

        if (isNaN(utcDate.getTime())) return;

        element.textContent = new Intl.DateTimeFormat(
            undefined,
            {
                day: "2-digit",
                month: "short",
                year: "numeric",
                hour: "2-digit",
                minute: "2-digit",
                hour12: false
            }
        ).format(utcDate);

    });

});


/* =========================================================
   CABLEQIMS OFFLINE FORM PROTECTION
   ========================================================= */

let cqimsSubmittingForm = false;


/*
 * Display a small offline message
 */
function showOfflineMessage(messageText) {

    const existing =
        document.getElementById("cqims-offline-message");

    if (existing) {
        existing.remove();
    }

    const message =
        document.createElement("div");

    message.id = "cqims-offline-message";

    message.innerHTML = `
        <div class="cqims-offline-content">

            <div class="cqims-offline-icon">
                <i class="bi bi-wifi-off text-warning"></i>
            </div>

            <div class="cqims-offline-text">

                <strong>
                    You're Offline
                </strong>

                <span>
                    ${messageText ||
                    "Please check your internet connection. Your action was not submitted."}
                </span>

            </div>

        </div>
    `;

    document.body.appendChild(message);


    setTimeout(function () {

        if (!message.parentNode) {
            return;
        }

        message.classList.add(
            "cqims-offline-hide"
        );


        setTimeout(function () {

            if (message.parentNode) {
                message.remove();
            }

        }, 300);

    }, 5000);
}


/*
 * Check whether CableQIMS server is reachable
 */
async function isCableQIMSOnline() {

    /*
     * First check browser connection.
     */
    if (!navigator.onLine) {
        return false;
    }


    /*
     * Try to contact CableQIMS itself.
     */
    const controller =
        new AbortController();

    const timeout =
        setTimeout(function () {

            controller.abort();

        }, 5000);


    try {

        await fetch(
            "/?offline_check=" +
            Date.now(),
            {
                method: "GET",
                cache: "no-store",
                credentials: "same-origin",
                signal: controller.signal
            }
        );

        clearTimeout(timeout);

        return true;

    } catch (error) {

        clearTimeout(timeout);

        console.warn(
            "CableQIMS server is unreachable:",
            error
        );

        return false;
    }
}


/*
 * Intercept form submissions
 */
document.addEventListener(
    "submit",
    async function (event) {

        /*
         * Allow the second submission through.
         */
        if (cqimsSubmittingForm) {
            return;
        }


        /*
         * Stop the normal POST immediately.
         */
        event.preventDefault();
        event.stopPropagation();
        event.stopImmediatePropagation();


        const form =
            event.target;


        /*
         * Check CableQIMS connection.
         */
        const online =
            await isCableQIMSOnline();


        if (!online) {

            showOfflineMessage(
                "Please check your internet connection. Your action was not submitted."
            );

            return;
        }


        /*
         * Server is reachable.
         *
         * Allow the original form to submit.
         */
        cqimsSubmittingForm = true;

        form.submit();

    },
    true
);


/*
 * Detect browser going offline
 */
window.addEventListener(
    "offline",
    function () {

        showOfflineMessage(
            "Please check your internet connection."
        );

    }
);


/*
 * Detect connection restored
 */
window.addEventListener(
    "online",
    function () {

        console.log(
            "CableQIMS: Internet connection restored."
        );

    }
);




