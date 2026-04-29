// ════════════════════════════
// DATA & STATE
// ════════════════════════════

let currentUser = null;
let filter = 'pending';
let nextId = 1;

let tasks = [];

// Map category → Lucide icon name
const catIcon = {
  cleaning: 'sparkles',
  kitchen:  'utensils',
  garden:   'leaf',
  laundry:  'shirt',
  shopping: 'shopping-cart',
  trash:    'trash-2',
  pets:     'paw-print',
  repairs:  'wrench',
  bathroom: 'bath',
  storage:  'package',
  other:    'clipboard-list',
};

// ════════════════════════════
// UTILITIES
// ════════════════════════════

function setGreeting() {
  const h = new Date().getHours();
  const g = h < 12 ? 'Good morning' : h < 17 ? 'Good afternoon' : 'Good evening';
  document.getElementById('time-greeting').textContent = g;
}

function guessCategory(text) {
  const t = text.toLowerCase();
  if (/vacu|mop|dust|wipe|sweep|clean|scrub|wash|laundry/.test(t)) return 'cleaning';
  if (/cook|meal|dish|kitchen|grocery|groceries|food|bake|dinner|lunch|breakfast/.test(t)) return 'kitchen';
  if (/garden|plant|water|mow|lawn|weed|prune|flower|herb/.test(t)) return 'garden';
  return 'other';
}

// Re-render all Lucide icons after DOM changes
function refreshIcons() {
  lucide.createIcons();
}

// ════════════════════════════
// AUTH
// ════════════════════════════

function doLogout() {
  window.location.href = '/logout';
}

// ════════════════════════════
// NAVIGATION
// ════════════════════════════

function showLeaderboard() {
  document.getElementById('home-page').classList.remove('active');
  document.getElementById('leaderboard-page').classList.add('active');
  document.getElementById('nav-home').classList.remove('active');
  document.getElementById('nav-leaderboard').classList.add('active');
}

function showHome() {
  document.getElementById('leaderboard-page').classList.remove('active');
  document.getElementById('home-page').classList.add('active');
  document.getElementById('nav-leaderboard').classList.remove('active');
  document.getElementById('nav-home').classList.add('active');
}

// ════════════════════════════
// TASKS
// ════════════════════════════

function openModal() {
  document.getElementById('taskModal').classList.add('open');
  document.getElementById('modalOverlay').classList.add('open');
  document.getElementById('modal-task-name').focus();
  refreshIcons();
}

function closeModal() {
  document.getElementById('taskModal').classList.remove('open');
  document.getElementById('modalOverlay').classList.remove('open');
  document.getElementById('modal-task-name').value = '';
  document.getElementById('modal-assigned').value = '';
  document.getElementById('modal-points').value = '';
  document.getElementById('modal-due').value = 'Today';
  document.getElementById('modal-error').textContent = '';
  document.getElementById('modal-cat-select').value = 'cleaning';
  updateCatPreview();
  refreshIcons();
}

function updateCatPreview() {
  const sel  = document.getElementById('modal-cat-select');
  const icon = sel.options[sel.selectedIndex].dataset.icon || 'clipboard-list';
  document.getElementById('catIconPreview').innerHTML = `<i data-lucide="${icon}"></i>`;
  refreshIcons();
}

function submitTask() {
  const name     = document.getElementById('modal-task-name').value.trim();
  const assigned = document.getElementById('modal-assigned').value;
  const points   = document.getElementById('modal-points').value;
  const due      = document.getElementById('modal-due').value;
  const cat      = document.getElementById('modal-cat-select').value || 'other';
  const errEl    = document.getElementById('modal-error');

  if (!name) {
    errEl.textContent = 'Please enter a task name.';
    document.getElementById('modal-task-name').focus();
    return;
  }
  if (!assigned) {
    errEl.textContent = 'Please select who this is assigned to.';
    return;
  }

  errEl.textContent = '';
  tasks.unshift({
    id: nextId++,
    text: name,
    done: false,
    cat,
    assignedTo: assigned,
    points: points ? parseInt(points) : null,
    due,
  });

  closeModal();
  renderTasks();
}

