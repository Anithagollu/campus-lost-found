document.addEventListener("DOMContentLoaded", function () {

    // ==========================================
    // LOST ITEM FORM
    // ==========================================

    const lostForm = document.querySelector(
        'form[action="/report-lost"]'
    );

    if (lostForm) {

        lostForm.addEventListener("submit", function () {

            // Do NOT prevent the form submission.
            // Flask will receive the image using multipart/form-data.

        });

    }


    // ==========================================
    // FOUND ITEM FORM
    // ==========================================

    const foundForm = document.querySelector(
        'form[action="/report-found"]'
    );

    if (foundForm) {

        foundForm.addEventListener("submit", function () {

            // Do NOT prevent the form submission.
            // Flask will receive the image using multipart/form-data.

        });

    }


    // ==========================================
    // LOST ITEM SEARCH
    // ==========================================

    const lostSearch = document.getElementById("lostSearch");

    if (lostSearch) {

        lostSearch.addEventListener("input", function () {

            searchLostItems();

        });

    }

});


// ==========================================
// SEARCH LOST ITEMS
// ==========================================

function searchLostItems() {

    const searchInput = document.getElementById("lostSearch");

    if (!searchInput) {
        return;
    }

    const searchValue =
        searchInput.value.toLowerCase();

    const cards =
        document.querySelectorAll(".item-card");

    cards.forEach(function (card) {

        const itemText =
            card.textContent.toLowerCase();

        if (itemText.includes(searchValue)) {

            card.style.display = "block";

        } else {

            card.style.display = "none";

        }

    });

}