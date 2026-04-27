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
