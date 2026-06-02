/**
 * app.js — з повноцінною підтримкою I18n
 */
const App = (() => {

  function showAuth() {
    document.getElementById('auth-wrapper').classList.remove('hidden');
    document.getElementById('app-wrapper').classList.add('hidden');
    document.getElementById('page-login').classList.add('active');
    document.getElementById('page-register').classList.remove('active');
  }

  function showApp() {
    document.getElementById('auth-wrapper').classList.add('hidden');
    document.getElementById('app-wrapper').classList.remove('hidden');
    _updateSidebar();
    navigateTo('dashboard');
    AccountsPage.load();
  }

  function _updateSidebar() {
    const user = Store.getUser();
    if (!user) return;
    document.getElementById('sidebar-email').textContent  = user.email || '—';
    document.getElementById('sidebar-role').textContent   = user.role  || 'USER';
    document.getElementById('sidebar-avatar').textContent = (user.email || 'U')[0].toUpperCase();

    const adminLink = document.getElementById('nav-admin');
    if (adminLink) adminLink.style.display = user.role === 'ADMIN' ? 'flex' : 'none';
  }

  // ── Navigation ──────────────────────────────────────────────────────────────
  const PAGE_LOADERS = {
    dashboard:    () => DashboardPage.load(),
    accounts:     () => AccountsPage.load(),
    transfer:     () => {},
    transactions: () => TransactionsPage.load(),
    requests:     () => RequestsPage.load(),
    profile:      () => ProfilePage.load(),
  };

  // Ключі i18n для заголовків сторінок
  const PAGE_TITLE_KEYS = {
    dashboard:    'nav.dashboard',
    accounts:     'nav.accounts',
    transfer:     'nav.transfer',
    transactions: 'nav.transactions',
    requests:     'nav.requests',
    profile:      'nav.profile',
  };

  function navigateTo(pageId) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

    const page = document.getElementById(`page-${pageId}`);
    const nav  = document.querySelector(`[data-page="${pageId}"]`);
    if (page) page.classList.add('active');
    if (nav)  nav.classList.add('active');

    // Заголовок через I18n
    const titleEl = document.getElementById('page-title');
    if (titleEl) {
      const key = PAGE_TITLE_KEYS[pageId];
      titleEl.textContent = key ? I18n.t(key) : pageId;
      titleEl.dataset.i18nPage = pageId; // зберігаємо для re-render при зміні мови
    }

    const loader = PAGE_LOADERS[pageId];
    if (loader) loader();
  }

  document.querySelectorAll('.nav-item[data-page]').forEach(item => {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      navigateTo(item.dataset.page);
    });
  });

  // ── Mobile sidebar ──────────────────────────────────────────────────────────
  const burger  = document.getElementById('sidebar-toggle');
  const sidebar = document.querySelector('.sidebar');
  const overlay = document.getElementById('sidebar-overlay');

  function closeSidebar() {
    sidebar.classList.remove('open');
    overlay.classList.remove('visible');
    burger.classList.remove('open');
  }
  function toggleSidebar() {
    const isOpen = sidebar.classList.toggle('open');
    overlay.classList.toggle('visible', isOpen);
    burger.classList.toggle('open', isOpen);
  }
  burger.addEventListener('click', toggleSidebar);
  overlay.addEventListener('click', closeSidebar);

  document.querySelectorAll('.nav-item[data-page]').forEach(item => {
    item.addEventListener('click', closeSidebar);
  });
  const adminLink = document.getElementById('nav-admin');
  if (adminLink) adminLink.addEventListener('click', closeSidebar);

  // ── Logout ──────────────────────────────────────────────────────────────────
  document.getElementById('btn-logout').addEventListener('click', async () => {
    const rt = Store.get('refreshToken');
    try { if (rt) await Api.logout(rt); } catch {}
    Store.clear();
    showAuth();
    UI.toast(I18n.t('common.logout_toast'), 'info');
  });

  // ── Boot ────────────────────────────────────────────────────────────────────
  function init() {
    // Ініціалізуємо I18n першим — до будь-якого рендеру
    I18n.init();

    if (Store.isLoggedIn()) {
      Api.getMe()
        .then(user => { Store.setUser(user); showApp(); })
        .catch(() => { Store.clear(); showAuth(); });
    } else {
      showAuth();
    }
  }

  return { showAuth, showApp, navigateTo, init };
})();

App.init();