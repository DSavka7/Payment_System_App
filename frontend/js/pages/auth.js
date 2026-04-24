const AuthPage = (() => {

  // ── Перемикання між сторінками ──────────────────────────────────────

  document.getElementById('go-register').addEventListener('click', (e) => {
    e.preventDefault();
    document.getElementById('page-login').classList.remove('active');
    document.getElementById('page-register').classList.add('active');
  });

  document.getElementById('go-login').addEventListener('click', (e) => {
    e.preventDefault();
    document.getElementById('page-register').classList.remove('active');
    document.getElementById('page-login').classList.add('active');
  });

  // ── Вхід ───────────────────────────────────────────────────────────

  document.getElementById('form-login').addEventListener('submit', async (e) => {
    e.preventDefault();
    const form  = e.currentTarget;
    const email = document.getElementById('login-email').value.trim();
    const pass  = document.getElementById('login-password').value;

    UI.clearErrors(form);

    let valid = true;
    if (!email) { UI.showError('login-email', 'Введіть email'); valid = false; }
    if (!pass)  { UI.showError('login-password', 'Введіть пароль'); valid = false; }
    if (!valid) return;

    UI.setLoading(form, true);
    try {
      const tokens = await Api.login(email, pass);
      Store.setAuth(tokens);
      const user = await Api.getMe();
      Store.setUser(user);
      App.showApp();
    } catch (err) {
      UI.showAlert('login-error', err.message);
    } finally {
      UI.setLoading(form, false);
    }
  });

  // ── Показати / приховати пароль (форма входу) ───────────────────────

  document.getElementById('login-password-eye').addEventListener('click', function () {
    const input    = document.getElementById('login-password');
    const isHidden = input.type === 'password';
    input.type = isHidden ? 'text' : 'password';
    document.getElementById('login-eye-show').style.display = isHidden ? 'none' : '';
    document.getElementById('login-eye-hide').style.display = isHidden ? ''     : 'none';
  });

  // ── Слайдер надійності пароля ───────────────────────────────────────

  const PASSWORD_RULES = [
    { id: 'req-len',     test: (v) => v.length >= 8 },
    { id: 'req-upper',   test: (v) => /[A-Z]/.test(v) },
    { id: 'req-lower',   test: (v) => /[a-z]/.test(v) },
    { id: 'req-digit',   test: (v) => /\d/.test(v) },
    { id: 'req-special', test: (v) => /[!@#$%^&*()\-_=+\[\]{}|;:,.<>?]/.test(v) },
  ];

  const STRENGTH_LABELS = ['', 'Дуже слабкий', 'Слабкий', 'Задовільний', 'Добрий', 'Відмінний'];
  const STRENGTH_MODS   = ['', 'weak', 'weak', 'fair', 'good', 'strong'];

  function updatePasswordStrength(value) {
    let score = PASSWORD_RULES.reduce((acc, rule) => {
      const met = rule.test(value);
      document.getElementById(rule.id).classList.toggle('pwd-reqs__item--met', met);
      return acc + (met ? 1 : 0);
    }, 0);

    // Бонус за довжину ≥ 12
    const display = value.length === 0 ? 0 : Math.min(5, score + (value.length >= 12 ? 1 : 0));
    const final   = value.length === 0 ? 0 : Math.max(1, display);

    for (let i = 1; i <= 5; i++) {
      const bar = document.getElementById(`pwd-bar-${i}`);
      bar.className = 'pwd-strength__bar' +
        (i <= final ? ` pwd-strength__bar--${STRENGTH_MODS[final]}` : '');
    }

    const labelEl = document.getElementById('pwd-strength-label');
    labelEl.textContent = value.length ? STRENGTH_LABELS[final] : '';
    labelEl.className   = 'pwd-strength__label' +
      (value.length ? ` pwd-strength__label--${STRENGTH_MODS[final]}` : '');
  }

  document.getElementById('reg-password').addEventListener('input', function () {
    updatePasswordStrength(this.value);
  });

  // ── Показати / приховати пароль (форма реєстрації) ──────────────────

  document.getElementById('reg-password-eye').addEventListener('click', function () {
    const input    = document.getElementById('reg-password');
    const isHidden = input.type === 'password';
    input.type = isHidden ? 'text' : 'password';
    document.getElementById('eye-icon-show').style.display = isHidden ? 'none' : '';
    document.getElementById('eye-icon-hide').style.display = isHidden ? ''     : 'none';
  });

  // ── Допоміжні валідатори ─────────────────────────────────────────────

  function isValidName(value) {
    return value.length >= 2 && /^[A-Za-zА-ЯҐЄІЇа-яґєії'\-\s]+$/.test(value);
  }

  function allPasswordRulesMet(value) {
    return PASSWORD_RULES.every((rule) => rule.test(value));
  }

  // ── Реєстрація ──────────────────────────────────────────────────────

  document.getElementById('form-register').addEventListener('submit', async (e) => {
    e.preventDefault();
    const form      = e.currentTarget;
    const firstName = document.getElementById('reg-first-name').value.trim();
    const lastName  = document.getElementById('reg-last-name').value.trim();
    const email     = document.getElementById('reg-email').value.trim();
    const phone     = document.getElementById('reg-phone').value.trim();
    const pass      = document.getElementById('reg-password').value;

    UI.clearErrors(form);

    let valid = true;

    if (!isValidName(firstName)) {
      UI.showError('reg-first-name', "Лише літери, мін. 2 символи");
      valid = false;
    }
    if (!isValidName(lastName)) {
      UI.showError('reg-last-name', "Лише літери, мін. 2 символи");
      valid = false;
    }
    if (!email) {
      UI.showError('reg-email', 'Введіть email');
      valid = false;
    }
    if (!/^\+380\d{9}$/.test(phone)) {
      UI.showError('reg-phone', 'Формат: +380XXXXXXXXX');
      valid = false;
    }
    if (!allPasswordRulesMet(pass)) {
      UI.showError('reg-password', 'Пароль не відповідає всім вимогам');
      valid = false;
    }
    if (!valid) return;

    UI.setLoading(form, true);
    UI.hideAlert('reg-error');
    UI.hideAlert('reg-success');

    try {
      await Api.register({
        email,
        phone,
        password:   pass,
        first_name: firstName,
        last_name:  lastName,
      });
      UI.showAlert('reg-success', 'Акаунт створено! Тепер увійдіть у систему.');
      form.reset();
      updatePasswordStrength('');
      PASSWORD_RULES.forEach((r) => {
        document.getElementById(r.id).classList.remove('pwd-reqs__item--met');
      });
      setTimeout(() => {
        document.getElementById('page-register').classList.remove('active');
        document.getElementById('page-login').classList.add('active');
      }, 1800);
    } catch (err) {
      UI.showAlert('reg-error', err.message);
    } finally {
      UI.setLoading(form, false);
    }
  });

})();