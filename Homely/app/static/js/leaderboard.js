// ── Person data ───────────────────────────────────
const people = {
  Bob: {
    rank:      1,
    points:    520,
    completed: 26,
    onTime:    22,
    late:      4,
    streak:    4,
    avatar:    'crown',
    rankColor: '#c49a2a',
  },
  Marcus: {
    rank:      2,
    points:    340,
    completed: 17,
    onTime:    14,
    late:      3,
    streak:    2,
    avatar:    'medal',
    rankColor: '#9e9087',
  },
  Jamie: {
    rank:      3,
    points:    210,
    completed: 11,
    onTime:    11,
    late:      0,
    streak:    0,
    avatar:    'award',
    rankColor: '#b07248',
  },
};

// ── Modal open / close ────────────────────────────
function openPersonModal(name) {
  const p = people[name];
  if (!p) return;

  const pct     = p.completed > 0 ? Math.round((p.onTime / p.completed) * 100) : 0;
  const latePct = 100 - pct;

  document.getElementById('modalAvatar').innerHTML =
    `<i data-lucide="${p.avatar}"></i>`;
  document.getElementById('modalAvatar').style.color = p.rankColor;
  document.getElementById('modalAvatar').style.borderColor = p.rankColor;
  document.getElementById('modalAvatar').style.background =
    p.rankColor + '18';

  document.getElementById('modalName').textContent  = name;
  document.getElementById('modalRank').textContent  = `#${p.rank} in household · ${p.points} pts`;
  document.getElementById('modalTotal').textContent  = p.completed;
  document.getElementById('modalOnTime').textContent = p.onTime;
  document.getElementById('modalLate').textContent   = p.late;
  document.getElementById('modalRate').textContent   = `${pct}%`;
  document.getElementById('modalBarFill').style.width = `${pct}%`;
  document.getElementById('modalBarLate').style.width = `${latePct}%`;

  document.getElementById('personOverlay').classList.add('open');
  document.getElementById('personModal').classList.add('open');

  lucide.createIcons();
}

function closePersonModal() {
  document.getElementById('personOverlay').classList.remove('open');
  document.getElementById('personModal').classList.remove('open');
}

// ── Wire up all clickable names ───────────────────
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.lb-person-clickable').forEach(el => {
    el.addEventListener('click', () => openPersonModal(el.dataset.person));
  });

  lucide.createIcons();
});
