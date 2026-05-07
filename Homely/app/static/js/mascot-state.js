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
