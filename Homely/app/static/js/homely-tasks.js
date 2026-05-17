// ════════════════════════════
// DATA & STATE
// ════════════════════════════

let currentUser = null;
let filter = "pending";
let nextId = 1;

let tasks = typeof initialTasks !== "undefined" ? initialTasks : [];

// Map category → Lucide icon name
const catIcon = {
  cleaning: "sparkles",
  kitchen: "utensils",
  garden: "leaf",
  laundry: "shirt",
  shopping: "shopping-cart",
  trash: "trash-2",
  pets: "paw-print",
  repairs: "wrench",
  bathroom: "bath",
  storage: "package",
  other: "clipboard-list",
};

// Map category → accent colour
const catColor = {
  cleaning: "#c17f5a",
  kitchen: "#d4834a",
  garden: "#6a9e5a",
  laundry: "#5a7eb8",
  shopping: "#9a6ab8",
  trash: "#8a9e7a",
  pets: "#d4a84a",
  repairs: "#6a8eb8",
  bathroom: "#5ab0a8",
  storage: "#b89a5a",
  other: "#9e9087",
};

// Map category → display label
const catLabel = {
  cleaning: "Cleaning",
  kitchen: "Kitchen",
  garden: "Garden",
  laundry: "Laundry",
  shopping: "Shopping",
  trash: "Bins & Trash",
  pets: "Pets",
  repairs: "Repairs",
  bathroom: "Bathroom",
  storage: "Storage",
  other: "Other",
};

// ════════════════════════════
// UTILITIES
// ════════════════════════════

function setGreeting() {
  const now = new Date();
  const h = now.getHours();
  const g =
    h < 12 ? "Good morning" : h < 17 ? "Good afternoon" : "Good evening";
  document.getElementById("time-greeting").textContent = g;
  document.getElementById("greeting-date").textContent = now.toLocaleDateString(
    [],
    {
      weekday: "long",
      day: "numeric",
      month: "long",
    },
  );
}

function guessCategory(text) {
  const t = text.toLowerCase();
  if (/vacu|mop|dust|wipe|sweep|clean|scrub|wash|laundry/.test(t))
    return "cleaning";
  if (
    /cook|meal|dish|kitchen|grocery|groceries|food|bake|dinner|lunch|breakfast/.test(
      t,
    )
  )
    return "kitchen";
  if (/garden|plant|water|mow|lawn|weed|prune|flower|herb/.test(t))
    return "garden";
  return "other";
}

function formatDue(val) {
  if (!val) return "";
  const d = new Date(val);
  return d.toLocaleString([], { dateStyle: "medium", timeStyle: "short" });
}

// Re-render all Lucide icons after DOM changes
function refreshIcons() {
  lucide.createIcons();
}

// ════════════════════════════
// AUTH
// ════════════════════════════

function doLogout() {
  window.location.href = "/logout";
}

// ════════════════════════════
// NAVIGATION
// ════════════════════════════

function showLeaderboard() {
  document.getElementById("home-page").classList.remove("active");
  document.getElementById("leaderboard-page").classList.add("active");
  document.getElementById("nav-home").classList.remove("active");
  document.getElementById("nav-leaderboard").classList.add("active");
}

function showHome() {
  document.getElementById("leaderboard-page").classList.remove("active");
  document.getElementById("home-page").classList.add("active");
  document.getElementById("nav-leaderboard").classList.remove("active");
  document.getElementById("nav-home").classList.add("active");
}

// ════════════════════════════
// TASKS
// ════════════════════════════

function openModal() {
  document.getElementById("taskModal").classList.add("open");
  document.getElementById("modalOverlay").classList.add("open");
  document.getElementById("modal-task-name").focus();
  refreshIcons();
}

function closeModal() {
  document.getElementById("taskModal").classList.remove("open");
  document.getElementById("modalOverlay").classList.remove("open");
  document.getElementById("modal-task-name").value = "";
  document.getElementById("modal-assigned").value = "";
  document.getElementById("modal-points").value = "";
  document.getElementById("modal-due-date").value = "";
  document.getElementById("modal-due-time").value = "";
  document.getElementById("modal-error").textContent = "";
  document.getElementById("modal-cat-select").value = "cleaning";
  updateCatPreview();
  refreshIcons();
}

function updateCatPreview() {
  const sel = document.getElementById("modal-cat-select");
  const icon = sel.options[sel.selectedIndex].dataset.icon || "clipboard-list";
  document.getElementById("catIconPreview").innerHTML =
    `<i data-lucide="${icon}"></i>`;
  refreshIcons();
}