function toggleTask(id) {
  const t = tasks.find(t => t.id === id);
  if (t) t.done = !t.done;
  renderTasks();
}

function deleteTask(id) {
  tasks = tasks.filter(t => t.id !== id);
  renderTasks();
}

function setFilter(f) {
  filter = f;
  renderTasks();
}

function renderFilters() {
  const row = document.getElementById('cat-row');

  const catLabel = {
    cleaning: 'Cleaning', kitchen: 'Kitchen', garden: 'Garden',
    laundry: 'Laundry',   shopping: 'Shopping', trash: 'Bins & Trash',
    pets: 'Pets',         repairs: 'Repairs',   bathroom: 'Bathroom',
    storage: 'Storage',   other: 'Other',
  };

  // Only show category tabs for categories that still have incomplete tasks
  const activeCats = [...new Set(tasks.filter(t => !t.done).map(t => t.cat))];

  let html = `<button class="cat-btn ${filter === 'all' ? 'active' : ''}" onclick="setFilter('all')">
    <i data-lucide="layout-grid"></i> All
  </button>
  <button class="cat-btn ${filter === 'pending' ? 'active' : ''}" onclick="setFilter('pending')">
    <i data-lucide="clock"></i> Pending
  </button>`;

  activeCats.forEach(cat => {
    const icon  = catIcon[cat] || 'clipboard-list';
    const label = catLabel[cat] || cat;
    html += `<button class="cat-btn ${filter === cat ? 'active' : ''}" onclick="setFilter('${cat}')">
      <i data-lucide="${icon}"></i> ${label}
    </button>`;
  });

  html += `<button class="cat-btn ${filter === 'done' ? 'active' : ''}" onclick="setFilter('done')">
    <i data-lucide="check-circle"></i> Done
  </button>`;

  row.innerHTML = html;
  refreshIcons();
}

function renderTasks() {
  renderFilters();

  const list  = document.getElementById('task-list');
  const empty = document.getElementById('empty-state');

  const visible = tasks.filter(t => {
    if (filter === 'all')     return true;
    if (filter === 'pending') return !t.done;
    if (filter === 'done')    return t.done;
    return t.cat === filter && !t.done;
  });

  list.innerHTML = '';

  if (visible.length === 0) {
    empty.classList.add('show');
  } else {
    empty.classList.remove('show');

    visible.forEach(t => {
      const icon = catIcon[t.cat] || 'clipboard-list';
      const el   = document.createElement('div');
      el.className = 'task-item' + (t.done ? ' done' : '');
      el.innerHTML = `
        <div class="task-check" onclick="toggleTask(${t.id})">
          <i data-lucide="check"></i>
        </div>
        <div class="task-icon">
          <i data-lucide="${icon}"></i>
        </div>
        <div class="task-body">
          <div class="task-text">${t.text}</div>
          <div class="task-meta">
            ${t.assignedTo ? `<span class="task-meta-item"><i data-lucide="user"></i> ${t.assignedTo}</span>` : ''}
            ${t.points     ? `<span class="task-meta-item"><i data-lucide="zap"></i> ${t.points} pts</span>` : ''}
            ${t.due        ? `<span class="task-meta-item"><i data-lucide="clock"></i> ${t.due}</span>` : ''}
          </div>
        </div>
        <div class="task-cat">${t.cat}</div>
        <button class="task-del" onclick="deleteTask(${t.id})">
          <i data-lucide="x"></i>
        </button>
      `;
      list.appendChild(el);
    });
  }

  // Update stats
  const done = tasks.filter(t => t.done).length;
  document.getElementById('stat-total').textContent = tasks.length;
  document.getElementById('stat-done').textContent  = done;
  document.getElementById('stat-rem').textContent   = tasks.length - done;

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
