const App = (() => {

  function showAuth() {
    document.getElementById('auth-wrapper').classList.remove('hidden');
    document.getElementById('app-wrapper').classList.add('hidden');
    document.getElementById('blocked-wrapper').classList.add('hidden');
  }

  function showApp() {
    document.getElementById('auth-wrapper').classList.add('hidden');
    document.getElementById('blocked-wrapper').classList.add('hidden');
    document.getElementById('app-wrapper').classList.remove('hidden');
    _updateSidebar();
    navigateTo('dashboard');
    AccountsPage.load();
  }

  function showBlocked(blockInfo) {
    document.getElementById('auth-wrapper').classList.add('hidden');
    document.getElementById('app-wrapper').classList.add('hidden');
    document.getElementById('blocked-wrapper').classList.remove('hidden');

    const emailEl  = document.getElementById('blocked-email');
    const reasonEl = document.getElementById('blocked-reason');
    if (emailEl)  emailEl.textContent  = blockInfo.email        || '';
    if (reasonEl) reasonEl.textContent = blockInfo.block_reason || 'Причину не вказано';

    Store.set('blockedUserId', blockInfo.id);
    Store.set('blockedEmail',  blockInfo.email);

    const msgEl = document.getElementById('blocked-request-message');
    const errEl = document.getElementById('blocked-request-error');
    const sucEl = document.getElementById('blocked-request-success');
    if (msgEl) msgEl.value = '';
    if (errEl) errEl.classList.add('hidden');
    if (sucEl) sucEl.classList.add('hidden');
  }

  // ── Sidebar ───────────────────────────────────────────────────────

  function _updateSidebar() {
    const user = Store.getUser();
    if (!user) return;
    document.getElementById('sidebar-email').textContent  = user.email || '—';
    document.getElementById('sidebar-role').textContent   = user.role  || 'USER';
    document.getElementById('sidebar-avatar').textContent = (user.email || 'U')[0].toUpperCase();

    // Адмін посилання — завжди ховаємо (адмін іде на admin.html)
    const adminLink = document.getElementById('nav-admin');
    if (adminLink) adminLink.style.display = 'none';
  }

  // ── Navigation ────────────────────────────────────────────────────

  const PAGE_LOADERS = {
    dashboard:    () => DashboardPage.load(),
    accounts:     () => AccountsPage.load(),
    transfer:     () => {},
    transactions: () => TransactionsPage.load(),
    requests:     () => RequestsPage.load(),
    profile:      () => ProfilePage.load(),
  };

  const PAGE_TITLES = {
    dashboard:    'Огляд',
    accounts:     'Рахунки',
    transfer:     'Переказ коштів',
    transactions: 'Транзакції',
    requests:     'Запити',
    profile:      'Особистий кабінет',
  };

  function navigateTo(pageId) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

    const page = document.getElementById(`page-${pageId}`);
    const nav  = document.querySelector(`[data-page="${pageId}"]`);
    if (page) page.classList.add('active');
    if (nav)  nav.classList.add('active');

    const titleEl = document.getElementById('page-title');
    if (titleEl) titleEl.textContent = PAGE_TITLES[pageId] || pageId;

    const loader = PAGE_LOADERS[pageId];
    if (loader) loader();
  }

  document.querySelectorAll('.nav-item[data-page]').forEach(item => {
    item.addEventListener('click', e => {
      e.preventDefault();
      navigateTo(item.dataset.page);
    });
  });

  // ── Mobile sidebar ─────────────────────────────────────────────────

  const burger  = document.getElementById('sidebar-toggle');
  const sidebar = document.querySelector('.sidebar');
  const overlay = document.getElementById('sidebar-overlay');

  if (burger && sidebar && overlay) {
    const close  = () => {
      sidebar.classList.remove('open');
      overlay.classList.remove('visible');
      burger.classList.remove('open');
    };
    const toggle = () => {
      const o = sidebar.classList.toggle('open');
      overlay.classList.toggle('visible', o);
      burger.classList.toggle('open', o);
    };
    burger.addEventListener('click', toggle);
    overlay.addEventListener('click', close);
    document.querySelectorAll('.nav-item[data-page]').forEach(i => i.addEventListener('click', close));
  }

  // ── Logout ────────────────────────────────────────────────────────

  const logoutBtn = document.getElementById('btn-logout');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', async () => {
      const rt = Store.get('refreshToken');
      try { if (rt) await Api.logout(rt); } catch {}
      Store.clear();
      showAuth();
      UI.toast('Ви вийшли з системи', 'info');
    });
  }

  // ── Blocked page handlers ─────────────────────────────────────────

  const blockedLogoutBtn = document.getElementById('blocked-logout-btn');
  if (blockedLogoutBtn) {
    blockedLogoutBtn.addEventListener('click', async () => {
      const rt = Store.get('refreshToken');
      try { if (rt) await Api.logout(rt); } catch {}
      Store.clear();
      showAuth();
    });
  }

  const blockedForm = document.getElementById('blocked-request-form');
  if (blockedForm) {
    blockedForm.addEventListener('submit', async e => {
      e.preventDefault();
      const message   = document.getElementById('blocked-request-message').value.trim();
      const userId    = Store.get('blockedUserId');
      const errEl     = document.getElementById('blocked-request-error');
      const successEl = document.getElementById('blocked-request-success');
      const btn       = blockedForm.querySelector('button[type="submit"]');

      errEl.classList.add('hidden');
      successEl.classList.add('hidden');

      if (!message || message.length < 10) {
        errEl.textContent = 'Введіть повідомлення (мінімум 10 символів)';
        errEl.classList.remove('hidden');
        return;
      }
      if (!userId) {
        errEl.textContent = 'Помилка: спробуйте вийти та увійти знову.';
        errEl.classList.remove('hidden');
        return;
      }

      btn.disabled = true;
      const btnText = btn.querySelector('.btn__text');

      try {
        let accountId = userId;
        try {
          const accounts = await Api.getUserAccounts(userId);
          if (accounts && accounts.length > 0) accountId = accounts[0].id;
        } catch {}

        await Api.createRequest({ user_id: userId, account_id: accountId, type: 'UNBLOCK', message });

        successEl.textContent = '✓ Запит надіслано адміністратору. Очікуйте відповіді.';
        successEl.classList.remove('hidden');
        blockedForm.reset();

        let sec = 60;
        const t = setInterval(() => {
          sec--;
          if (sec <= 0) {
            clearInterval(t);
            btn.disabled = false;
            if (btnText) btnText.textContent = 'Надіслати запит на розблокування';
          } else {
            if (btnText) btnText.textContent = `Надіслано (${sec}с)`;
          }
        }, 1000);
      } catch (err) {
        errEl.textContent = err.message || 'Помилка. Спробуйте ще раз.';
        errEl.classList.remove('hidden');
        btn.disabled = false;
      }
    });
  }

  // ── Language toggle ───────────────────────────────────────────────

  const TRANS = {
    en: {
      'Огляд': 'Overview', 'Рахунки': 'Accounts', 'Переказ': 'Transfer',
      'Транзакції': 'Transactions', 'Запити': 'Requests', 'Кабінет': 'Profile',
      'Загальний баланс': 'Total Balance', 'Переказ коштів': 'Transfer Funds',
      'Особистий кабінет': 'My Profile',
    },
    uk: {}
  };

  document.querySelectorAll('.lang-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.lang-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const map = TRANS[btn.dataset.lang] || {};
      if (Object.keys(map).length) {
        document.querySelectorAll('.stat-card__label,.section-title,.nav-item span,.topbar__title').forEach(el => {
          const key = el.textContent.trim();
          if (map[key]) el.textContent = map[key];
        });
      }
    });
  });

  // ── Boot ──────────────────────────────────────────────────────────

  async function init() {
    if (!Store.isLoggedIn()) { showAuth(); return; }

    try {
      const meResult = await Api.getMe();

      if (meResult && meResult.blocked === true) {
        Store.set('blockedUserId', meResult.id);
        Store.set('blockedEmail',  meResult.email);
        showBlocked(meResult);
        return;
      }

      // Адмін → перекидаємо на admin.html
      if (meResult.role === 'ADMIN') {
        Store.setUser(meResult);
        window.location.href = 'admin.html';
        return;
      }

      Store.setUser(meResult);
      showApp();
    } catch {
      Store.clear();
      showAuth();
    }
  }

  return { showAuth, showApp, showBlocked, navigateTo, init };
})();

App.init();