const App = (() => {

  // ── Auth state ──────────────────────────────────────────────────────────────
  function showAuth() {
    document.getElementById('auth-wrapper').classList.remove('hidden');
    document.getElementById('app-wrapper').classList.add('hidden');
    document.getElementById('page-login').classList.add('active');
    document.getElementById('page-register').classList.remove('active');
  }

  function showApp() {
    const user = Store.getUser();
    if (!user) { showAuth(); return; }

    // Адміністратор не має доступу до банківського інтерфейсу —
    // його одразу перенаправляємо на окрему адмін-панель.
    if (user.role === 'ADMIN') {
      window.location.href = 'admin.html';
      return;
    }

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

    // Звичайний користувач ніколи не бачить посилання на адмін-панель
    const adminLink = document.getElementById('nav-admin');
    if (adminLink) adminLink.style.display = 'none';
  }

  // ── Navigation ──────────────────────────────────────────────────────────────
  const PAGE_LOADERS = {
    dashboard:    () => DashboardPage.load(),
    accounts:     () => AccountsPage.load(),
    transfer:     () => {},
    transactions: () => TransactionsPage.load(),
    requests:     () => RequestsPage.load(),
  };

  const PAGE_TITLES = {
    dashboard:    'Огляд',
    accounts:     'Рахунки',
    transfer:     'Переказ коштів',
    transactions: 'Транзакції',
    requests:     'Запити',
  };

  function navigateTo(pageId) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

    const page = document.getElementById(`page-${pageId}`);
    const nav  = document.querySelector(`[data-page="${pageId}"]`);
    if (page) page.classList.add('active');
    if (nav)  nav.classList.add('active');

    document.getElementById('page-title').textContent = PAGE_TITLES[pageId] || pageId;

    const loader = PAGE_LOADERS[pageId];
    if (loader) loader();
  }

  document.querySelectorAll('.nav-item[data-page]').forEach(item => {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      navigateTo(item.dataset.page);
    });
  });

  // ── Mobile sidebar ─────────────────────────────────────────────────────────
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

  // ── Logout ─────────────────────────────────────────────────────────────────
  document.getElementById('btn-logout').addEventListener('click', async () => {
    const rt = Store.get('refreshToken');
    try {
      if (rt) await Api.logout(rt);
    } catch {}
    Store.clear();
    showAuth();
    UI.toast('Ви вийшли з системи', 'info');
  });

  // ── Language toggle ────────────────────────────────────────────────────────
  const TRANSLATIONS = {
    en: {
      'Огляд':            'Overview',
      'Рахунки':          'Accounts',
      'Переказ':          'Transfer',
      'Транзакції':       'Transactions',
      'Запити':           'Requests',
      'Загальний баланс': 'Total Balance',
      'Всі рахунки':      'All Accounts',
      'Останній переказ': 'Last Transfer',
      'Переказ коштів':   'Transfer Funds',
      'Мої запити':       'My Requests',
    },
    uk: {},
  };

  let _lang = 'uk';

  document.querySelectorAll('.lang-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      _lang = btn.dataset.lang;
      document.querySelectorAll('.lang-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      _applyLang(_lang);
    });
  });

  function _applyLang(lang) {
    if (lang === 'uk') return;
    const map = TRANSLATIONS[lang] || {};
    document.querySelectorAll('.stat-card__label, .section-title, .nav-item span, .topbar__title').forEach(el => {
      const uk = el.textContent.trim();
      if (map[uk]) el.textContent = map[uk];
    });
  }

  // ── Boot ────────────────────────────────────────────────────────────────────
  function init() {
    if (Store.isLoggedIn()) {
      Api.getMe()
        .then(user => {
          Store.setUser(user);
          // Якщо адмін відкрив index.html — одразу редирект
          showApp();
        })
        .catch(() => {
          Store.clear();
          showAuth();
        });
    } else {
      showAuth();
    }
  }

  return { showAuth, showApp, navigateTo, init };
})();

App.init();
