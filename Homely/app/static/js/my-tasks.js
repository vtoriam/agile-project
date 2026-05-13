let filter = 'pending';
let nextId = 1;
let tasks = [];

const catIcon = {
  cleaning: 'sparkles', kitchen: 'utensils',  garden:   'leaf',
  laundry:  'shirt',    shopping: 'shopping-cart', trash: 'trash-2',
  pets:     'paw-print', repairs: 'wrench',   bathroom: 'bath',
  storage:  'package',  other:   'clipboard-list',
};

const catColor = {
  cleaning: '#c17f5a', kitchen: '#d4834a', garden:  '#6a9e5a',
  laundry:  '#5a7eb8', shopping: '#9a6ab8', trash:  '#8a9e7a',
  pets:     '#d4a84a', repairs:  '#6a8eb8', bathroom:'#5ab0a8',
  storage:  '#b89a5a', other:   '#9e9087',
};

const catLabel = {
  cleaning: 'Cleaning', kitchen: 'Kitchen',   garden:   'Garden',
  laundry:  'Laundry',  shopping: 'Shopping', trash:    'Bins & Trash',
  pets:     'Pets',     repairs:  'Repairs',  bathroom: 'Bathroom',
  storage:  'Storage',  other:    'Other',
};

// ── Database sync ─────────────────────────────────
// Keep `nextId` aligned with existing task IDs (max + 1)
function syncNextId() {
  nextId = tasks.length ? tasks.reduce((m, t) => Math.max(m, t.id), 0) + 1 : 1;
}

function loadTasks() {
  const payload = document.getElementById('initial-tasks-data');
  try {
    tasks = payload ? JSON.parse(payload.textContent || '[]') : [];
  } catch (_) {
    tasks = [];
  }
  syncNextId();
}

// ── Utilities ─────────────────────────────────────
function setGreeting() {
  const h = new Date().getHours();
  document.getElementById('time-greeting').textContent =
    h < 12 ? 'Good morning' : h < 17 ? 'Good afternoon' : 'Good evening';
  document.getElementById('greeting-date').textContent =
    new Date().toLocaleDateString([], { weekday: 'long', day: 'numeric', month: 'long' });
}

function formatDue(val) {
  if (!val) return '';
  return new Date(val).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' });
}

function refreshIcons() { lucide.createIcons(); }

function showToast(points) {
  const existing = document.getElementById('pts-toast');
  if (existing) existing.remove();
  const toast = document.createElement('div');
  toast.id = 'pts-toast';
  toast.className = 'pts-toast';
  toast.innerHTML = `<i data-lucide="zap"></i> +${points} pts earned!`;
  document.body.appendChild(toast);
  lucide.createIcons();
  requestAnimationFrame(() => requestAnimationFrame(() => toast.classList.add('show')));
  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// ── Modal ─────────────────────────────────────────
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
  document.getElementById('modal-points').value    = '';
  document.getElementById('modal-due-date').value  = '';
  document.getElementById('modal-due-time').value  = '';
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
// Submit a new task: validate input, POST to server, then update local state
async function submitTask() {
  const nameEl = document.getElementById('modal-task-name');
  const name = nameEl.value.trim();
  const pointsRaw = document.getElementById('modal-points').value;
  const dueDate = document.getElementById('modal-due-date').value;
  const dueTime = document.getElementById('modal-due-time').value;
  const cat = document.getElementById('modal-cat-select').value || 'other';
  const errEl = document.getElementById('modal-error');

  if (!name) {
    errEl.textContent = 'Please enter a task name.';
    nameEl.focus();
    return;
  }

  const points = pointsRaw !== '' ? parseInt(pointsRaw, 10) : null;
  if (points !== null && (!Number.isInteger(points) || points < 1)) {
    errEl.textContent = 'Points must be a positive number.';
    document.getElementById('modal-points').focus();
    return;
  }

  const due = dueDate ? `${dueDate}T${dueTime || '00:00'}` : null;

  try {
    const response = await fetch('/tasks/create', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: name, cat: cat, points: points, due: due }),
    });

    if (!response.ok) throw new Error('Failed to create task');

    const created = await response.json();
    errEl.textContent = '';
    tasks.unshift(created);
    syncNextId();
    closeModal();
    renderTasks();
  } catch (error) {
    console.error('Error creating task:', error);
    errEl.textContent = 'Failed to create task. Please try again.';
  }
}