function submitTask() {
  console.log("modal-task-name:", document.getElementById("modal-task-name"));
  console.log("modal-assigned:", document.getElementById("modal-assigned"));
  console.log("modal-points:", document.getElementById("modal-points"));
  console.log("modal-due:", document.getElementById("modal-due"));
  console.log("modal-cat-select:", document.getElementById("modal-cat-select"));
  console.log("modal-error:", document.getElementById("modal-error"));
  const name = document.getElementById("modal-task-name").value.trim();
  const assigned = document.getElementById("modal-assigned").value;
  const points = document.getElementById("modal-points").value;
  const dueDate = document.getElementById("modal-due-date").value;
  const dueTime = document.getElementById("modal-due-time").value;
  const due = dueDate ? `${dueDate}T${dueTime || "00:00"}` : null;
  const cat = document.getElementById("modal-cat-select").value || "other";
  const errEl = document.getElementById("modal-error");

  if (!name) {
    errEl.textContent = "Please enter a task name.";
    document.getElementById("modal-task-name").focus();
    return;
  }
  if (!assigned) {
    errEl.textContent = "Please select who this is assigned to.";
    return;
  }

  errEl.textContent = "";

  // Disable button while saving
  const addBtn = document.getElementById("modal-add-btn");
  if (addBtn) addBtn.disabled = true;

  fetch("/tasks/create", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCsrfToken(),
    },
    body: JSON.stringify({
      text: name,
      assignedTo: assigned,
      points: points || null,
      due: due || null,
      cat: cat,
    }),
  })
    .then((res) => res.json())
    .then((task) => {
      // Add the returned task (with real database id) to the array
      tasks.unshift(task);
      closeModal();
      renderTasks();
      updateOverdueBanner();
    })
    .catch((err) => {
      console.error("Failed to create task:", err);
      errEl.textContent = "Something went wrong — please try again.";
    })
    .finally(() => {
      if (addBtn) addBtn.disabled = false;
    });
}

function toggleTask(id) {
  const t = tasks.find((t) => t.id === id);
  if (!t) return;

  // Track the previous state to show toast only on completion
  const wasDone = t.done;

  // Optimistically update the UI immediately
  t.done = !t.done;
  renderTasks();
  updateOverdueBanner();

  // Then sync with the database in the background
  fetch(`/tasks/${id}/toggle`, {
    method: "POST",
    headers: { "X-CSRFToken": getCsrfToken() },
  })
    .then((res) => res.json())
    .then((data) => {
      // Confirm the server state matches
      t.done = data.done;
      renderTasks();
      updateOverdueBanner();
      // Show toast when task is newly completed
      if (!wasDone && t.done) {
        const message = data.message || `You earned ${t.points || 0} points!`;
        showToast(message);
      }
    })
    .catch((err) => {
      // If the request fails, roll back the optimistic update
      console.error("Failed to toggle task:", err);
      t.done = !t.done;
      renderTasks();
      updateOverdueBanner();
    });
}

