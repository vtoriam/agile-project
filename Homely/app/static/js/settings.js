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