// ── Toggle / delete ───────────────────────────────
async function toggleTask(id) {
  const t = tasks.find(task => task.id === id);
  if (!t) return;
  try {
    const response = await fetch(`/tasks/${id}/toggle`, { method: 'POST' });
    if (!response.ok) throw new Error('Failed to toggle task');

    const data = await response.json();
    const wasDone = t.done;
    t.done = Boolean(data.done);
    // If task transitioned to done, show earned points
    if (!wasDone && t.done && t.points) showToast(t.points);
    renderTasks();
  } catch (error) {
    console.error('Error toggling task:', error);
  }
}

async function deleteTask(id) {
  try {
    const response = await fetch(`/tasks/${id}`, { method: 'DELETE' });
    if (!response.ok) throw new Error('Failed to delete task');

    tasks = tasks.filter(t => t.id !== id);
    syncNextId();
    renderTasks();
  } catch (error) {
    console.error('Error deleting task:', error);
  }
}

function setFilter(f) { filter = f; renderTasks(); }

// ── Render ────────────────────────────────────────
function renderFilters() {
  const row = document.getElementById('cat-row');
  const activeCats = [...new Set(tasks.filter(t => !t.done).map(t => t.cat))];
  // Helper to build a filter button
  const makeBtn = (value, icon, label) =>
    `<button class="cat-btn ${filter === value ? 'active' : ''}" onclick="setFilter('${value}')"><i data-lucide="${icon}"></i> ${label}</button>`;

  const buttons = [];
  buttons.push(makeBtn('all', 'layout-grid', 'All'));
  buttons.push(makeBtn('pending', 'clock', 'Pending'));

  activeCats.forEach(cat => {
    const icon = catIcon[cat] || 'clipboard-list';
    const label = catLabel[cat] || cat;
    buttons.push(makeBtn(cat, icon, label));
  });

  buttons.push(makeBtn('done', 'check-circle', 'Done'));
  row.innerHTML = buttons.join('');
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
      const icon  = catIcon[t.cat]  || 'clipboard-list';
      const color = catColor[t.cat] || '#9e9087';
      const label = catLabel[t.cat] || t.cat;
      const el = document.createElement('div');
      el.className = 'task-item' + (t.done ? ' done' : '');
      el.style.borderLeftColor = color;
      el.innerHTML = `
        <div class="task-check" onclick="toggleTask(${t.id})"><i data-lucide="check"></i></div>
        <div class="task-icon-pill" style="background:${color}18; color:${color}"><i data-lucide="${icon}"></i></div>
        <div class="task-body">
          <div class="task-text">${t.text}</div>
          <div class="task-meta">
            ${t.points ? `<span class="task-chip chip-points"><i data-lucide="zap"></i> ${t.points} pts</span>` : ''}
            ${t.due    ? `<span class="task-chip chip-due"><i data-lucide="clock"></i> ${formatDue(t.due)}</span>` : ''}
            ${t.due && !t.done && new Date(t.due) < new Date() ? `<span class="overdue-badge"><i data-lucide="alert-circle"></i> Overdue</span>` : ''}
          </div>
        </div>
        <span class="task-cat-tag" style="background:${color}18; color:${color}; border-color:${color}40">${label}</span>
        <button class="task-del" onclick="deleteTask(${t.id})"><i data-lucide="x"></i></button>`;
      list.appendChild(el);
    });
  }

  const sectionTitles = { all: 'All My Tasks', pending: 'Pending', done: 'Completed' };
  const title = sectionTitles[filter] || catLabel[filter] || 'My Tasks';
  const count = visible.length;
  const countLabel = filter === 'done'
    ? `${count} completed`
    : `${count} task${count !== 1 ? 's' : ''} remaining`;

  document.getElementById('task-section-title').textContent = title;
  document.getElementById('task-section-count').textContent = count > 0 ? countLabel : '';

  const done = tasks.filter(t => t.done).length;
  document.getElementById('stat-total').textContent = tasks.length;
  document.getElementById('stat-done').textContent  = done;
  document.getElementById('stat-rem').textContent   = tasks.length - done;

  refreshIcons();
}

// ── Init ──────────────────────────────────────────
loadTasks();
setGreeting();
renderTasks();
