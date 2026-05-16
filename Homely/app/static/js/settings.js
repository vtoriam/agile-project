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

window.openAddHouseholdModal = function (btn) {
  const actionUrl = btn.dataset.action;

  document.getElementById("addHouseholdTitle").textContent =
    btn.dataset.title;
  document.getElementById("addHouseholdMessage").textContent =
    btn.dataset.message;
  document.getElementById("addHouseholdSub").textContent =
    btn.dataset.sub;
  currentAddHouseholdAction = actionUrl;

  const modal = document.getElementById("addHouseholdModal");
  const overlay = document.getElementById("addHouseholdOverlay");

  modal.classList.add("open");
  overlay.classList.add("open");

  lucide.createIcons();
}

window.closeAddHouseholdModal = function () {
  document.getElementById("addHouseholdModal").classList.remove("open");
  document.getElementById("addHouseholdOverlay").classList.remove("open");
  currentAddHouseholdAction = null;
}

// window.submitAddHouseholdAction = function () {
//   if (!currentAddHouseholdAction) {
//     alert("Error: No action specified");
//     return false;
//   }

//   fetch(currentAddHouseholdAction, {
//     method: "POST",
//     headers: {
//       "Content-Type": "application/x-www-form-urlencoded",
//       "X-CSRFToken": getCsrfToken(),
//     },
//   })
//     .then((response) => {
//       if (response.redirected) {
//         window.location.href = response.url;
//       } else if (response.ok) {
//         window.location.href = "/home";
//       } else {
//         alert("Error: " + response.status);
//       }
//     })
//     .catch((error) => {
//       alert("Error: " + error.message);
//     });

//   closeAddHouseholdModal();
//   return false;
// };


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
