const rewardsPage = document.getElementById("rewardsPage");
const USER_POINTS = Number(rewardsPage?.dataset.userPoints || 0);
const rewardsList = document.getElementById("rewardsList");
const filterTabs = document.querySelectorAll(".filter-tab");

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function visibleRewardItems() {
  return [...document.querySelectorAll(".reward-item")].filter(
    (item) => item.style.display !== "none",
  );
}

function checkEmptyState() {
  const existing = rewardsList?.querySelector(".empty-state");
  if (existing) existing.remove();

  if (!rewardsList) {
    return;
  }

  if (visibleRewardItems().length === 0) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    empty.innerHTML = `<div class="empty-icon"><i data-lucide="gift"></i></div><p>No rewards in this category yet.</p>`;
    rewardsList.appendChild(empty);
    lucide.createIcons();
  }
}

function updateClaimedCount() {
  const count = document.querySelectorAll(".reward-item.claimed").length;
  const badge = document.getElementById("claimed-count");
  if (badge) badge.textContent = count;
}

function applyRewardFilter(filter) {
  document.querySelectorAll(".reward-item").forEach((item) => {
    const type = item.dataset.type;
    const isClaimed = item.classList.contains("claimed");
    const isUnlocked = item.classList.contains("unlocked") || isClaimed;

    if (filter === "all") {
      item.style.display = isClaimed ? "none" : "flex";
    } else if (filter === "unlocked") {
      item.style.display = isUnlocked ? "flex" : "none";
    } else if (filter === "claimed") {
      item.style.display = isClaimed ? "flex" : "none";
    } else {
      item.style.display = type === filter ? "flex" : "none";
    }
  });

  checkEmptyState();
}

filterTabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    filterTabs.forEach((button) => button.classList.remove("active"));
    tab.classList.add("active");
    applyRewardFilter(tab.dataset.filter || "all");
  });
});

function launchConfetti(anchorElement) {
  const host =
    anchorElement.closest(".reward-item") || anchorElement.parentElement;
  if (!host) {
    return;
  }

  const existing = host.querySelector(".confetti-burst");
  if (existing) existing.remove();

  const confetti = document.createElement("div");
  confetti.className = "confetti-burst";
  const colors = ["#c17f5a", "#9a6ab8", "#8a9e7a", "#d9b35e", "#de7f6f"];

  for (let index = 0; index < 20; index += 1) {
    const piece = document.createElement("span");
    piece.className = "confetti-piece";
    piece.style.left = `${8 + Math.random() * 84}%`;
    piece.style.backgroundColor = colors[index % colors.length];
    piece.style.setProperty(
      "--confetti-x",
      `${(Math.random() * 2 - 1) * 150}px`,
    );
    piece.style.setProperty("--confetti-y", `${-110 - Math.random() * 80}px`);
    piece.style.setProperty(
      "--confetti-rotate",
      `${360 + Math.random() * 540}deg`,
    );
    piece.style.animationDelay = `${Math.random() * 0.12}s`;
    confetti.appendChild(piece);
  }

  host.appendChild(confetti);
  window.setTimeout(() => confetti.remove(), 1400);
}

function getActiveFilter() {
  const activeTab = document.querySelector(".filter-tab.active");
  return activeTab ? (activeTab.dataset.filter || "all") : "all";
}

function markRewardClaimed(item, button) {
  item.classList.add("claimed");
  item.classList.remove("locked", "unlocked");
  item.dataset.claimed = "true";

  const status = item.querySelector(".reward-status");
  if (status) {
    status.innerHTML =
      '<div class="status-claimed"><i data-lucide="badge-check"></i> Claimed</div>';
  }

  if (button) {
    button.disabled = true;
  }

  launchConfetti(item);
  lucide.createIcons();
  updateClaimedCount();
  applyRewardFilter(getActiveFilter());
}

