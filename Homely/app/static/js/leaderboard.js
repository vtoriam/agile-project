// Stats are injected by the server via window.memberStats
const people = window.memberStats || {};

function openPersonModal(name) {
  const p = people[name];
  if (!p) return;

  const pct     = p.completed > 0 ? Math.round((p.on_time / p.completed) * 100) : 0;
  const latePct = 100 - pct;

  const avatarEl = document.getElementById('modalAvatar');
  avatarEl.innerHTML = `<i data-lucide="${p.avatar}"></i>`;
  avatarEl.style.color       = p.rankColor;
  avatarEl.style.borderColor = p.rankColor;
  avatarEl.style.background  = p.rankColor + '18';

  document.getElementById('modalName').textContent   = name;
  document.getElementById('modalRank').textContent   = `#${p.rank} in household · ${p.points} pts`;
  document.getElementById('modalTotal').textContent  = p.completed;
  document.getElementById('modalOnTime').textContent = p.on_time;
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

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.lb-person-clickable').forEach(el => {
    el.addEventListener('click', () => openPersonModal(el.dataset.person));
  });

  lucide.createIcons();
});
