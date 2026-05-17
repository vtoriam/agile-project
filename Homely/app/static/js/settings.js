function copyCode() {
  const code = document.getElementById("joinCodeText").textContent.trim();
  navigator.clipboard.writeText(code).then(() => {
    const btn = document.querySelector('[onclick="copyCode()"]');
    const original = btn.innerHTML;
    btn.innerHTML = '<i data-lucide="check"></i> Copied!';
    lucide.createIcons();
    setTimeout(() => {
      btn.innerHTML = original;
      lucide.createIcons();
    }, 2000);
  });
}

function switchHousehold() {
  const select = document.getElementById("householdSelect");
  const householdId = select.value;
  if (!householdId) {
    return;
  } else {
    fetch("/household/switch", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
        "X-CSRFToken": getCsrfToken(),
      },
      body: `household_id=${householdId}`,
    })
      .then((response) => {
        if (response.redirected) {
          window.location.href = response.url;
        } else if (response.ok) {
          window.location.href = "/home";
        } else {
          alert("Error: " + response.status);
        }
      })
      .catch((error) => {
        alert("Error: " + error.message);
      });
  }
}

let currentAddHouseholdAction = null;
let currentAddHouseholdInputType = null;

window.openAddHouseholdModal = function (btn) {
  const actionUrl = btn.dataset.action;
  const inputType = btn.dataset.inputType; // "create" or "join"

  document.getElementById("addHouseholdTitle").textContent =
    btn.dataset.title;
  document.getElementById("addHouseholdMessage").textContent =
    btn.dataset.message;
  document.getElementById("addHouseholdSub").textContent =
    btn.dataset.sub;
  document.getElementById("addHouseholdSubmitBtn").textContent =
    btn.dataset.label;

  currentAddHouseholdAction = actionUrl;
  currentAddHouseholdInputType = inputType;

  // Update placeholder based on input type
  const input = document.getElementById("householdName");
  if (inputType === "create") {
    input.placeholder = "e.g., Smith Family";
    input.name = "household_name";
  } else if (inputType === "join") {
    input.placeholder = "e.g., HM-A1B2";
    input.name = "join_code";
  }
  input.value = "";

  const modal = document.getElementById("addHouseholdModal");
  const overlay = document.getElementById("addHouseholdOverlay");

  modal.classList.add("open");
  overlay.classList.add("open");

  lucide.createIcons();
}

window.closeAddHouseholdModal = function () {
  // Clear any error messages
  const error_div = document.getElementById("addHouseholdError");
  const error_message = document.getElementById("addHouseholdErrorMessage");
  error_message.textContent = "";
  error_div.style.display = "none";

  document.getElementById("addHouseholdModal").classList.remove("open");
  document.getElementById("addHouseholdOverlay").classList.remove("open");
  currentAddHouseholdAction = null;
  currentAddHouseholdInputType = null;
}

window.submitAddHouseholdAction = function () {
  if (!currentAddHouseholdAction) {
    alert("Error: No action specified");
    return false;
  }

  const input = document.getElementById("householdName");
  const inputValue = input.value.trim();

  if (!inputValue) {
    displayError("Input cannot be empty. Please enter a valid value.");
    return false;
  }

  // Determine the form data key based on input type
  const formDataKey = currentAddHouseholdInputType === "create" ? "household_name" : "join_code";
  const body = new URLSearchParams();
  body.append(formDataKey, inputValue);

  fetch(currentAddHouseholdAction, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
      "X-CSRFToken": getCsrfToken(),
    },
    body: body.toString(),
  })
    .then((response) => {
      if (response.redirected) {
        window.location.href = response.url;
      } else if (!response.ok) {
        // Error response - extract error message and display in modal
        return response.json().then((data) => {
          if (data.error) {
            displayError(data.error);
          } else {
            alert("Error: " + response.status);
          }
        });
      } else {
        // Success - close modal and redirect to home
        closeAddHouseholdModal();
        window.location.href = "/home";
      }
    })
    .catch((error) => {
      alert("Error: " + error.message);
    });

  return false;
};

function displayError(message) {
  const error_div = document.getElementById("addHouseholdError");
  const error_message = document.getElementById("addHouseholdErrorMessage");
  error_message.textContent = message;
  error_div.style.display = "inline";
}

// Store the current action URL globally
let currentDangerAction = null;

// Make sure these are accessible globally
window.openDangerModal = function (btn) {
  const actionUrl = btn.dataset.action;

  document.getElementById("dangerModalTitle").textContent = btn.dataset.title;
  document.getElementById("dangerModalMessage").textContent =
    btn.dataset.message;
  document.getElementById("dangerModalSub").textContent = btn.dataset.sub;
  document.getElementById("dangerBtnLabel").textContent = btn.dataset.label;

  // Store the action URL globally
  currentDangerAction = actionUrl;

  const modal = document.getElementById("dangerModal");
  const overlay = document.getElementById("dangerOverlay");

  modal.classList.add("open");
  overlay.classList.add("open");

  lucide.createIcons();
};

window.closeDangerModal = function () {
  document.getElementById("dangerModal").classList.remove("open");
  document.getElementById("dangerOverlay").classList.remove("open");
  currentDangerAction = null;
};

window.submitDangerAction = function () {
  if (!currentDangerAction) {
    alert("Error: No action specified");
    return false;
  }

  fetch(currentDangerAction, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
      "X-CSRFToken": getCsrfToken(),
    },
  })
    .then((response) => {
      if (response.redirected) {
        window.location.href = response.url;
      } else if (response.ok) {
        window.location.href = "/home";
      } else {
        alert("Error: " + response.status);
      }
    })
    .catch((error) => {
      alert("Error: " + error.message);
    });

  closeDangerModal();
  return false;
};
