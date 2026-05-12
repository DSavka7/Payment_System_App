
const ProfilePage = (() => {
  let _userData = null;
  let _accounts = [];
  let _editMode = false;

  // ── Головна точка входу ───────────────────────────────────────────
  async function load() {
    const user = Store.getUser();
    if (!user) return;

    _setLoadingSkeleton();

    try {
      const [freshUser, accounts] = await Promise.all([
        Api.getMe(),
        Api.getUserAccounts(user.id),
      ]);

      _userData = freshUser.blocked ? user : freshUser;
      _accounts = Array.isArray(accounts) ? accounts : [];

      Store.setUser(_userData);
      _render();
    } catch (err) {
      document.getElementById('profile-container').innerHTML =
        `<div class="empty-state">Помилка завантаження: ${err.message}</div>`;
    }
  }

  // ── Skeleton ──────────────────────────────────────────────────────
  function _setLoadingSkeleton() {
    const c = document.getElementById('profile-container');
    c.innerHTML = `
      <div class="skeleton" style="height:140px;border-radius:var(--radius-lg);margin-bottom:24px"></div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px">
        <div class="skeleton" style="height:260px;border-radius:var(--radius-md)"></div>
        <div class="skeleton" style="height:260px;border-radius:var(--radius-md)"></div>
        <div class="skeleton" style="height:200px;border-radius:var(--radius-md)"></div>
        <div class="skeleton" style="height:200px;border-radius:var(--radius-md)"></div>
      </div>
    `;
  }

  // ── Рендер ────────────────────────────────────────────────────────
  function _render() {
    const u = _userData;
    const initials = ((u.first_name || '')[0] + (u.last_name || '')[0]).toUpperCase() || u.email[0].toUpperCase();
    const since = new Date(u.created_at).toLocaleDateString('uk-UA', { month: 'long', year: 'numeric' });

    const activeAccounts = _accounts.filter(a => a.status === 'active').length;
    const totalUAH = _accounts.filter(a => a.currency === 'UAH').reduce((s, a) => s + a.balance, 0);
    const totalUSD = _accounts.filter(a => a.currency === 'USD').reduce((s, a) => s + a.balance, 0);
    const totalEUR = _accounts.filter(a => a.currency === 'EUR').reduce((s, a) => s + a.balance, 0);

    document.getElementById('profile-container').innerHTML = `

      <!-- Hero -->
      <div class="profile-hero" style="animation:fade-up .4s ease both">
        <div class="profile-avatar" id="profile-avatar-el">${initials}</div>
        <div class="profile-hero__info">
          <div class="profile-hero__name" id="profile-hero-name">${_esc(u.first_name)} ${_esc(u.last_name)}</div>
          <div class="profile-hero__email">${_esc(u.email)}</div>
          <div class="profile-hero__meta">
            <span class="profile-hero__badge profile-hero__badge--user">
              ${u.role === 'ADMIN' ? '⚙ Admin' : '◆ User'}
            </span>
            <span class="profile-hero__badge profile-hero__badge--since">
              З ${since}
            </span>
            ${UI.statusBadge(u.status)}
          </div>
        </div>
        <div class="profile-hero__actions">
          <button class="btn btn--outline btn--sm" id="profile-edit-toggle">
            ✎ Редагувати профіль
          </button>
          <button class="btn btn--ghost btn--sm" id="profile-copy-id" title="Копіювати ID">
            ⊕ ID: ···${u.id.slice(-6)}
          </button>
        </div>
      </div>

      <div class="profile-grid">

        <!-- Особисті дані -->
        <div class="profile-card" style="animation:fade-up .4s .05s ease both">
          <div class="profile-card__title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
            Особисті дані
          </div>

          <div id="profile-view-mode">
            <div class="info-row">
              <span class="info-row__label">Ім'я</span>
              <span class="info-row__value">${_esc(u.first_name)}</span>
            </div>
            <div class="info-row">
              <span class="info-row__label">Прізвище</span>
              <span class="info-row__value">${_esc(u.last_name)}</span>
            </div>
            <div class="info-row">
              <span class="info-row__label">Email</span>
              <span class="info-row__value info-row__value--mono">${_esc(u.email)}</span>
            </div>
            <div class="info-row">
              <span class="info-row__label">Телефон</span>
              <span class="info-row__value info-row__value--mono">${_esc(u.phone || '—')}</span>
            </div>
            <div class="info-row">
              <span class="info-row__label">Статус</span>
              <span class="info-row__value">${UI.statusBadge(u.status)}</span>
            </div>

            <!-- Причина блокування -->
            ${u.block_reason ? `
            <div class="info-row" style="background:rgba(239,68,68,0.1);border-left:4px solid var(--red);padding:12px 14px;border-radius:8px;margin:8px 0;">
              <span class="info-row__label" style="color:var(--red)">Причина блокування</span>
              <span class="info-row__value" style="color:var(--red);font-weight:500">${_esc(u.block_reason)}</span>
            </div>` : ''}

            <div class="info-row">
              <span class="info-row__label">Роль</span>
              <span class="info-row__value info-row__value--gold">${u.role}</span>
            </div>
            <div class="info-row">
              <span class="info-row__label">Реєстрація</span>
              <span class="info-row__value">${UI.formatDate(u.created_at)}</span>
            </div>
          </div>

          <!-- Режим редагування -->
          <div id="profile-edit-mode" class="profile-edit-form">
            <form id="form-profile-edit" class="form" novalidate>
              <div class="field-row">
                <div class="field">
                  <label class="field__label" for="edit-first-name">Ім'я</label>
                  <input class="field__input" id="edit-first-name" type="text" value="${_esc(u.first_name)}" maxlength="50" />
                  <span class="field__error" id="edit-first-name-err"></span>
                </div>
                <div class="field">
                  <label class="field__label" for="edit-last-name">Прізвище</label>
                  <input class="field__input" id="edit-last-name" type="text" value="${_esc(u.last_name)}" maxlength="50" />
                  <span class="field__error" id="edit-last-name-err"></span>
                </div>
              </div>
              <div class="field">
                <label class="field__label" for="edit-phone">Телефон</label>
                <input class="field__input" id="edit-phone" type="tel" value="${_esc(u.phone || '')}" placeholder="+380XXXXXXXXX" />
                <span class="field__error" id="edit-phone-err"></span>
              </div>
              <div id="edit-error" class="alert alert--error hidden"></div>
              <div id="edit-success" class="alert alert--success hidden"></div>
              <div style="display:flex;gap:8px;margin-top:4px">
                <button type="button" class="btn btn--outline btn--sm" id="profile-cancel-edit">Скасувати</button>
                <button type="submit" class="btn btn--primary btn--sm">
                  <span class="btn__text">Зберегти</span>
                  <span class="btn__loader hidden"></span>
                </button>
              </div>
            </form>
          </div>
        </div>

        <!-- Статистика -->
        <div class="profile-card" style="animation:fade-up .4s .1s ease both">
          <div class="profile-card__title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M18 20V10M12 20V4M6 20v-6"/></svg>
            Статистика
          </div>
          <div class="profile-stats" style="margin-bottom:16px">
            <div class="profile-stat">
              <div class="profile-stat__val">${_accounts.length}</div>
              <div class="profile-stat__label">Рахунків</div>
            </div>
            <div class="profile-stat">
              <div class="profile-stat__val">${activeAccounts}</div>
              <div class="profile-stat__label">Активних</div>
            </div>
            <div class="profile-stat">
              <div class="profile-stat__val" id="profile-tx-count">—</div>
              <div class="profile-stat__label">Транзакцій</div>
            </div>
          </div>
          <div style="display:flex;flex-direction:column;gap:8px">
            ${totalUAH > 0 ? `<div class="info-row" style="padding:8px 0"><span class="info-row__label">Баланс UAH</span><span class="info-row__value info-row__value--gold" style="font-family:var(--font-display);font-size:1.1rem">${UI.formatMoney(totalUAH, 'UAH')}</span></div>` : ''}
            ${totalUSD > 0 ? `<div class="info-row" style="padding:8px 0"><span class="info-row__label">Баланс USD</span><span class="info-row__value" style="font-family:var(--font-display);font-size:1.1rem">${UI.formatMoney(totalUSD, 'USD')}</span></div>` : ''}
            ${totalEUR > 0 ? `<div class="info-row" style="padding:8px 0"><span class="info-row__label">Баланс EUR</span><span class="info-row__value" style="font-family:var(--font-display);font-size:1.1rem">${UI.formatMoney(totalEUR, 'EUR')}</span></div>` : ''}
          </div>
        </div>

        <!-- Безпека (без 2FA) -->
        <div class="profile-card" style="animation:fade-up .4s .15s ease both">
          <div class="profile-card__title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
            Безпека
          </div>

          <div class="security-item">
            <div class="security-item__icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
            </div>
            <div class="security-item__body">
              <div class="security-item__title">Пароль</div>
              <div class="security-item__sub">Змінено: невідомо</div>
            </div>
            <button class="btn btn--outline btn--sm" id="toggle-pwd-form">Змінити</button>
          </div>

          <!-- Форма зміни пароля -->
          <div class="pwd-form" id="pwd-form">
            <form id="form-change-pwd" class="form" novalidate style="margin-top:0">
              <div class="field">
                <label class="field__label" for="pwd-current">Поточний пароль</label>
                <input class="field__input" id="pwd-current" type="password" placeholder="••••••••" />
                <span class="field__error" id="pwd-current-err"></span>
              </div>
              <div class="field">
                <label class="field__label" for="pwd-new">Новий пароль</label>
                <input class="field__input" id="pwd-new" type="password" placeholder="мін. 8 символів" />
                <span class="field__error" id="pwd-new-err"></span>
              </div>
              <div class="field">
                <label class="field__label" for="pwd-confirm">Підтвердження</label>
                <input class="field__input" id="pwd-confirm" type="password" placeholder="повторіть пароль" />
                <span class="field__error" id="pwd-confirm-err"></span>
              </div>
              <div id="pwd-error" class="alert alert--error hidden"></div>
              <div id="pwd-success" class="alert alert--success hidden"></div>
              <div style="display:flex;gap:8px">
                <button type="button" class="btn btn--outline btn--sm" id="cancel-pwd-form">Скасувати</button>
                <button type="submit" class="btn btn--primary btn--sm">
                  <span class="btn__text">Змінити пароль</span>
                  <span class="btn__loader hidden"></span>
                </button>
              </div>
            </form>
          </div>
        </div>

        <!-- Остання активність -->
        <div class="profile-card" style="animation:fade-up .4s .2s ease both">
          <div class="profile-card__title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
            Остання активність
          </div>
          <div id="profile-recent-tx">
            <div class="skeleton" style="height:40px;border-radius:6px;margin-bottom:8px"></div>
            <div class="skeleton" style="height:40px;border-radius:6px;margin-bottom:8px"></div>
            <div class="skeleton" style="height:40px;border-radius:6px"></div>
          </div>
        </div>

      </div>
    `;

    _loadRecentActivity();
    _bindEvents();
  }

  // ── Остання активність ─────────────────────────────────────────────
  async function _loadRecentActivity() {
    const container = document.getElementById('profile-recent-tx');
    const countEl = document.getElementById('profile-tx-count');
    if (!container) return;

    try {
      if (_accounts.length === 0) {
        container.innerHTML = '<div class="empty-state" style="padding:16px;font-size:.82rem">Немає рахунків</div>';
        if (countEl) countEl.textContent = '0';
        return;
      }

      const data = await Api.getAccountTx(_accounts[0].id, 5, 0);
      const items = data.items || [];

      if (countEl) countEl.textContent = data.total ?? items.length;

      if (!items.length) {
        container.innerHTML = '<div class="empty-state" style="padding:16px;font-size:.82rem">Транзакцій немає</div>';
        return;
      }

      container.innerHTML = '';
      items.forEach(tx => {
        const isOut = tx.from_account_id === _accounts[0].id;
        const sym = { UAH: '₴', USD: '$', EUR: '€' }[tx.currency] || '';
        const div = document.createElement('div');
        div.className = 'tx-item';
        div.style.cssText = 'padding:10px 0;animation:fade-up .3s ease both';
        div.innerHTML = `
          <div class="tx-item__icon ${isOut ? 'tx-item__icon--out' : 'tx-item__icon--in'}">
            ${isOut ? 'OUT' : 'IN'}
          </div>
          <div class="tx-item__body">
            <div class="tx-item__desc">${_esc(tx.description || tx.type)}</div>
            <div class="tx-item__date">${UI.formatDate(tx.created_at)}</div>
          </div>
          <div class="tx-item__amount ${isOut ? 'tx-item__amount--out' : 'tx-item__amount--in'}">
            ${isOut ? '−' : '+'}${sym}${Number(tx.amount).toLocaleString('uk-UA', { minimumFractionDigits: 2 })}
          </div>
        `;
        container.appendChild(div);
      });
    } catch (e) {
      container.innerHTML = '<div class="empty-state" style="padding:16px;font-size:.82rem">Помилка завантаження</div>';
    }
  }

  // ── Events ────────────────────────────────────────────────────────
  function _bindEvents() {
    document.getElementById('profile-edit-toggle')?.addEventListener('click', () => _toggleEditMode(true));
    document.getElementById('profile-cancel-edit')?.addEventListener('click', () => _toggleEditMode(false));
    document.getElementById('profile-copy-id')?.addEventListener('click', () => {
      navigator.clipboard?.writeText(_userData.id).catch(() => {});
      UI.toast('ID скопійовано ✓', 'success', 2000);
    });

    document.getElementById('form-profile-edit')?.addEventListener('submit', _handleEditSubmit);
    document.getElementById('toggle-pwd-form')?.addEventListener('click', togglePasswordForm);
    document.getElementById('cancel-pwd-form')?.addEventListener('click', togglePasswordForm);
    document.getElementById('form-change-pwd')?.addEventListener('submit', _handlePasswordChange);
  }

  function togglePasswordForm() {
    const form = document.getElementById('pwd-form');
    const btn = document.getElementById('toggle-pwd-form');
    const isActive = form.classList.toggle('active');
    btn.textContent = isActive ? 'Скасувати' : 'Змінити';
    if (!isActive) document.getElementById('form-change-pwd').reset();
  }

  function _toggleEditMode(active) {
    _editMode = active;
    const viewEl = document.getElementById('profile-view-mode');
    const editEl = document.getElementById('profile-edit-mode');
    const btn = document.getElementById('profile-edit-toggle');

    if (active) {
      viewEl.classList.add('hidden-view');
      editEl.classList.add('active');
      btn.textContent = '✕ Скасувати';
    } else {
      viewEl.classList.remove('hidden-view');
      editEl.classList.remove('active');
      btn.textContent = '✎ Редагувати профіль';
      document.getElementById('edit-first-name').value = _userData.first_name || '';
      document.getElementById('edit-last-name').value = _userData.last_name || '';
      document.getElementById('edit-phone').value = _userData.phone || '';
    }
  }

  // ── Інші функції (редагування, пароль)
  async function _handleEditSubmit(e) { /* ... */ }
  async function _handlePasswordChange(e) { /* ... */ }
  async function _apiPatch(path, body) { /* ... */ }

  function _esc(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  return { load };
})();