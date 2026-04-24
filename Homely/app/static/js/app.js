// ════════════════════════════
// DATA & STATE
// ════════════════════════════

const USERS = { bob: 'home', admin: '1234' };

let currentUser = null;
let filter = 'all';
let nextId = 5;

let tasks = [
  { id: 1, text: 'Vacuum the living room', done: false, cat: 'cleaning' },
  { id: 2, text: 'Meal prep for the week',  done: false, cat: 'kitchen'  },
  { id: 3, text: 'Water the herb garden',   done: false, cat: 'garden'   },
  { id: 4, text: 'Wipe down the benchtops', done: true,  cat: 'cleaning' },
];

// Map category → Lucide icon name
const catIcon = {
  cleaning: 'sparkles',
  kitchen:  'utensils',
  garden:   'leaf',
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

function doLogin() {
  const u   = document.getElementById('username').value.trim().toLowerCase();
  const p   = document.getElementById('password').value;
  const err = document.getElementById('error-msg');

  if (USERS[u] && USERS[u] === p) {
    err.classList.remove('show');
    currentUser = u;

    const name = u.charAt(0).toUpperCase() + u.slice(1);
    document.getElementById('display-user').textContent = name;
    document.getElementById('login-page').style.display = 'none';
    document.getElementById('home-page').classList.add('active');

    setGreeting();
    renderTasks();
  } else {
    err.classList.add('show');
    document.getElementById('password').value = '';
  }
}

function doLogout() {
  document.getElementById('login-page').style.display = 'flex';
  document.getElementById('home-page').classList.remove('active');
  document.getElementById('leaderboard-page').classList.remove('active');
  document.getElementById('username').value = '';
  document.getElementById('password').value = '';
  refreshIcons();
}

// ════════════════════════════
// NAVIGATION
// ════════════════════════════

function showLeaderboard() {
  document.getElementById('home-page').classList.remove('active');
  document.getElementById('leaderboard-page').classList.add('active');
}

function showHome() {
  document.getElementById('leaderboard-page').classList.remove('active');
  document.getElementById('home-page').classList.add('active');
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
  document.querySelectorAll('.modal-cat').forEach(b => b.classList.remove('active'));
  document.querySelector('.modal-cat[data-cat="cleaning"]').classList.add('active');
  refreshIcons();
}

function selectCat(btn) {
  document.querySelectorAll('.modal-cat').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  refreshIcons();
}

function submitTask() {
  const name     = document.getElementById('modal-task-name').value.trim();
  const assigned = document.getElementById('modal-assigned').value;
  const points   = document.getElementById('modal-points').value;
  const due      = document.getElementById('modal-due').value;
  const catBtn   = document.querySelector('.modal-cat.active');
  const cat      = catBtn ? catBtn.dataset.cat : 'other';
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

function addTask() {
  const input = document.getElementById('task-input');
  if (!input) return;
  const text = input.value.trim();
  if (!text) return;
  tasks.unshift({ id: nextId++, text, done: false, cat: guessCategory(text) });
  input.value = '';
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

function setFilter(f, btn) {
  filter = f;
  document.querySelectorAll('.cat-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  renderTasks();
}

function renderTasks() {
  const list  = document.getElementById('task-list');
  const empty = document.getElementById('empty-state');

  const visible = tasks.filter(t => {
    if (filter === 'all')  return !t.done;
    if (filter === 'done') return t.done;
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
            ${t.points    ? `<span class="task-meta-item"><i data-lucide="zap"></i> ${t.points} pts</span>` : ''}
            ${t.due       ? `<span class="task-meta-item"><i data-lucide="clock"></i> ${t.due}</span>` : ''}
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

document.getElementById('password').addEventListener('keydown', e => {
  if (e.key === 'Enter') doLogin();
});

// ════════════════════════════
// INIT
// ════════════════════════════

// Initial Lucide icon render (for static HTML icons)
refreshIcons();
