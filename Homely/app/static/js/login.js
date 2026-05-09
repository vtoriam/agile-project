// ── Password visibility toggle ────────────────────
const pwInput  = document.getElementById('password');
const pwToggle = document.getElementById('pwToggle');

if (pwToggle && pwInput) {
  pwToggle.addEventListener('click', () => {
    const isHidden = pwInput.type === 'password';
    pwInput.type = isHidden ? 'text' : 'password';
    pwToggle.innerHTML = isHidden
      ? '<i data-lucide="eye-off"></i>'
      : '<i data-lucide="eye"></i>';
    lucide.createIcons();
  });
}

// ── Client-side validation ────────────────────────
const form          = document.getElementById('loginForm');
const emailInput    = document.getElementById('email');
const emailError    = document.getElementById('emailError');
const passwordError = document.getElementById('passwordError');

function clearErrors() {
  emailInput.classList.remove('error');
  pwInput.classList.remove('error');
  emailError.textContent   = '';
  passwordError.textContent = '';
}

function validateEmail(val) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val);
}

if (form) {
  form.addEventListener('submit', (e) => {
    clearErrors();
    let valid = true;

    if (!emailInput.value.trim()) {
      emailInput.classList.add('error');
      emailError.textContent = 'Please enter your email address.';
      valid = false;
    } else if (!validateEmail(emailInput.value.trim())) {
      emailInput.classList.add('error');
      emailError.textContent = 'Please enter a valid email address.';
      valid = false;
    }

    if (!pwInput.value) {
      pwInput.classList.add('error');
      passwordError.textContent = 'Please enter your password.';
      valid = false;
    }

    if (!valid) e.preventDefault();
  });

  // Clear error on input
  emailInput.addEventListener('input', () => {
    emailInput.classList.remove('error');
    emailError.textContent = '';
  });

  pwInput.addEventListener('input', () => {
    pwInput.classList.remove('error');
    passwordError.textContent = '';
  });
}
