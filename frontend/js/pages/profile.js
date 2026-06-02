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
    const sinceLoc = I18n.getLang() === 'en' ? 'en-GB' : 'uk-UA';
    const since = new Date(u.created_at).toLocaleDateString(sinceLoc, { month: 'long', year: 'numeric' });

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
            ${I18n.t('profile.edit')}
          </button>
          <button class="btn btn--ghost btn--sm" id="profile-copy-id" title="Копіювати ID">
            ⊕ ID: ···${u.id.slice(-6)}
          </button>
          <button class="btn btn--primary btn--sm" id="profile-export-pdf-btn" style="gap:6px;display:flex;align-items:center">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="13" height="13">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
              <line x1="12" y1="18" x2="12" y2="12"/>
              <line x1="9" y1="15" x2="15" y2="15"/>
            </svg>
            ${I18n.t('profile.export_pdf')}
          </button>
        </div>
      </div>

      <div class="profile-grid">

        <!-- Особисті дані -->
        <div class="profile-card" style="animation:fade-up .4s .05s ease both">
          <div class="profile-card__title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
            ${I18n.t('profile.personal')}
          </div>

          <div id="profile-view-mode">
            <div class="info-row">
              <span class="info-row__label">${I18n.t('profile.first_name')}</span>
              <span class="info-row__value">${_esc(u.first_name)}</span>
            </div>
            <div class="info-row">
              <span class="info-row__label">${I18n.t('profile.last_name')}</span>
              <span class="info-row__value">${_esc(u.last_name)}</span>
            </div>
            <div class="info-row">
              <span class="info-row__label">${I18n.t('profile.email')}</span>
              <span class="info-row__value info-row__value--mono">${_esc(u.email)}</span>
            </div>
            <div class="info-row">
              <span class="info-row__label">${I18n.t('profile.phone')}</span>
              <span class="info-row__value info-row__value--mono">${_esc(u.phone || '—')}</span>
            </div>
            <div class="info-row">
              <span class="info-row__label">${I18n.t('profile.status')}</span>
              <span class="info-row__value">${UI.statusBadge(u.status)}</span>
            </div>

            <!-- Причина блокування -->
            ${u.block_reason ? `
            <div class="info-row" style="background:rgba(239,68,68,0.1);border-left:4px solid var(--red);padding:12px 14px;border-radius:8px;margin:8px 0;">
              <span class="info-row__label" style="color:var(--red)">${I18n.t('profile.block_reason')}</span>
              <span class="info-row__value" style="color:var(--red);font-weight:500">${_esc(u.block_reason)}</span>
            </div>` : ''}

            <div class="info-row">
              <span class="info-row__label">${I18n.t('profile.role')}</span>
              <span class="info-row__value info-row__value--gold">${u.role}</span>
            </div>
            <div class="info-row">
              <span class="info-row__label">${I18n.t('profile.registered')}</span>
              <span class="info-row__value">${UI.formatDate(u.created_at)}</span>
            </div>
          </div>

          <!-- Режим редагування -->
          <div id="profile-edit-mode" class="profile-edit-form">
            <form id="form-profile-edit" class="form" novalidate>
              <div class="field-row">
                <div class="field">
                  <label class="field__label" for="edit-first-name">${I18n.t('profile.first_name')}</label>
                  <input class="field__input" id="edit-first-name" type="text" value="${_esc(u.first_name)}" maxlength="50" />
                  <span class="field__error" id="edit-first-name-err"></span>
                </div>
                <div class="field">
                  <label class="field__label" for="edit-last-name">${I18n.t('profile.last_name')}</label>
                  <input class="field__input" id="edit-last-name" type="text" value="${_esc(u.last_name)}" maxlength="50" />
                  <span class="field__error" id="edit-last-name-err"></span>
                </div>
              </div>
              <div class="field">
                <label class="field__label" for="edit-phone">${I18n.t('profile.phone')}</label>
                <input class="field__input" id="edit-phone" type="tel" value="${_esc(u.phone || '')}" placeholder="+380XXXXXXXXX" />
                <span class="field__error" id="edit-phone-err"></span>
              </div>
              <div id="edit-error" class="alert alert--error hidden"></div>
              <div id="edit-success" class="alert alert--success hidden"></div>
              <div style="display:flex;gap:8px;margin-top:4px">
                <button type="button" class="btn btn--outline btn--sm" id="profile-cancel-edit">${I18n.t('profile.cancel')}</button>
                <button type="submit" class="btn btn--primary btn--sm">
                  <span class="btn__text">${I18n.t('profile.save')}</span>
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
            ${I18n.t('profile.stats')}
          </div>
          <div class="profile-stats" style="margin-bottom:16px">
            <div class="profile-stat">
              <div class="profile-stat__val">${_accounts.length}</div>
              <div class="profile-stat__label">${I18n.t('profile.accounts_count')}</div>
            </div>
            <div class="profile-stat">
              <div class="profile-stat__val">${activeAccounts}</div>
              <div class="profile-stat__label">${I18n.t('profile.active_count')}</div>
            </div>
            <div class="profile-stat">
              <div class="profile-stat__val" id="profile-tx-count">—</div>
              <div class="profile-stat__label">${I18n.t('profile.tx_count')}</div>
            </div>
          </div>
          <div style="display:flex;flex-direction:column;gap:8px">
            ${totalUAH > 0 ? `<div class="info-row" style="padding:8px 0"><span class="info-row__label">${I18n.t('profile.bal_uah', 'UAH')}</span><span class="info-row__value info-row__value--gold" style="font-family:var(--font-display);font-size:1.1rem">${UI.formatMoney(totalUAH, 'UAH')}</span></div>` : ''}
            ${totalUSD > 0 ? `<div class="info-row" style="padding:8px 0"><span class="info-row__label">${I18n.t('profile.bal_usd', 'USD')}</span><span class="info-row__value" style="font-family:var(--font-display);font-size:1.1rem">${UI.formatMoney(totalUSD, 'USD')}</span></div>` : ''}
            ${totalEUR > 0 ? `<div class="info-row" style="padding:8px 0"><span class="info-row__label">${I18n.t('profile.bal_eur', 'EUR')}</span><span class="info-row__value" style="font-family:var(--font-display);font-size:1.1rem">${UI.formatMoney(totalEUR, 'EUR')}</span></div>` : ''}
          </div>
        </div>

        <!-- Безпека (без 2FA) -->
        <div class="profile-card" style="animation:fade-up .4s .15s ease both">
          <div class="profile-card__title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
            ${I18n.t('profile.security')}
          </div>

          <div class="security-item">
            <div class="security-item__icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
            </div>
            <div class="security-item__body">
              <div class="security-item__title">${I18n.t('profile.password')}</div>
              <div class="security-item__sub">${I18n.t('profile.pw_protected')}</div>
            </div>
            <button class="btn btn--outline btn--sm" id="toggle-pwd-form">${I18n.t('profile.pw_change')}</button>
          </div>

          <!-- Форма зміни пароля -->
          <div class="pwd-form" id="pwd-form">
            <form id="form-change-pwd" class="form" novalidate style="margin-top:0">

              <!-- Поточний пароль -->
              <div class="field">
                <label class="field__label" for="pwd-current">${I18n.t('profile.pwd.current')}</label>
                <div class="field__password-wrap">
                  <input class="field__input" id="pwd-current" type="password" placeholder="••••••••" autocomplete="current-password" />
                  <button type="button" class="field__eye-btn" id="pwd-current-eye" aria-label="Показати пароль">
                    <svg class="field__eye-icon" id="pwd-current-eye-show" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                    <svg class="field__eye-icon" id="pwd-current-eye-hide" style="display:none" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
                  </button>
                </div>
                <span class="field__error" id="pwd-current-err"></span>
              </div>

              <!-- Новий пароль -->
              <div class="field">
                <label class="field__label" for="pwd-new">${I18n.t('profile.pwd.new')}</label>
                <div class="field__password-wrap">
                  <input class="field__input" id="pwd-new" type="password" placeholder="мін. 8 символів" autocomplete="new-password" />
                  <button type="button" class="field__eye-btn" id="pwd-new-eye" aria-label="Показати пароль">
                    <svg class="field__eye-icon" id="pwd-new-eye-show" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                    <svg class="field__eye-icon" id="pwd-new-eye-hide" style="display:none" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
                  </button>
                </div>

                <!-- Індикатор сили пароля -->
                <div class="pwd-strength" id="chpwd-strength-wrap" style="display:none">
                  <div class="pwd-strength__bars">
                    <div class="pwd-strength__bar" id="chpwd-bar-1"></div>
                    <div class="pwd-strength__bar" id="chpwd-bar-2"></div>
                    <div class="pwd-strength__bar" id="chpwd-bar-3"></div>
                    <div class="pwd-strength__bar" id="chpwd-bar-4"></div>
                    <div class="pwd-strength__bar" id="chpwd-bar-5"></div>
                  </div>
                  <span class="pwd-strength__label" id="chpwd-strength-label"></span>
                </div>

                <!-- Вимоги до пароля -->
                <ul class="pwd-reqs" id="chpwd-reqs" style="display:none">
                  <li class="pwd-reqs__item" id="chpwd-req-len">
                    <svg class="pwd-reqs__icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="8" cy="8" r="6"/></svg>
                    ${I18n.t('auth.pwd.req.len')}
                  </li>
                  <li class="pwd-reqs__item" id="chpwd-req-upper">
                    <svg class="pwd-reqs__icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="8" cy="8" r="6"/></svg>
                    ${I18n.t('auth.pwd.req.upper')}
                  </li>
                  <li class="pwd-reqs__item" id="chpwd-req-lower">
                    <svg class="pwd-reqs__icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="8" cy="8" r="6"/></svg>
                    ${I18n.t('auth.pwd.req.lower')}
                  </li>
                  <li class="pwd-reqs__item" id="chpwd-req-digit">
                    <svg class="pwd-reqs__icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="8" cy="8" r="6"/></svg>
                    ${I18n.t('auth.pwd.req.digit')}
                  </li>
                  <li class="pwd-reqs__item" id="chpwd-req-special">
                    <svg class="pwd-reqs__icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="8" cy="8" r="6"/></svg>
                    ${I18n.t('auth.pwd.req.special')}
                  </li>
                  <li class="pwd-reqs__item" id="chpwd-req-diff">
                    <svg class="pwd-reqs__icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="8" cy="8" r="6"/></svg>
                    ${I18n.t('profile.pwd.req.diff')}
                  </li>
                </ul>

                <span class="field__error" id="pwd-new-err"></span>
              </div>

              <!-- Підтвердження пароля -->
              <div class="field">
                <label class="field__label" for="pwd-confirm">${I18n.t('profile.pwd.confirm')}</label>
                <div class="field__password-wrap">
                  <input class="field__input" id="pwd-confirm" type="password" placeholder="повторіть новий пароль" autocomplete="new-password" />
                  <button type="button" class="field__eye-btn" id="pwd-confirm-eye" aria-label="Показати пароль">
                    <svg class="field__eye-icon" id="pwd-confirm-eye-show" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                    <svg class="field__eye-icon" id="pwd-confirm-eye-hide" style="display:none" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
                  </button>
                </div>
                <!-- Індикатор збігу паролів -->
                <div id="pwd-match-hint" style="font-size:.75rem;margin-top:4px;display:none"></div>
                <span class="field__error" id="pwd-confirm-err"></span>
              </div>

              <div id="pwd-error" class="alert alert--error hidden"></div>
              <div id="pwd-success" class="alert alert--success hidden"></div>
              <div style="display:flex;gap:8px">
                <button type="button" class="btn btn--outline btn--sm" id="cancel-pwd-form">${I18n.t('profile.cancel')}</button>
                <button type="submit" class="btn btn--primary btn--sm" id="pwd-submit-btn">
                  <span class="btn__text">${I18n.t('profile.pwd.btn')}</span>
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
            ${I18n.t('profile.activity')}
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
        container.innerHTML = `<div class="empty-state" style="padding:16px;font-size:.82rem">${I18n.t('tx.no_account')}</div>`;
        if (countEl) countEl.textContent = '0';
        return;
      }

      const myAccountIds = _accounts.map(a => a.id);

      // Завантажуємо транзакції з усіх рахунків паралельно
      const results = await Promise.allSettled(
        _accounts.map(acc => Api.getAccountTx(acc.id, 20, 0))
      );

      // Збираємо унікальні транзакції та загальну кількість
      const seen = new Set();
      const allTx = [];
      let totalCount = 0;
      results.forEach(r => {
        if (r.status === 'fulfilled') {
          totalCount += r.value.total || 0;
          (r.value.items || []).forEach(tx => {
            if (!seen.has(tx.id)) {
              seen.add(tx.id);
              allTx.push(tx);
            }
          });
        }
      });

      // Сортуємо за датою (найновіші першими)
      allTx.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));

      if (countEl) countEl.textContent = totalCount || allTx.length;

      const items = allTx.slice(0, 5);

      if (!items.length) {
        container.innerHTML = `<div class="empty-state" style="padding:16px;font-size:.82rem">${I18n.t('tx.empty')}</div>`;
        return;
      }

      container.innerHTML = '';
      items.forEach(tx => {
        // isOut = гроші ВИХОДЯТЬ з наших рахунків
        const isOut = myAccountIds.includes(tx.from_account_id);
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
      container.innerHTML = `<div class="empty-state" style="padding:16px;font-size:.82rem">${I18n.t('common.error')}</div>`;
    }
  }

  // ── Events ────────────────────────────────────────────────────────
  function _bindEvents() {
    document.getElementById('profile-edit-toggle')?.addEventListener('click', () => _toggleEditMode(true));
    document.getElementById('profile-cancel-edit')?.addEventListener('click', () => _toggleEditMode(false));
    document.getElementById('profile-copy-id')?.addEventListener('click', () => {
      navigator.clipboard?.writeText(_userData.id).catch(() => {});
      UI.toast(I18n.t('common.success') + ' · ID', 'success', 2000);
    });

    // PDF export
    document.getElementById('profile-export-pdf-btn')?.addEventListener('click', () => {
      VaultPDF.exportAccountStatement(_userData, _accounts);
    });

    document.getElementById('form-profile-edit')?.addEventListener('submit', _handleEditSubmit);
    document.getElementById('toggle-pwd-form')?.addEventListener('click', togglePasswordForm);
    document.getElementById('cancel-pwd-form')?.addEventListener('click', togglePasswordForm);
    document.getElementById('form-change-pwd')?.addEventListener('submit', _handlePasswordChange);

    // ── Кнопки ока ──────────────────────────────────────────
    _bindEyeBtn('pwd-current-eye', 'pwd-current', 'pwd-current-eye-show', 'pwd-current-eye-hide');
    _bindEyeBtn('pwd-new-eye',     'pwd-new',     'pwd-new-eye-show',     'pwd-new-eye-hide');
    _bindEyeBtn('pwd-confirm-eye', 'pwd-confirm', 'pwd-confirm-eye-show', 'pwd-confirm-eye-hide');

    // ── Live-перевірка нового пароля ─────────────────────────
    document.getElementById('pwd-new')?.addEventListener('input', function () {
      const val = this.value;

      // Показуємо блоки тільки якщо є хоч один символ
      const strengthWrap = document.getElementById('chpwd-strength-wrap');
      const reqsList     = document.getElementById('chpwd-reqs');
      if (strengthWrap) strengthWrap.style.display = val.length ? 'flex' : 'none';
      if (reqsList)     reqsList.style.display     = val.length ? 'block' : 'none';

      _updatePwdStrength(val);
      _updatePwdRequirements(val);
      _updateMatchHint(); // оновити підказку збігу якщо confirm вже заповнений
    });

    // ── Live-перевірка підтвердження пароля ──────────────────
    document.getElementById('pwd-confirm')?.addEventListener('input', _updateMatchHint);
  }

  // ── Кнопка показу/приховання пароля ──────────────────────
  function _bindEyeBtn(btnId, inputId, showIconId, hideIconId) {
    const btn = document.getElementById(btnId);
    if (!btn) return;
    btn.addEventListener('click', () => {
      const input    = document.getElementById(inputId);
      const showIcon = document.getElementById(showIconId);
      const hideIcon = document.getElementById(hideIconId);
      if (!input) return;
      const isHidden = input.type === 'password';
      input.type = isHidden ? 'text' : 'password';
      if (showIcon) showIcon.style.display = isHidden ? 'none' : '';
      if (hideIcon) hideIcon.style.display = isHidden ? ''     : 'none';
    });
  }

  // ── Правила перевірки пароля ──────────────────────────────
  const PWD_RULES = [
    { id: 'chpwd-req-len',     test: v => v.length >= 8 },
    { id: 'chpwd-req-upper',   test: v => /[A-Z]/.test(v) },
    { id: 'chpwd-req-lower',   test: v => /[a-z]/.test(v) },
    { id: 'chpwd-req-digit',   test: v => /\d/.test(v) },
    { id: 'chpwd-req-special', test: v => /[!@#$%^&*()\-_=+\[\]{}|;:,.<>?]/.test(v) },
    { id: 'chpwd-req-diff',    test: v => {
        const cur = (document.getElementById('pwd-current')?.value || '').trim();
        return cur.length > 0 && v !== cur;
      }
    },
  ];

  const STRENGTH_MODS   = ['', 'weak', 'weak', 'fair', 'good', 'strong'];
  const STRENGTH_LABELS = () => ['', I18n.t('auth.pwd.strength.1'), I18n.t('auth.pwd.strength.2'), I18n.t('auth.pwd.strength.3'), I18n.t('auth.pwd.strength.4'), I18n.t('auth.pwd.strength.5')];

  function _updatePwdStrength(value) {
    // Рахуємо скільки правил (крім req-diff) виконано
    const baseRules = PWD_RULES.slice(0, 5);
    let score = baseRules.reduce((acc, r) => acc + (r.test(value) ? 1 : 0), 0);
    const display = value.length === 0 ? 0 : Math.max(1, Math.min(5, score + (value.length >= 12 ? 1 : 0)));
    const final   = value.length === 0 ? 0 : Math.max(1, display);

    for (let i = 1; i <= 5; i++) {
      const bar = document.getElementById(`chpwd-bar-${i}`);
      if (bar) bar.className = 'pwd-strength__bar' +
        (i <= final ? ` pwd-strength__bar--${STRENGTH_MODS[final]}` : '');
    }
    const labelEl = document.getElementById('chpwd-strength-label');
    if (labelEl) {
      labelEl.textContent = value.length ? STRENGTH_LABELS()[final] : '';
      labelEl.className   = 'pwd-strength__label' +
        (value.length ? ` pwd-strength__label--${STRENGTH_MODS[final]}` : '');
    }
  }

  function _updatePwdRequirements(value) {
    PWD_RULES.forEach(rule => {
      const el = document.getElementById(rule.id);
      if (el) el.classList.toggle('pwd-reqs__item--met', rule.test(value));
    });
  }

  function _updateMatchHint() {
    const newVal     = document.getElementById('pwd-new')?.value     || '';
    const confirmVal = document.getElementById('pwd-confirm')?.value || '';
    const hintEl     = document.getElementById('pwd-match-hint');
    if (!hintEl) return;

    if (!confirmVal) {
      hintEl.style.display = 'none';
      return;
    }
    hintEl.style.display = 'block';
    if (newVal === confirmVal) {
      hintEl.innerHTML = `<span style="color:var(--green)">${I18n.t('profile.pwd.match')}</span>`;
    } else {
      hintEl.innerHTML = `<span style="color:var(--red)">${I18n.t('profile.pwd.no_match')}</span>`;
    }
  }

  function _allPwdRulesMet(value) {
    return PWD_RULES.every(r => r.test(value));
  }

  function togglePasswordForm() {
    const form = document.getElementById('pwd-form');
    const btn  = document.getElementById('toggle-pwd-form');
    const isActive = form.classList.toggle('active');
    btn.textContent = isActive ? I18n.t('profile.cancel') : I18n.t('profile.pw_change');

    if (!isActive) {
      // Скидаємо форму і всі індикатори
      document.getElementById('form-change-pwd').reset();
      UI.clearErrors(document.getElementById('form-change-pwd'));
      UI.hideAlert('pwd-error');
      UI.hideAlert('pwd-success');

      const strengthWrap = document.getElementById('chpwd-strength-wrap');
      const reqsList     = document.getElementById('chpwd-reqs');
      const matchHint    = document.getElementById('pwd-match-hint');
      if (strengthWrap) strengthWrap.style.display = 'none';
      if (reqsList)     reqsList.style.display     = 'none';
      if (matchHint)    matchHint.style.display    = 'none';

      // Скидаємо bars
      for (let i = 1; i <= 5; i++) {
        const bar = document.getElementById(`chpwd-bar-${i}`);
        if (bar) bar.className = 'pwd-strength__bar';
      }
      // Скидаємо вимоги
      PWD_RULES.forEach(r => {
        const el = document.getElementById(r.id);
        if (el) el.classList.remove('pwd-reqs__item--met');
      });
    }
  }

  function _toggleEditMode(active) {
    _editMode = active;
    const viewEl = document.getElementById('profile-view-mode');
    const editEl = document.getElementById('profile-edit-mode');
    const btn = document.getElementById('profile-edit-toggle');

    if (active) {
      viewEl.classList.add('hidden-view');
      editEl.classList.add('active');
      btn.textContent = `✕ ${I18n.t('profile.cancel')}`;
    } else {
      viewEl.classList.remove('hidden-view');
      editEl.classList.remove('active');
      btn.textContent = I18n.t('profile.edit');
      document.getElementById('edit-first-name').value = _userData.first_name || '';
      document.getElementById('edit-last-name').value = _userData.last_name || '';
      document.getElementById('edit-phone').value = _userData.phone || '';
    }
  }

  // ── Редагування профілю ────────────────────────────────────
  async function _handleEditSubmit(e) {
    e.preventDefault();
    const form      = e.currentTarget;
    const firstName = document.getElementById('edit-first-name').value.trim();
    const lastName  = document.getElementById('edit-last-name').value.trim();
    const phone     = document.getElementById('edit-phone').value.trim();

    UI.clearErrors(form);
    UI.hideAlert('edit-error');
    UI.hideAlert('edit-success');

    let valid = true;
    if (!firstName || firstName.length < 2) {
      UI.showError('edit-first-name', I18n.getLang() === 'en' ? 'Minimum 2 characters' : 'Мінімум 2 символи');
      valid = false;
    }
    if (!lastName || lastName.length < 2) {
      UI.showError('edit-last-name', I18n.getLang() === 'en' ? 'Minimum 2 characters' : 'Мінімум 2 символи');
      valid = false;
    }
    if (phone && !/^\+380\d{9}$/.test(phone)) {
      UI.showError('edit-phone', I18n.getLang() === 'en' ? 'Format: +380XXXXXXXXX' : 'Формат: +380XXXXXXXXX');
      valid = false;
    }
    if (!valid) return;

    UI.setLoading(form, true);
    try {
      const updated = await _apiPatch(`/users/${_userData.id}`, {
        first_name: firstName,
        last_name:  lastName,
        phone:      phone || undefined,
      });
      _userData = updated;
      Store.setUser(updated);
      UI.showAlert('edit-success', '✓ ' + I18n.t('common.success'));

      // Оновлюємо ім'я у хедері
      const heroName = document.getElementById('profile-hero-name');
      if (heroName) heroName.textContent = `${updated.first_name} ${updated.last_name}`;

      // Оновлюємо sidebar
      document.getElementById('sidebar-email').textContent = updated.email || '—';

      setTimeout(() => _toggleEditMode(false), 1000);
    } catch (err) {
      UI.showAlert('edit-error', err.message || 'Помилка оновлення');
    } finally {
      UI.setLoading(form, false);
    }
  }

  // ── Зміна пароля ──────────────────────────────────────────
  async function _handlePasswordChange(e) {
    e.preventDefault();
    const form    = e.currentTarget;
    const current = document.getElementById('pwd-current').value;
    const newPwd  = document.getElementById('pwd-new').value;
    const confirm = document.getElementById('pwd-confirm').value;

    // Скидаємо попередні помилки
    UI.clearErrors(form);
    UI.hideAlert('pwd-error');
    UI.hideAlert('pwd-success');

    // ── Валідація ────────────────────────────────────────────
    let valid = true;

    // 1. Поточний пароль
    if (!current.trim()) {
      UI.showError('pwd-current', 'Введіть поточний пароль');
      valid = false;
    }

    // 2. Новий пароль — всі правила
    if (!newPwd) {
      UI.showError('pwd-new', 'Введіть новий пароль');
      valid = false;
    } else {
      const errors = [];
      if (newPwd.length < 8)                                          errors.push('мінімум 8 символів');
      if (!/[A-Z]/.test(newPwd))                                      errors.push('велика літера (A–Z)');
      if (!/[a-z]/.test(newPwd))                                      errors.push('мала літера (a–z)');
      if (!/\d/.test(newPwd))                                         errors.push('цифра (0–9)');
      if (!/[!@#$%^&*()\-_=+\[\]{}|;:,.<>?]/.test(newPwd))          errors.push('спецсимвол (!@#$%^&*…)');
      if (current.trim() && newPwd === current)                       errors.push('новий пароль має відрізнятись від поточного');

      if (errors.length > 0) {
        UI.showError('pwd-new', `Пароль не відповідає вимогам: ${errors.join(', ')}`);
        valid = false;
      }
    }

    // 3. Підтвердження
    if (!confirm) {
      UI.showError('pwd-confirm', 'Підтвердіть новий пароль');
      valid = false;
    } else if (newPwd && confirm !== newPwd) {
      UI.showError('pwd-confirm', 'Паролі не збігаються');
      valid = false;
    }

    if (!valid) return;

    // ── Відправка ────────────────────────────────────────────
    const submitBtn = document.getElementById('pwd-submit-btn');
    if (submitBtn) submitBtn.disabled = true;
    UI.setLoading(form, true);

    try {
      await _apiPatch(`/users/${_userData.id}`, {
        password:         newPwd,
        current_password: current,
      });

      UI.showAlert('pwd-success', '✓ ' + I18n.t('common.success'));
      form.reset();

      // Сховати індикатори
      const strengthWrap = document.getElementById('chpwd-strength-wrap');
      const reqsList     = document.getElementById('chpwd-reqs');
      const matchHint    = document.getElementById('pwd-match-hint');
      if (strengthWrap) strengthWrap.style.display = 'none';
      if (reqsList)     reqsList.style.display     = 'none';
      if (matchHint)    matchHint.style.display    = 'none';

      // Скинути індикатор сили
      for (let i = 1; i <= 5; i++) {
        const bar = document.getElementById(`chpwd-bar-${i}`);
        if (bar) bar.className = 'pwd-strength__bar';
      }

      setTimeout(() => togglePasswordForm(), 2000);
    } catch (err) {
      const msg = err.message || 'Помилка зміни пароля';
      // Якщо бекенд повернув помилку про невірний поточний пароль
      if (
        msg.toLowerCase().includes('невірний поточний') ||
        msg.toLowerCase().includes('невірн') ||
        msg.toLowerCase().includes('incorrect') ||
        msg.toLowerCase().includes('wrong') ||
        msg.toLowerCase().includes('current')
      ) {
        const errEl = document.getElementById('pwd-current-err');
        const inputEl = document.getElementById('pwd-current');
        if (errEl)   errEl.textContent = 'Невірний поточний пароль';
        if (inputEl) inputEl.classList.add('error');
      } else {
        UI.showAlert('pwd-error', msg);
      }
    } finally {
      UI.setLoading(form, false);
      if (submitBtn) submitBtn.disabled = false;
    }
  }

  // ── API helper ────────────────────────────────────────────
  async function _apiPatch(path, body) {
    const accessToken = Store.get('accessToken');
    const res = await fetch(`http://localhost:8000${path}`, {
      method:  'PATCH',
      headers: {
        'Content-Type':  'application/json',
        'Authorization': `Bearer ${accessToken}`,
      },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.detail || `HTTP ${res.status}`);
    }
    return res.json();
  }

  function _esc(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  // Re-render profile on language change
  if (typeof I18n !== 'undefined') {
    I18n.onLangChange(() => {
      // If profile container has rendered content, reload it
      const c = document.getElementById('profile-container');
      if (c && c.querySelector('.profile-hero') && _userData) {
        _render();
      }
    });
  }

  return { load };
})();