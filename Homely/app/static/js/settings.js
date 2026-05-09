// Store the current action URL globally
let currentDangerAction = null;

// Make sure these are accessible globally
window.openDangerModal = function (btn) {
  console.log("✓ openDangerModal called");
  const actionUrl = btn.dataset.action;

  console.log("✓ Opening danger modal with action:", actionUrl);

  document.getElementById("dangerModalTitle").textContent = btn.dataset.title;
  document.getElementById("dangerModalMessage").textContent =
    btn.dataset.message;
  document.getElementById("dangerModalSub").textContent = btn.dataset.sub;
  document.getElementById("dangerBtnLabel").textContent = btn.dataset.label;

  // Store the action URL globally
  currentDangerAction = actionUrl;
  console.log("✓ Action stored:", currentDangerAction);

  const modal = document.getElementById("dangerModal");
  const overlay = document.getElementById("dangerOverlay");

  console.log("Modal element:", modal);
  console.log("Overlay element:", overlay);

  modal.classList.add("open");
  overlay.classList.add("open");

  console.log("Modal classes:", modal.className);
  console.log("Overlay classes:", overlay.className);

  lucide.createIcons();
  console.log("✓ Modal should now be visible!");
};

window.closeDangerModal = function () {
  console.log("✓ closeDangerModal called");
  document.getElementById("dangerModal").classList.remove("open");
  document.getElementById("dangerOverlay").classList.remove("open");
  currentDangerAction = null;
};

window.submitDangerAction = function () {
  console.log("🔴🔴🔴 submitDangerAction called! 🔴🔴🔴");
  console.log("Current action:", currentDangerAction);

  if (!currentDangerAction) {
    console.error("ERROR: No action URL!");
    alert("Error: No action specified");
    return false;
  }

  console.log("🔴 Making POST request to:", currentDangerAction);

  fetch(currentDangerAction, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
  })
    .then((response) => {
      console.log("🔴 Response status:", response.status);
      if (response.redirected) {
        console.log("🔴 Redirected to:", response.url);
        window.location.href = response.url;
      } else if (response.ok) {
        console.log("🔴 Success! Redirecting to /home");
        window.location.href = "/home";
      } else {
        console.error("🔴 Error status:", response.status);
        alert("Error: " + response.status);
      }
    })
    .catch((error) => {
      console.error("🔴 Fetch error:", error);
      alert("Error: " + error.message);
    });

  closeDangerModal();
  return false;
};
