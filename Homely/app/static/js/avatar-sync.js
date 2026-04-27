const AVATAR_STORAGE_KEY = "homequest.selectedAvatar";
const DEFAULT_AVATAR = "user-round";

const allowedAvatars = new Set([
  "user-round",
  "cat",
  "dog",
  "bird",
  "fish",
  "rabbit",
  "bug",
  "turtle",
  "squirrel",
  "snail",
]);

function getSavedAvatar() {
  const saved = localStorage.getItem(AVATAR_STORAGE_KEY);
  if (saved && allowedAvatars.has(saved)) return saved;
  return DEFAULT_AVATAR;
}

function paintAvatarSlots(iconName) {
  const slots = document.querySelectorAll("[data-user-avatar-slot]");
  slots.forEach((slot) => {
    slot.innerHTML = `<i data-lucide="${iconName}"></i>`;
  });
}

function setSelectedAvatarOption(iconName) {
  const options = document.querySelectorAll("[data-avatar-option]");
  options.forEach((option) => {
    const selected = option.dataset.avatarOption === iconName;
    option.classList.toggle("selected", selected);
    option.setAttribute("aria-pressed", selected ? "true" : "false");
  });
}

function applyAvatar(iconName) {
  paintAvatarSlots(iconName);
  setSelectedAvatarOption(iconName);
  if (window.lucide && typeof window.lucide.createIcons === "function") {
    window.lucide.createIcons();
  }
}

function saveAvatar(iconName) {
  if (!allowedAvatars.has(iconName)) return;
  localStorage.setItem(AVATAR_STORAGE_KEY, iconName);
  applyAvatar(iconName);
}

function bindAvatarPicker() {
  const options = document.querySelectorAll("[data-avatar-option]");
  options.forEach((option) => {
    option.addEventListener("click", () => {
      const iconName = option.dataset.avatarOption;
      saveAvatar(iconName);
    });
  });
}

document.addEventListener("DOMContentLoaded", () => {
  bindAvatarPicker();
  applyAvatar(getSavedAvatar());
});

window.HomeQuestAvatar = {
  get: getSavedAvatar,
  set: saveAvatar,
  apply: applyAvatar,
};