async function claimReward(button) {
  const item = button.closest(".reward-item");
  const claimUrl = button.dataset.claimUrl || item.dataset.claimUrl;

  if (!item) {
    return;
  }

  if (!claimUrl) {
    markRewardClaimed(item, button);
    return;
  }

  button.disabled = true;
  const originalLabel = button.textContent;
  button.textContent = "Claiming...";

  try {
    const response = await fetch(claimUrl, {
      method: "POST",
      headers: {
        "X-CSRFToken": getCsrfToken(),
      },
    });
    const payload = await response.json();

    if (!response.ok || !payload.success) {
      throw new Error(payload.message || "Unable to claim reward.");
    }

    markRewardClaimed(item, button);

    if (payload.newPoints !== undefined) {
      const pointsEl = document.querySelector(".stat-card-points .stat-card-value");
      if (pointsEl) pointsEl.textContent = payload.newPoints.toLocaleString();
      // Refresh other rewards' unlocked/locked state based on new points
      try {
        refreshRewardsForNewPoints(payload.newPoints);
      } catch (e) {
        // ignore
      }
    }
  } catch (error) {
    button.disabled = false;
    button.textContent = originalLabel;
    // show styled danger modal instead of native alert
    if (typeof openDangerModal === "function") {
      const fakeBtn = document.createElement("button");
      fakeBtn.dataset.title = "Unable to claim";
      fakeBtn.dataset.message = error.message || "Unable to claim reward.";
      fakeBtn.dataset.sub = "";
      fakeBtn.dataset.label = "OK";
      openDangerModal(fakeBtn);
    } else {
      window.alert(error.message || "Unable to claim reward.");
    }
  }
}

function attachRewardControls(item) {
  const deleteButton = item.querySelector(".btn-delete");
  if (deleteButton) {
    deleteButton.addEventListener("click", async () => {
      const rewardId = item.dataset.rewardId;
      if (rewardId) {
        await fetch(`/rewards/custom/${rewardId}`, {
          method: "DELETE",
          headers: { "X-CSRFToken": getCsrfToken() },
        }).catch(console.error);
      }
      item.style.transition = "opacity 0.2s, transform 0.2s";
      item.style.opacity = "0";
      item.style.transform = "translateX(10px)";
      window.setTimeout(() => {
        item.remove();
        checkEmptyState();
      }, 200);
    });
  }

  const claimButton = item.querySelector(".reward-claim-btn");
  if (claimButton) {
    claimButton.addEventListener("click", () => claimReward(claimButton));
  }
}

document.querySelectorAll(".reward-item").forEach(attachRewardControls);

// Danger modal helpers (used to display styled warnings)
window.openDangerModal = function (btn) {
  document.getElementById("dangerModalTitle").textContent = btn.dataset.title || "Warning";
  document.getElementById("dangerModalMessage").textContent = btn.dataset.message || "";
  document.getElementById("dangerModalSub").textContent = btn.dataset.sub || "";
  const modal = document.getElementById("dangerModal");
  const overlay = document.getElementById("dangerOverlay");
  modal.classList.add("open");
  overlay.classList.add("open");
  lucide.createIcons();
};

window.closeDangerModal = function () {
  const modal = document.getElementById("dangerModal");
  const overlay = document.getElementById("dangerOverlay");
  if (modal) modal.classList.remove("open");
  if (overlay) overlay.classList.remove("open");
};

// Update reward list unlocked/locked states after points change
function refreshRewardsForNewPoints(newPoints) {
  // Update global USER_POINTS constant-like variable
  window.USER_POINTS = Number(newPoints || 0);
  // update stat card
  const pointsEl = document.querySelector('.stat-card-points .stat-card-value');
  if (pointsEl) pointsEl.textContent = Number(newPoints).toLocaleString();

  document.querySelectorAll('.reward-item').forEach((item) => {
    // skip claimed items
    if (item.classList.contains('claimed')) return;

    const cond = item.querySelector('.condition-badge');
    if (!cond) return;
    const txt = cond.textContent || '';
    // extract first number found in the condition text
    const m = txt.replace(/,/g, '').match(/(\d+)/);
    const threshold = m ? Number(m[0]) : null;

    if (threshold === null) return;

    if (Number(newPoints) >= threshold) {
      // mark unlocked
      item.classList.remove('locked');
      item.classList.add('unlocked');
      const status = item.querySelector('.reward-status');
      if (status) {
        status.innerHTML = '<div class="status-unlocked"><i data-lucide="check"></i> Unlocked</div><button class="reward-claim-btn" type="button">Claim</button>';
        const btn = status.querySelector('.reward-claim-btn');
        if (btn) btn.addEventListener('click', () => claimReward(btn));
      }
    } else {
      // still locked: update progress if present
      item.classList.remove('unlocked');
      item.classList.add('locked');
      const status = item.querySelector('.reward-status');
      if (status) {
        const remaining = threshold - Number(newPoints);
        status.innerHTML = `<div class="status-locked"><i data-lucide="lock"></i> ${remaining.toLocaleString()} pts away</div>`;
      }
      const progressFill = item.querySelector('.progress-fill');
      if (progressFill) {
        const pct = Math.min(100, Math.round((Number(newPoints) / threshold) * 100));
        progressFill.style.width = pct + '%';
        const label = item.querySelector('.progress-label');
        if (label) label.textContent = `${Math.min(Number(newPoints), threshold).toLocaleString()} / ${threshold.toLocaleString()} pts`;
      }
    }
  });
  updateClaimedCount();
  // Ensure lucide icons are (re)rendered for newly-updated status elements
  try { lucide.createIcons(); } catch (e) { /* lucide may not be available in tests */ }
}

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

