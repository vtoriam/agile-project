lucide.createIcons();

// Store initial avatar value and display name
const initialAvatar = document.getElementById("initialAvatar").value;
const initialDisplayName = document
  .getElementById("editProfileForm")
  .getAttribute("data-display-name");

const avatarButtons = document.querySelectorAll(".avatar-option");
const selectedAvatarInput = document.getElementById("selectedAvatar");
const displayNameInput = document.querySelector('input[name="display_name"]');

function syncInitialState() {
  avatarButtons.forEach((btn) => {
    const isInitialAvatar =
      btn.getAttribute("data-avatar-option") === initialAvatar;
    btn.classList.toggle("selected", isInitialAvatar);
    btn.setAttribute("aria-pressed", isInitialAvatar ? "true" : "false");
  });

  if (selectedAvatarInput) {
    selectedAvatarInput.value = initialAvatar;
  }

  if (displayNameInput) {
    displayNameInput.value = initialDisplayName;
  }

  if (window.HomelyAvatar && typeof window.HomelyAvatar.set === "function") {
    window.HomelyAvatar.set(initialAvatar);
  } else if (window.localStorage) {
    window.localStorage.setItem("homely.selectedAvatar", initialAvatar);
  }
}

function resetForm() {
  syncInitialState();
  window.location.replace(window.location.pathname);
}

syncInitialState();

window.addEventListener("pageshow", () => {
  syncInitialState();
});

// Handle avatar selection
avatarButtons.forEach((button) => {
  button.addEventListener("click", (e) => {
    e.preventDefault();

    // Remove selected class from all buttons
    avatarButtons.forEach((btn) => {
      btn.classList.remove("selected");
      btn.setAttribute("aria-pressed", "false");
    });

    // Add selected class to clicked button
    button.classList.add("selected");
    button.setAttribute("aria-pressed", "true");

    // Update hidden input
    const avatarValue = button.getAttribute("data-avatar-option");
    selectedAvatarInput.value = avatarValue;
  });
});
