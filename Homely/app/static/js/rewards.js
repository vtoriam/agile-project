// Current user stats provided by the server
const rewardsPage = document.getElementById("rewardsPage");
const USER_POINTS = Number(rewardsPage?.dataset.userPoints || 0);

// Filter tabs
const filterTabs = document.querySelectorAll(".filter-tab");
const rewardItems = document.querySelectorAll(".reward-item");

filterTabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    // Update active tab
    filterTabs.forEach((t) => t.classList.remove("active"));
    tab.classList.add("active");

    const filter = tab.dataset.filter;

    rewardItems.forEach((item) => {
      const type = item.dataset.type;
      const isUnlocked = item.classList.contains("unlocked");

      if (filter === "all") {
        item.style.display = "flex";
      } else if (filter === "unlocked") {
        item.style.display = isUnlocked ? "flex" : "none";
      } else {
        item.style.display = type === filter ? "flex" : "none";
      }
    });

    checkEmptyState();
  });
});

// Delete custom rewards
document.querySelectorAll(".btn-delete").forEach((btn) => {
  btn.addEventListener("click", () => {
    const item = btn.closest(".reward-item");
    item.style.transition = "opacity 0.2s, transform 0.2s";
    item.style.opacity = "0";
    item.style.transform = "translateX(10px)";
    setTimeout(() => {
      item.remove();
      checkEmptyState();
    }, 200);
  });
});


function openRewardModal() {
  document.getElementById("rewardModal").classList.add("open");
  document.getElementById("rewardModalOverlay").classList.add("open");
  document.getElementById("rewardTitle").focus();
  updateRewardIconPreview();
  lucide.createIcons();
}

function closeRewardModal() {
  document.getElementById("rewardModal").classList.remove("open");
  document.getElementById("rewardModalOverlay").classList.remove("open");
  document.getElementById("rewardTitle").value = "";
  document.getElementById("rewardDesc").value = "";
  document.getElementById("rewardType").value = "points";
  document.getElementById("thresholdValue").value = "";
  document.getElementById("rewardIcon").value = "star";
  document.getElementById("rewardModalError").textContent = "";
  updateRewardIconPreview();
  lucide.createIcons();
}

function updateRewardIconPreview() {
  const select = document.getElementById("rewardIcon");
  const option = select.options[select.selectedIndex];
  const icon = option?.dataset.icon || select.value || "star";
  document.getElementById("rewardIconPreview").innerHTML =
    `<i data-lucide="${icon}"></i>`;
  lucide.createIcons();
}

// Add custom reward
function submitReward() {
  const title = document.getElementById("rewardTitle").value.trim();
  const desc = document.getElementById("rewardDesc").value.trim();
  const type = document.getElementById("rewardType").value || "points";
  const threshold = parseInt(document.getElementById("thresholdValue").value);
  const icon = document.getElementById("rewardIcon").value || "star";
  const errEl = document.getElementById("rewardModalError");

  // Basic validation
  if (!title) {
    errEl.textContent = "Please enter a reward title.";
    highlight("rewardTitle");
    return;
  }
  if (!threshold || threshold < 1) {
    errEl.textContent = "Points must be a positive number.";
    highlight("thresholdValue");
    return;
  }

  if (type !== "points") {
    errEl.textContent = "Only point-based rewards are supported right now.";
    return;
  }

  // Determine if unlocked
  let isUnlocked = false;
  let statusText = "";
  let conditionHTML = "";

  isUnlocked = USER_POINTS >= threshold;
  const remaining = threshold - USER_POINTS;
  statusText = isUnlocked
    ? "✓ Unlocked"
    : `<i data-lucide="lock"></i> ${remaining.toLocaleString()} pts away`;
  const progressPct = Math.min(
    100,
    Math.round((USER_POINTS / threshold) * 100),
  );
  conditionHTML = `<span class="condition-badge points-badge"><i data-lucide="zap"></i> ${threshold.toLocaleString()} pts</span>`;
  if (!isUnlocked) {
    conditionHTML += `
      <div class="progress-wrap">
        <div class="progress-bar-custom">
          <div class="progress-fill" style="width:${progressPct}%"></div>
        </div>
        <span class="progress-label">${USER_POINTS.toLocaleString()} / ${threshold.toLocaleString()} pts</span>
      </div>`;
  }

  const statusClass = isUnlocked ? "status-unlocked" : "status-locked";
  const itemClass = isUnlocked ? "unlocked" : "locked";

  const newItem = document.createElement("div");
  newItem.className = `reward-item custom-reward ${itemClass}`;
  newItem.dataset.type = "custom";
  newItem.innerHTML = `
    <div class="reward-icon-wrap">
      <div class="reward-icon ${isUnlocked ? "" : "muted"}"><i data-lucide="${icon}"></i></div>
    </div>
    <div class="reward-body">
      <div class="reward-title-row">
        <div class="reward-title">${title}</div>
        <span class="custom-tag">Custom</span>
      </div>
      <p class="reward-desc">${desc || "No description provided."}</p>
      <div class="reward-condition">${conditionHTML}</div>
    </div>
    <div class="reward-status">
      <div class="${statusClass}">${statusText}</div>
      <button class="btn-delete" title="Delete reward">✕</button>
    </div>
  `;

  // Attach delete handler to new item
  newItem.querySelector(".btn-delete").addEventListener("click", () => {
    newItem.style.transition = "opacity 0.2s, transform 0.2s";
    newItem.style.opacity = "0";
    newItem.style.transform = "translateX(10px)";
    setTimeout(() => {
      newItem.remove();
      checkEmptyState();
    }, 200);
  });

  document.getElementById("rewardsList").prepend(newItem);
  lucide.createIcons();

  closeRewardModal();
}

// Highlight invalid field briefly
function highlight(id) {
  const el = document.getElementById(id);
  el.style.borderColor = "#e05c5c";
  el.focus();
  setTimeout(() => (el.style.borderColor = ""), 1500);
}

// Check if filtered list is empty and show empty state
function checkEmptyState() {
  const list = document.getElementById("rewardsList");
  const visible = [...list.querySelectorAll(".reward-item")].filter(
    (i) => i.style.display !== "none",
  );

  const existing = list.querySelector(".empty-state");
  if (existing) existing.remove();

  if (visible.length === 0) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    empty.innerHTML = `<div class="empty-icon"><i data-lucide="gift"></i></div><p>No rewards in this category yet.</p>`;
    list.appendChild(empty);
  }
}

window.openRewardModal = openRewardModal;
window.closeRewardModal = closeRewardModal;
window.submitReward = submitReward;
window.updateRewardIconPreview = updateRewardIconPreview;