function buildCustomRewardCard({
  title,
  desc,
  threshold,
  icon,
  isUnlocked,
  rewardId,
}) {
  const progressPct = Math.min(
    100,
    Math.round((USER_POINTS / threshold) * 100),
  );
  const remaining = Math.max(threshold - USER_POINTS, 0);
  const statusMarkup = isUnlocked
    ? `
      <div class="status-unlocked"><i data-lucide="check"></i> Unlocked</div>
      <button class="reward-claim-btn" type="button">Claim</button>
    `
    : `<div class="status-locked"><i data-lucide="lock"></i> ${remaining.toLocaleString()} pts away</div>`;

  const conditionMarkup = isUnlocked
    ? `
      <div class="reward-condition">
        <span class="condition-badge points-badge"><i data-lucide="zap"></i> ${threshold.toLocaleString()} pts</span>
      </div>
    `
    : `
      <div class="reward-condition">
        <span class="condition-badge points-badge"><i data-lucide="zap"></i> ${threshold.toLocaleString()} pts</span>
      </div>
      <div class="progress-wrap">
        <div class="progress-bar-custom">
          <div class="progress-fill" style="width: ${progressPct}%"></div>
        </div>
        <span class="progress-label">${Math.min(USER_POINTS, threshold).toLocaleString()} / ${threshold.toLocaleString()} pts</span>
      </div>
    `;

  return `
    <div class="reward-item custom-reward ${isUnlocked ? "unlocked" : "locked"}" data-type="custom" data-reward-id="${escapeHtml(String(rewardId))}" data-claimed="false">
      <div class="reward-icon-wrap">
        <div class="reward-icon ${isUnlocked ? "" : "muted"}"><i data-lucide="${escapeHtml(icon)}"></i></div>
      </div>
      <div class="reward-body">
        <div class="reward-title-row">
          <div class="reward-title">${escapeHtml(title)}</div>
          <span class="custom-tag">Custom</span>
        </div>
        <p class="reward-desc">${escapeHtml(desc || "No description provided.")}</p>
        ${conditionMarkup}
      </div>
      <div class="reward-status">
        ${statusMarkup}
        <button class="btn-delete" type="button" title="Delete reward"><i data-lucide="x"></i></button>
      </div>
    </div>
  `;
}

async function submitReward() {
  const title = document.getElementById("rewardTitle").value.trim();
  const desc = document.getElementById("rewardDesc").value.trim();
  const threshold = Number.parseInt(
    document.getElementById("thresholdValue").value,
    10,
  );
  const icon = document.getElementById("rewardIcon").value || "star";
  const errEl = document.getElementById("rewardModalError");

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

  const addBtn = document.querySelector("#rewardModal .modal-btn-add");
  if (addBtn) addBtn.disabled = true;

  try {
    const res = await fetch("/rewards/custom/create", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCsrfToken(),
      },
      body: JSON.stringify({ title, desc, threshold, icon }),
    });

    if (!res.ok) {
      const data = await res.json();
      errEl.textContent = data.error || "Something went wrong.";
      return;
    }

    const { id } = await res.json();
    const isUnlocked = USER_POINTS >= threshold;
    const newItem = document.createElement("div");
    newItem.innerHTML = buildCustomRewardCard({ rewardId: id, title, desc, threshold, icon, isUnlocked });

    const rewardElement = newItem.firstElementChild;
    rewardsList.prepend(rewardElement);
    attachRewardControls(rewardElement);
    lucide.createIcons();
    closeRewardModal();
    checkEmptyState();
  } catch (err) {
    console.error(err);
    errEl.textContent = "Something went wrong — please try again.";
  } finally {
    if (addBtn) addBtn.disabled = false;
  }
}

function highlight(id) {
  const el = document.getElementById(id);
  el.style.borderColor = "#e05c5c";
  el.focus();
  window.setTimeout(() => (el.style.borderColor = ""), 1500);
}

window.openRewardModal = openRewardModal;
window.closeRewardModal = closeRewardModal;
window.submitReward = submitReward;
window.updateRewardIconPreview = updateRewardIconPreview;
