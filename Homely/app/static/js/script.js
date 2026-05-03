const sidebar = document.getElementById("sidebar");
const overlay = document.getElementById("sidebarOverlay");
const hamburger = document.getElementById("hamburgerBtn");

function openSidebar() {
  sidebar.classList.add("open");
  overlay.classList.add("active");
}

function closeSidebar() {
  sidebar.classList.remove("open");
  overlay.classList.remove("active");
}

hamburger.addEventListener("click", openSidebar);
overlay.addEventListener("click", closeSidebar);

document.querySelectorAll(".nav-item-custom").forEach((item) => {
  item.addEventListener("click", () => {
    if (window.innerWidth < 768) closeSidebar();
  });
});

// ════════════════════════════
// MASCOT STATE — TIME OF DAY
// ════════════════════════════

function updateMascotState() {
  const character = document.querySelector(".Character_spritesheet");
  if (!character) return;

  const hour = new Date().getHours();

  // Remove all state classes
  character.classList.remove("sitting-down", "sleeping");

  // Apply state based on time of day
  if (hour >= 6 && hour < 12) {
    // Morning: normal (no class)
  } else if (hour >= 12 && hour < 18) {
    // Afternoon: sitting
    character.classList.add("sitting-down");
  } else {
    // Evening & Night (6 PM - 6 AM): sleeping
    character.classList.add("sleeping");
  }
}

// Initialize mascot state and update every minute
updateMascotState();
setInterval(updateMascotState, 60000);
