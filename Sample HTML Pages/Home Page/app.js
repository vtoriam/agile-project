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

function addTask() {
  const input = document.getElementById('task-input');
  const text  = input.value.trim();
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
        <div class="task-text">${t.text}</div>
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
