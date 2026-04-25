const App = (() => {

  // ── Auth state ──────────────────────────────────────────────────────────────
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
    document.getElementById('sidebar-email').textContent = user.email || '—';
    document.getElementById('sidebar-role').textContent  = user.role || 'USER';
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
  };

  const PAGE_TITLES = {
    uk: {
      dashboard:    'Огляд',
      accounts:     'Рахунки',
      transfer:     'Переказ коштів',
      transactions: 'Транзакції',
      requests:     'Запити',
    },
    en: {
      dashboard:    'Overview',
      accounts:     'Accounts',
      transfer:     'Transfer Funds',
      transactions: 'Transactions',
      requests:     'Requests',
    },
  };

  let _currentPage = 'dashboard';

  function navigateTo(pageId) {
    _currentPage = pageId;
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

    const page = document.getElementById(`page-${pageId}`);
    const nav  = document.querySelector(`[data-page="${pageId}"]`);
    if (page) page.classList.add('active');
    if (nav)  nav.classList.add('active');

    document.getElementById('page-title').textContent =
      PAGE_TITLES[_lang][pageId] || pageId;

    const loader = PAGE_LOADERS[pageId];
    if (loader) loader();
  }

  document.querySelectorAll('.nav-item[data-page]').forEach(item => {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      navigateTo(item.dataset.page);
    });
  });

  // ── Mobile sidebar toggle ──────────────────────────────────────────────────
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

  // Logout
  document.getElementById('btn-logout').addEventListener('click', async () => {
    const rt = Store.get('refreshToken');
    try { if (rt) await Api.logout(rt); } catch {}
    Store.clear();
    showAuth();
    UI.toast(_lang === 'uk' ? 'Ви вийшли з системи' : 'You have logged out', 'info');
  });

  // ── Language system ─────────────────────────────────────────────────────────
  const TRANSLATIONS = {
    // Sidebar nav
    '[data-page="dashboard"] span':    { uk: 'Огляд',       en: 'Overview' },
    '[data-page="accounts"] span':     { uk: 'Рахунки',     en: 'Accounts' },
    '[data-page="transfer"] span':     { uk: 'Переказ',     en: 'Transfer' },
    '[data-page="transactions"] span': { uk: 'Транзакції',  en: 'Transactions' },
    '[data-page="requests"] span':     { uk: 'Запити',      en: 'Requests' },
    '#nav-admin span':                 { uk: 'Адмін панель',en: 'Admin Panel' },

    // Dashboard stat cards
    '#stats-grid .stat-card:nth-child(1) .stat-card__label': { uk: 'Загальний баланс',  en: 'Total Balance' },
    '#stats-grid .stat-card:nth-child(1) .stat-card__sub':   { uk: 'Всі рахунки',       en: 'All accounts' },
    '#stats-grid .stat-card:nth-child(2) .stat-card__label': { uk: 'Рахунків',          en: 'Accounts' },
    '#stats-grid .stat-card:nth-child(2) .stat-card__sub':   { uk: 'Активних',          en: 'Active' },
    '#stats-grid .stat-card:nth-child(3) .stat-card__label': { uk: 'Останній переказ',  en: 'Last Transfer' },

    // Dashboard section titles
    '#page-dashboard .section-title:nth-of-type(1)': { uk: 'Мої рахунки',          en: 'My Accounts' },
    '#page-dashboard .section-title:nth-of-type(2)': { uk: 'Останні транзакції',    en: 'Recent Transactions' },
    '#dash-add-account':                              { uk: '+ Додати',             en: '+ Add' },

    // Accounts page
    '#page-accounts .section-title':   { uk: 'Банківські рахунки', en: 'Bank Accounts' },
    '#btn-open-add-account':           { uk: '+ Новий рахунок',    en: '+ New Account' },

    // Transfer page
    '.transfer-card__title':           { uk: 'Переказ коштів',     en: 'Transfer Funds' },
    '.transfer-card__sub':             { uk: 'Миттєвий переказ між рахунками', en: 'Instant transfer between accounts' },
    'label[for="tf-from"]':            { uk: 'З рахунку / From',   en: 'From Account' },
    'label[for="tf-to"]':              { uk: 'Номер картки отримувача (16 цифр)', en: 'Recipient card number (16 digits)' },
    'label[for="tf-amount"]':          { uk: 'Сума / Amount',      en: 'Amount' },
    'label[for="tf-desc"]':            { uk: "Призначення (необов'язково)", en: 'Description (optional)' },
    '#form-transfer .btn__text':       { uk: 'Виконати переказ',   en: 'Execute Transfer' },

    // Transactions page
    '#page-transactions .section-title': { uk: 'Транзакції',       en: 'Transactions' },

    // Requests page
    '#page-requests .section-title':   { uk: 'Мої запити',         en: 'My Requests' },
    '#btn-open-add-request':           { uk: '+ Новий запит',      en: '+ New Request' },

    // Transaction table headers
    '#page-transactions .tx-table th:nth-child(1)': { uk: 'Дата',    en: 'Date' },
    '#page-transactions .tx-table th:nth-child(2)': { uk: 'Тип',     en: 'Type' },
    '#page-transactions .tx-table th:nth-child(3)': { uk: 'Опис',    en: 'Description' },
    '#page-transactions .tx-table th:nth-child(4)': { uk: 'Статус',  en: 'Status' },
    '#page-transactions .tx-table th:nth-child(5)': { uk: 'Сума',    en: 'Amount' },

    // Modal: Add account
    '#modal-add-account .modal__title':              { uk: 'Новий рахунок',     en: 'New Account' },
    'label[for="acc-currency"]':                     { uk: 'Валюта',            en: 'Currency' },
    'label[for="acc-balance"]':                      { uk: 'Початковий баланс', en: 'Initial Balance' },
    '#form-add-account .btn--primary':               { uk: 'Створити рахунок',  en: 'Create Account' },

    // Modal: Add request
    '#modal-add-request .modal__title':              { uk: 'Новий запит',       en: 'New Request' },
    'label[for="req-account"]':                      { uk: 'Рахунок',           en: 'Account' },
    'label[for="req-type"]':                         { uk: 'Тип запиту',        en: 'Request Type' },
    'label[for="req-message"]':                      { uk: 'Повідомлення',      en: 'Message' },
    '#form-add-request .btn--primary':               { uk: 'Надіслати запит',   en: 'Send Request' },
  };

  let _lang = 'uk';

  function _applyLang(lang) {
    Object.entries(TRANSLATIONS).forEach(([selector, texts]) => {
      try {
        document.querySelectorAll(selector).forEach(el => {
          // Для кнопок з loader-span всередині — міняємо тільки текстовий вміст
          if (el.querySelector('.btn__loader')) {
            const textNode = Array.from(el.childNodes)
              .find(n => n.nodeType === Node.TEXT_NODE && n.textContent.trim());
            if (textNode) textNode.textContent = texts[lang];
            else {
              const span = el.querySelector('.btn__text');
              if (span) span.textContent = texts[lang];
            }
          } else {
            el.textContent = texts[lang];
          }
        });
      } catch(e) {}
    });

    // Оновлюємо заголовок поточної сторінки
    document.getElementById('page-title').textContent =
      PAGE_TITLES[lang][_currentPage] || _currentPage;

    // Placeholder для поля переказу
    const tfTo = document.getElementById('tf-to');
    if (tfTo) tfTo.placeholder = lang === 'uk' ? '1234 5678 9012 3456' : '1234 5678 9012 3456';

    const tfDesc = document.getElementById('tf-desc');
    if (tfDesc) tfDesc.placeholder = lang === 'uk'
      ? 'За що переказ...'
      : 'Payment purpose...';

    const reqMsg = document.getElementById('req-message');
    if (reqMsg) reqMsg.placeholder = lang === 'uk'
      ? 'Опишіть причину запиту...'
      : 'Describe the reason...';

    const userSearch = document.getElementById('user-search');
    // userSearch може бути на сторінці адміна — пропускаємо
  }

  document.querySelectorAll('.lang-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      if (btn.dataset.lang === _lang) return;
      _lang = btn.dataset.lang;
      document.querySelectorAll('.lang-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      _applyLang(_lang);
    });
  });

  // ── Boot ────────────────────────────────────────────────────────────────────
  function init() {
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

// Boot
App.init();