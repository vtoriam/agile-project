// Stats are injected by the server via window.memberStats
let people = window.memberStats || {};

function buildSortedMembers(stats) {
  const arr = Object.keys(stats).map((name) => ({ name, ...stats[name] }));
  arr.sort((a, b) => b.points - a.points);
  return arr;
}

function formatPts(n) {
  return n == null ? "—" : n;
}

function openPersonModal(name) {
  const p = people[name];
  if (!p) return;

  const pct = p.completed > 0 ? Math.round((p.on_time / p.completed) * 100) : 0;
  const latePct = 100 - pct;

  const avatarEl = document.getElementById("modalAvatar");
  avatarEl.innerHTML = `<i data-lucide="${p.avatar}"></i>`;
  avatarEl.style.color = p.rankColor;
  avatarEl.style.borderColor = p.rankColor;
  avatarEl.style.background = p.rankColor + "18";

  document.getElementById("modalName").textContent = name;
  document.getElementById("modalRank").textContent =
    `#${p.rank} in household · ${p.points} pts`;
  document.getElementById("modalTotal").textContent = p.completed;
  document.getElementById("modalOnTime").textContent = p.on_time;
  document.getElementById("modalLate").textContent = p.late;
  document.getElementById("modalRate").textContent = `${pct}%`;
  document.getElementById("modalBarFill").style.width = `${pct}%`;
  document.getElementById("modalBarLate").style.width = `${latePct}%`;

  document.getElementById("personOverlay").classList.add("open");
  document.getElementById("personModal").classList.add("open");

  lucide.createIcons();
}

function closePersonModal() {
  document.getElementById("personOverlay").classList.remove("open");
  document.getElementById("personModal").classList.remove("open");
}

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".lb-person-clickable").forEach((el) => {
    el.addEventListener("click", () => openPersonModal(el.dataset.person));
  });

  lucide.createIcons();
});

function updateLeaderboardFromStats(newStats) {
  if (!newStats) return;
  people = newStats; // update global

  const members = buildSortedMembers(people);
  const podium = document.querySelector(".podium");
  // Update podium slots
  const slots = ["first", "second", "third"];
  for (let i = 0; i < 3; i++) {
    const slot = document.querySelector(`.podium-slot.${slots[i]}`);
    if (!slot) continue;
    const person = members[i];
    const nameEl = slot.querySelector(".podium-name");
    const pointsEl = slot.querySelector(".podium-points");
    if (person) {
      nameEl.textContent = person.name;
      pointsEl.textContent = person.points;
      nameEl.dataset.person = person.name;
      nameEl.classList.add("lb-person-clickable");
    } else {
      nameEl.textContent = "—";
      pointsEl.textContent = "—";
      nameEl.removeAttribute("data-person");
      nameEl.classList.remove("lb-person-clickable");
    }
  }

  // Recompute max points for bar widths
  const max_pts = members.length > 0 ? Math.max(1, members[0].points) : 1;

  // Rebuild list
  const list = document.querySelector(".lb-list");
  if (!list) return;
  let html = "";
  members.forEach((m, idx) => {
    // first three handled by podium, but keep consistent ordering
    // use rank number (1-based)
    const rank = idx + 1;
    const barPct = Math.round((m.points / max_pts) * 1000) / 10;
    html += `\n  <div class="lb-row ${rank <= 3 ? "rank-" + rank : ""}">\n    <div class="lb-pos">${rank}</div>\n    <div class="lb-avatar ${rank == 1 ? "rank-1-avatar" : rank == 2 ? "rank-2-avatar" : rank == 3 ? "rank-3-avatar" : ""}"><i data-lucide="${m.avatar || "user"}"></i></div>\n    <div class="lb-info">\n      <div class="lb-name-row">\n        <div class="lb-person-name lb-person-clickable" data-person="${m.name}"> ${m.name} </div>\n      </div>\n      <div class="lb-bar-wrap">\n        <div class="lb-bar-track">\n          <div class="lb-bar-fill" style="width: ${barPct}%"></div>\n        </div>\n      </div>\n    </div>\n    <div class="lb-score-wrap">\n      <span class="lb-score"> ${formatPts(m.points)} </span>\n      <span class="lb-score-label">points</span>\n    </div>\n  </div>`;
  });
  list.innerHTML = html;

  // Reattach click handlers
  document.querySelectorAll(".lb-person-clickable").forEach((el) => {
    el.removeEventListener("click", () => openPersonModal(el.dataset.person));
    el.addEventListener("click", () => openPersonModal(el.dataset.person));
  });

  lucide.createIcons();
}

// expose for external callers
window.updateLeaderboardFromStats = updateLeaderboardFromStats;
