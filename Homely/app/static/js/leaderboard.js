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
  const list = document.querySelector(".lb-list");
  if (!list) return;

  // Helper: animate numbers
  function animateNumber(el, start, end, duration = 400) {
    if (!el) return;
    start = Number(start) || 0;
    end = Number(end) || 0;
    const diff = end - start;
    if (diff === 0) {
      el.textContent = end;
      return;
    }
    const startTs = performance.now();
    function frame(ts) {
      const t = Math.min(1, (ts - startTs) / duration);
      const val = Math.round(start + diff * t);
      el.textContent = val;
      if (t < 1) requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
  }

  // Update podium and list rows in-place
  const max_pts = members.length > 0 ? Math.max(1, members[0].points) : 1;

  // Update podium slots
  const slots = ["first", "second", "third"];
  for (let i = 0; i < 3; i++) {
    const slot = document.querySelector(`.podium-slot.${slots[i]}`);
    if (!slot) continue;
    const person = members[i];
    const nameEl = slot.querySelector(".podium-name");
    const pointsEl = slot.querySelector(".podium-points");
    const prevPoints = Number(pointsEl.textContent) || 0;
    if (person) {
      nameEl.textContent = person.name;
      animateNumber(pointsEl, prevPoints, person.points);
      nameEl.dataset.person = person.name;
      nameEl.classList.add("lb-person-clickable");
    } else {
      nameEl.textContent = "—";
      pointsEl.textContent = "—";
      nameEl.removeAttribute("data-person");
      nameEl.classList.remove("lb-person-clickable");
    }
  }

  // Track existing rows by person name
  const existingRows = {};
  document.querySelectorAll(".lb-person-name[data-person]").forEach((el) => {
    const name = el.dataset.person;
    existingRows[name] = el.closest(".lb-row");
  });

  const newNames = members.map((m) => m.name);

  // Remove rows for members no longer present
  Object.keys(existingRows).forEach((name) => {
    if (!newNames.includes(name)) {
      const row = existingRows[name];
      if (row) {
        row.style.transition =
          "opacity 300ms ease, height 300ms ease, margin 300ms ease";
        row.style.opacity = 0;
        row.style.height = 0;
        row.style.margin = 0;
        setTimeout(() => row.remove(), 350);
      }
      delete existingRows[name];
    }
  });

  // Insert/update rows in correct order
  members.forEach((m, idx) => {
    const barPct = Math.round((m.points / max_pts) * 1000) / 10;
    let row = existingRows[m.name];
    if (row) {
      // update rank classes
      row.classList.remove("rank-1", "rank-2", "rank-3");
      if (idx === 0) row.classList.add("rank-1");
      if (idx === 1) row.classList.add("rank-2");
      if (idx === 2) row.classList.add("rank-3");

      // update pos
      const posEl = row.querySelector(".lb-pos");
      if (posEl) posEl.textContent = idx + 1;

      // update bar width (CSS transition handles smoothness)
      const fill = row.querySelector(".lb-bar-fill");
      if (fill) fill.style.width = `${barPct}%`;

      // animate score
      const scoreEl = row.querySelector(".lb-score");
      const prevScore = Number(scoreEl.textContent) || 0;
      animateNumber(scoreEl, prevScore, m.points);

      // highlight
      row.classList.add("updated");
      setTimeout(() => row.classList.remove("updated"), 700);
    } else {
      // create new row element
      const div = document.createElement("div");
      div.className = "lb-row";
      if (idx === 0) div.classList.add("rank-1");
      if (idx === 1) div.classList.add("rank-2");
      if (idx === 2) div.classList.add("rank-3");
      div.style.opacity = 0;
      div.innerHTML = `\n    <div class="lb-pos">${idx + 1}</div>\n    <div class="lb-avatar ${idx == 0 ? "rank-1-avatar" : idx == 1 ? "rank-2-avatar" : idx == 2 ? "rank-3-avatar" : ""}"><i data-lucide="${m.avatar || "user"}"></i></div>\n    <div class="lb-info">\n      <div class="lb-name-row">\n        <div class="lb-person-name lb-person-clickable" data-person="${m.name}"> ${m.name} </div>\n      </div>\n      <div class="lb-bar-wrap">\n        <div class="lb-bar-track">\n          <div class="lb-bar-fill" style="width: ${barPct}%"></div>\n        </div>\n      </div>\n    </div>\n    <div class="lb-score-wrap">\n      <span class="lb-score"> ${formatPts(m.points)} </span>\n      <span class="lb-score-label">points</span>\n    </div>`;
      // insert at position
      const ref = list.children[idx] || null;
      list.insertBefore(div, ref);
      // animate in
      setTimeout(() => {
        div.style.transition = "opacity 300ms ease";
        div.style.opacity = 1;
      }, 20);
      lucide.createIcons();
      // attach click handler
      const nameEl = div.querySelector(".lb-person-name");
      if (nameEl)
        nameEl.addEventListener("click", () =>
          openPersonModal(nameEl.dataset.person),
        );
    }

    // ensure row is at correct index
    const target = list.children[idx];
    const current =
      existingRows[m.name] ||
      list
        .querySelector(`.lb-person-name[data-person="${m.name}"]`)
        .closest(".lb-row");
    if (current && current !== target) {
      list.insertBefore(current, target);
    }
  });

  // rebind any remaining clickable names
  document.querySelectorAll(".lb-person-clickable").forEach((el) => {
    el.replaceWith(el.cloneNode(true));
  });

  lucide.createIcons();
}

// expose for external callers
window.updateLeaderboardFromStats = updateLeaderboardFromStats;