function showToast(message) {
  const existing = document.getElementById("pts-toast");
  if (existing) existing.remove();
  const toast = document.createElement("div");
  toast.id = "pts-toast";
  toast.className = "pts-toast";
  toast.innerHTML = `<i data-lucide="zap"></i> ${message}`;
  document.body.appendChild(toast);
  lucide.createIcons();
  requestAnimationFrame(() =>
    requestAnimationFrame(() => toast.classList.add("show")),
  );
  setTimeout(() => {
    toast.classList.remove("show");
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

function updateOverdueBanner() {
  const banner = document.getElementById("overdue-banner");
  if (!banner) return;

  const now = new Date();
  const overdueTasks = tasks.filter((t) => {
    if (t.done || !t.due) return false;
    return new Date(t.due) < now;
  });

  if (overdueTasks.length === 0) {
    banner.style.display = "none";
  } else {
    banner.style.display = "flex";
    const countText = document.getElementById("overdue-count-text");
    if (countText) {
      countText.innerHTML = `${overdueTasks.length} overdue task${overdueTasks.length !== 1 ? "s" : ""}`;
    }
  }
}

function deleteTask(id) {
  if (!window.confirm("Delete this task? This cannot be undone.")) return;

  fetch(`/tasks/${id}`, {
    method: "DELETE",
    headers: { "X-CSRFToken": getCsrfToken() },
  })
    .then((res) => {
      if (!res.ok) {
        return res
          .json()
          .catch(() => ({}))
          .then((data) => {
            throw new Error(data.error || "Could not delete task.");
          });
      }

      tasks = tasks.filter((t) => t.id !== id);
      renderTasks();
      updateOverdueBanner();
    })
    .catch((err) => {
      console.error("Failed to delete task:", err);
      alert(err.message || "Could not delete task. Please try again.");
    });
}

function setFilter(f) {
  filter = f;
  renderTasks();
}

function renderFilters() {
  const row = document.getElementById("cat-row");

  // Only show category tabs for categories that still have incomplete tasks
  const activeCats = [
    ...new Set(tasks.filter((t) => !t.done).map((t) => t.cat)),
  ];

  let html = `<button class="cat-btn ${filter === "all" ? "active" : ""}" onclick="setFilter('all')">
    <i data-lucide="layout-grid"></i> All
  </button>
  <button class="cat-btn ${filter === "pending" ? "active" : ""}" onclick="setFilter('pending')">
    <i data-lucide="clock"></i> Pending
  </button>`;

  activeCats.forEach((cat) => {
    const icon = catIcon[cat] || "clipboard-list";
    const label = catLabel[cat] || cat;
    html += `<button class="cat-btn ${filter === cat ? "active" : ""}" onclick="setFilter('${cat}')">
      <i data-lucide="${icon}"></i> ${label}
    </button>`;
  });

  html += `<button class="cat-btn ${filter === "done" ? "active" : ""}" onclick="setFilter('done')">
    <i data-lucide="check-circle"></i> Done
  </button>`;

  row.innerHTML = html;
  refreshIcons();
}

function renderTasks() {
  renderFilters();

  const list = document.getElementById("task-list");
  const empty = document.getElementById("empty-state");

  const visible = tasks.filter((t) => {
    if (filter === "all") return true;
    if (filter === "pending") return !t.done;
    if (filter === "done") return t.done;
    return t.cat === filter && !t.done;
  });

  list.innerHTML = "";

  if (visible.length === 0) {
    empty.classList.add("show");
  } else {
    empty.classList.remove("show");

    visible.forEach((t) => {
      const icon = catIcon[t.cat] || "clipboard-list";
      const color = catColor[t.cat] || "#9e9087";
      const label = catLabel[t.cat] || t.cat;
      const el = document.createElement("div");
      el.className = "task-item" + (t.done ? " done" : "");
      el.style.borderLeftColor = color;
      el.innerHTML = `
        <div class="task-check" onclick="toggleTask(${t.id})">
          <i data-lucide="check"></i>
        </div>
        <div class="task-icon-pill" style="background:${color}18; color:${color}">
          <i data-lucide="${icon}"></i>
        </div>
        <div class="task-body">
          <div class="task-text">${t.text}</div>
          <div class="task-meta">
            ${t.assignedTo ? `<span class="task-chip chip-user"><i data-lucide="user"></i> ${t.assignedTo}</span>` : ""}
            ${t.points ? `<span class="task-chip chip-points"><i data-lucide="zap"></i> ${t.points} pts</span>` : ""}
            ${t.due ? `<span class="task-chip chip-due"><i data-lucide="clock"></i> ${formatDue(t.due)}</span>` : ""}
            ${t.due && !t.done && new Date(t.due) < new Date() ? `<span class="overdue-badge"><i data-lucide="alert-circle"></i> Overdue</span>` : ""}
          </div>
        </div>
        <span class="task-cat-tag" style="background:${color}18; color:${color}; border-color:${color}40">${label}</span>
        <button class="task-del" onclick="deleteTask(${t.id})">
          <i data-lucide="x"></i>
        </button>
      `;
      list.appendChild(el);
    });
  }

  // Update section heading
  const sectionTitles = {
    all: "All Tasks",
    pending: "Pending",
    done: "Completed",
  };
  const title = sectionTitles[filter] || catLabel[filter] || "Tasks";
  const count = visible.length;
  const countLabel =
    filter === "done"
      ? `${count} completed`
      : `${count} task${count !== 1 ? "s" : ""} remaining`;

  document.getElementById("task-section-title").textContent = title;
  document.getElementById("task-section-count").textContent =
    count > 0 ? countLabel : "";

  // Update stats
  const done = tasks.filter((t) => t.done).length;
  document.getElementById("stat-total").textContent = tasks.length;
  document.getElementById("stat-done").textContent = done;
  document.getElementById("stat-rem").textContent = tasks.length - done;

  // Re-render Lucide icons after DOM update
  refreshIcons();
}

// ════════════════════════════
// EVENT LISTENERS
// ════════════════════════════

// ════════════════════════════
// INIT
// ════════════════════════════

refreshIcons();
setGreeting();
renderTasks();
