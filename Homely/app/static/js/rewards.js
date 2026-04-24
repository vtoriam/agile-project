// Current user stats (in a real app these would come from a database)
const USER_POINTS = 1240;
const USER_STREAK = 4;

// Filter tabs
const filterTabs = document.querySelectorAll('.filter-tab');
const rewardItems = document.querySelectorAll('.reward-item');

filterTabs.forEach(tab => {
  tab.addEventListener('click', () => {
    // Update active tab
    filterTabs.forEach(t => t.classList.remove('active'));
    tab.classList.add('active');

    const filter = tab.dataset.filter;

    rewardItems.forEach(item => {
      const type = item.dataset.type;
      const isUnlocked = item.classList.contains('unlocked');

      if (filter === 'all') {
        item.style.display = 'flex';
      } else if (filter === 'unlocked') {
        item.style.display = isUnlocked ? 'flex' : 'none';
      } else {
        item.style.display = type === filter ? 'flex' : 'none';
      }
    });

    checkEmptyState();
  });
});

// Delete custom rewards
document.querySelectorAll('.btn-delete').forEach(btn => {
  btn.addEventListener('click', () => {
    const item = btn.closest('.reward-item');
    item.style.transition = 'opacity 0.2s, transform 0.2s';
    item.style.opacity = '0';
    item.style.transform = 'translateX(10px)';
    setTimeout(() => {
      item.remove();
      checkEmptyState();
    }, 200);
  });
});

// Reward type toggle — update label and icon
const rewardTypeSelect = document.getElementById('rewardType');
const thresholdLabel = document.getElementById('thresholdLabel');
const thresholdIcon = document.getElementById('thresholdIcon');
const thresholdInput = document.getElementById('thresholdValue');

rewardTypeSelect.addEventListener('change', () => {
  if (rewardTypeSelect.value === 'streak') {
    thresholdLabel.textContent = 'Days at #1 Required';
    thresholdIcon.textContent = '🔥';
    thresholdInput.placeholder = 'e.g. 5';
  } else {
    thresholdLabel.textContent = 'Points Required';
    thresholdIcon.textContent = '⚡';
    thresholdInput.placeholder = 'e.g. 500';
  }
});

// Add custom reward
document.getElementById('addRewardBtn').addEventListener('click', () => {
  const title = document.getElementById('rewardTitle').value.trim();
  const desc = document.getElementById('rewardDesc').value.trim();
  const type = document.getElementById('rewardType').value;
  const threshold = parseInt(document.getElementById('thresholdValue').value);
  const emoji = document.getElementById('rewardEmoji').value.trim() || '🎁';

  // Basic validation
  if (!title) {
    highlight('rewardTitle');
    return;
  }
  if (!threshold || threshold < 1) {
    highlight('thresholdValue');
    return;
  }

  // Determine if unlocked
  let isUnlocked = false;
  let statusText = '';
  let conditionHTML = '';

  if (type === 'points') {
    isUnlocked = USER_POINTS >= threshold;
    const remaining = threshold - USER_POINTS;
    statusText = isUnlocked ? '✓ Unlocked' : `🔒 ${remaining.toLocaleString()} pts away`;
    const progressPct = Math.min(100, Math.round((USER_POINTS / threshold) * 100));
    conditionHTML = `<span class="condition-badge points-badge">⚡ ${threshold.toLocaleString()} pts</span>`;
    if (!isUnlocked) {
      conditionHTML += `
        <div class="progress-wrap">
          <div class="progress-bar-custom">
            <div class="progress-fill" style="width:${progressPct}%"></div>
          </div>
          <span class="progress-label">${USER_POINTS.toLocaleString()} / ${threshold.toLocaleString()} pts</span>
        </div>`;
    }
  } else {
    isUnlocked = USER_STREAK >= threshold;
    const remaining = threshold - USER_STREAK;
    statusText = isUnlocked ? '✓ Unlocked' : `🔒 ${remaining} days away`;
    const progressPct = Math.min(100, Math.round((USER_STREAK / threshold) * 100));
    conditionHTML = `<span class="condition-badge streak-badge">🔥 ${threshold} day streak at #1</span>`;
    if (!isUnlocked) {
      conditionHTML += `
        <div class="progress-wrap">
          <div class="progress-bar-custom streak-bar">
            <div class="progress-fill streak-fill" style="width:${progressPct}%"></div>
          </div>
          <span class="progress-label">${USER_STREAK} / ${threshold} days</span>
        </div>`;
    }
  }

  const statusClass = isUnlocked ? 'status-unlocked' : 'status-locked';
  const itemClass = isUnlocked ? 'unlocked' : 'locked';

  const newItem = document.createElement('div');
  newItem.className = `reward-item custom-reward ${itemClass}`;
  newItem.dataset.type = 'custom';
  newItem.innerHTML = `
    <div class="reward-icon-wrap">
      <div class="reward-icon ${isUnlocked ? '' : 'muted'}">${emoji}</div>
    </div>
    <div class="reward-body">
      <div class="d-flex align-items-center gap-2">
        <div class="reward-title">${title}</div>
        <span class="custom-tag">Custom</span>
      </div>
      <p class="reward-desc">${desc || 'No description provided.'}</p>
      <div class="reward-condition">${conditionHTML}</div>
    </div>
    <div class="reward-status">
      <div class="${statusClass}">${statusText}</div>
      <button class="btn-delete" title="Delete reward">✕</button>
    </div>
  `;

  // Attach delete handler to new item
  newItem.querySelector('.btn-delete').addEventListener('click', () => {
    newItem.style.transition = 'opacity 0.2s, transform 0.2s';
    newItem.style.opacity = '0';
    newItem.style.transform = 'translateX(10px)';
    setTimeout(() => {
      newItem.remove();
      checkEmptyState();
    }, 200);
  });

  document.getElementById('rewardsList').appendChild(newItem);

  // Reset form
  document.getElementById('rewardTitle').value = '';
  document.getElementById('rewardDesc').value = '';
  document.getElementById('rewardEmoji').value = '';
  document.getElementById('thresholdValue').value = '';

  // Scroll to new item
  newItem.scrollIntoView({ behavior: 'smooth', block: 'center' });
});

// Highlight invalid field briefly
function highlight(id) {
  const el = document.getElementById(id);
  el.style.borderColor = '#e05c5c';
  el.focus();
  setTimeout(() => el.style.borderColor = '', 1500);
}

// Check if filtered list is empty and show empty state
function checkEmptyState() {
  const list = document.getElementById('rewardsList');
  const visible = [...list.querySelectorAll('.reward-item')].filter(
    i => i.style.display !== 'none'
  );

  const existing = list.querySelector('.empty-state');
  if (existing) existing.remove();

  if (visible.length === 0) {
    const empty = document.createElement('div');
    empty.className = 'empty-state';
    empty.innerHTML = `<div class="empty-icon">🎁</div><p>No rewards in this category yet.</p>`;
    list.appendChild(empty);
  }
}
