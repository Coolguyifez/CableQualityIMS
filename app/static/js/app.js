
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
