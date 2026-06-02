/**
 * i18n.js — Full Ukrainian / English translation system for Vault Banking.
 *
 * Usage in HTML: add data-i18n="key" to any element.
 *   <span data-i18n="nav.dashboard">Огляд</span>
 *
 * For placeholders:  data-i18n-placeholder="key"
 * For titles:        data-i18n-title="key"
 * For aria-labels:   data-i18n-aria="key"
 *
 * JS API:
 *   I18n.t('key')           — get translated string
 *   I18n.setLang('en'|'uk') — switch language & re-render
 *   I18n.getLang()          — current language
 *   I18n.onLangChange(fn)   — register callback called after each lang switch
 */

const I18n = (() => {

  const DICT = {
    uk: {
      // ── Brand ──────────────────────────────────────────────
      'brand.name':    'Vault',
      'brand.tagline': 'Private Banking Platform',

      // ── Auth ───────────────────────────────────────────────
      'auth.login.title':       'Вхід до системи',
      'auth.login.sub':         'Ласкаво просимо',
      'auth.login.email':       'Email',
      'auth.login.password':    'Пароль',
      'auth.login.btn':         'Увійти',
      'auth.login.no_account':  'Немає акаунту?',
      'auth.login.go_register': 'Зареєструватись',
      'auth.login.pw_placeholder': '••••••••',

      'auth.register.title':      'Реєстрація',
      'auth.register.sub':        'Створіть акаунт',
      'auth.register.first_name': "Ім'я",
      'auth.register.last_name':  'Прізвище',
      'auth.register.phone':      'Телефон',
      'auth.register.password':   'Пароль',
      'auth.register.btn':        'Зареєструватись',
      'auth.register.has_account':'Вже маєте акаунт?',
      'auth.register.go_login':   'Увійти',
      'auth.register.fn_ph':      'Іван',
      'auth.register.ln_ph':      'Петренко',
      'auth.register.pw_ph':      'мін. 8 символів',

      'auth.pwd.req.len':     'Мінімум 8 символів',
      'auth.pwd.req.upper':   'Велика літера (A–Z)',
      'auth.pwd.req.lower':   'Мала літера (a–z)',
      'auth.pwd.req.digit':   'Цифра (0–9)',
      'auth.pwd.req.special': 'Спецсимвол (!@#$%^&*…)',

      'auth.pwd.strength.1': 'Дуже слабкий',
      'auth.pwd.strength.2': 'Слабкий',
      'auth.pwd.strength.3': 'Задовільний',
      'auth.pwd.strength.4': 'Добрий',
      'auth.pwd.strength.5': 'Відмінний',

      // ── Navigation ─────────────────────────────────────────
      'nav.dashboard':    'Огляд',
      'nav.accounts':     'Рахунки',
      'nav.transfer':     'Переказ',
      'nav.transactions': 'Транзакції',
      'nav.requests':     'Запити',
      'nav.profile':      'Кабінет',
      'nav.admin':        'Адмін панель',

      // ── Dashboard ──────────────────────────────────────────
      'dash.total_balance':   'Загальний баланс',
      'dash.all_accounts':    'Всі рахунки',
      'dash.accounts_count':  'Рахунків',
      'dash.accounts_active': 'Активних',
      'dash.last_tx':         'Останній переказ',
      'dash.my_accounts':     'Мої рахунки',
      'dash.add':             '+ Додати',
      'dash.recent_tx':       'Останні транзакції',
      'dash.no_accounts':     'Рахунки не знайдено. Додайте перший рахунок.',
      'dash.no_tx':           'Транзакцій немає',

      // ── Accounts ───────────────────────────────────────────
      'acc.title':       'Банківські рахунки',
      'acc.new':         '+ Новий рахунок',
      'acc.not_found':   'Рахунки не знайдено',
      'acc.modal.title': 'Новий рахунок',
      'acc.modal.btn':   'Створити рахунок',
      'acc.modal.currency': 'Валюта',

      // ── Transfer ───────────────────────────────────────────
      'tf.title':    'Переказ коштів',
      'tf.sub':      'Миттєвий переказ між рахунками',
      'tf.from':     'З рахунку',
      'tf.to':       'Номер картки отримувача (16 цифр)',
      'tf.to_ph':    '1234 5678 9012 3456',
      'tf.amount':   'Сума',
      'tf.desc':     "Призначення (необов'язково)",
      'tf.desc_ph':  'За що переказ...',
      'tf.from_ph':  '— оберіть рахунок —',
      'tf.btn':      'Виконати переказ',

      // ── Transactions ───────────────────────────────────────
      'tx.title':     'Транзакції',
      'tx.col.date':  'Дата',
      'tx.col.id':    '№ ID',
      'tx.col.type':  'Тип',
      'tx.col.desc':  'Опис',
      'tx.col.status':'Статус',
      'tx.col.amount':'Сума',
      'tx.empty':     'Транзакцій немає',
      'tx.not_found': 'Транзакцій не знайдено',
      'tx.no_account':'Спочатку створіть рахунок',
      'tx.type.transfer_in':  'Надходження',
      'tx.type.transfer_out': 'Переказ',
      'tx.type.income':       'Надходження',
      'tx.filter.new':        '↓ Нові',
      'tx.filter.old':        '↑ Старі',
      'tx.filter.reset':      '✕ Скинути',
      'tx.summary.income':    '↓ Надходження',
      'tx.summary.outcome':   '↑ Витрати',
      'tx.summary.count':     'Транзакцій',

      // ── Requests ───────────────────────────────────────────
      'req.title':      'Мої запити',
      'req.new':        '+ Новий запит',
      'req.empty':      'Запитів немає. Натисніть "+ Новий запит".',
      'req.modal.title':'Новий запит',
      'req.modal.acc':  'Рахунок',
      'req.modal.type': 'Тип запиту',
      'req.modal.msg':  'Повідомлення',
      'req.modal.ph':   'Опишіть причину запиту...',
      'req.modal.btn':  'Надіслати запит',
      'req.modal.acc_ph': '— оберіть рахунок —',
      'req.type.unblock': 'Розблокування',

      // ── Profile ────────────────────────────────────────────
      'profile.title':       'Кабінет',
      'profile.edit':        '✎ Редагувати профіль',
      'profile.copy_id':     'Скопіювати ID',
      'profile.export_pdf':  '↓ Завантажити виписку PDF',
      'profile.personal':    'Особисті дані',
      'profile.first_name':  "Ім'я",
      'profile.last_name':   'Прізвище',
      'profile.email':       'Email',
      'profile.phone':       'Телефон',
      'profile.status':      'Статус',
      'profile.block_reason':'Причина блокування',
      'profile.role':        'Роль',
      'profile.registered':  'Реєстрація',
      'profile.stats':       'Статистика',
      'profile.accounts_count': 'Рахунків',
      'profile.active_count':   'Активних',
      'profile.tx_count':       'Транзакцій',
      'profile.security':    'Безпека',
      'profile.password':    'Пароль',
      'profile.pw_protected':'Захищено паролем',
      'profile.pw_change':   'Змінити',
      'profile.activity':    'Остання активність',
      'profile.save':        'Зберегти',
      'profile.cancel':      'Скасувати',
      'profile.bal_uah':     'Баланс UAH',
      'profile.bal_usd':     'Баланс USD',
      'profile.bal_eur':     'Баланс EUR',
      'req.type.block':      'Блокування',
      'req.type.limit_change': 'Зміна ліміту',
      'tx.tab.all':          '📋 Всі',
      'tx.filter.sort':      '📅 Сортування за датою',
      'tx.filter.search':    '🔍 Пошук за номером',

      'profile.pwd.current': 'Поточний пароль',
      'profile.pwd.new':     'Новий пароль',
      'profile.pwd.confirm': 'Підтвердження нового пароля',
      'profile.pwd.btn':     'Змінити пароль',
      'profile.pwd.req.diff':'Відрізняється від поточного',
      'profile.pwd.match':   '✓ Паролі збігаються',
      'profile.pwd.no_match':'✕ Паролі не збігаються',

      // ── Statuses ───────────────────────────────────────────
      'status.active':         'Активний',
      'status.blocked':        'Заблоковано',
      'status.pending':        'Очікує',
      'status.approved':       'Схвалено',
      'status.rejected':       'Відхилено',
      'status.pending_review': 'На розгляді',
      'status.success':        'Успішно',

      // ── Blocked page ───────────────────────────────────────
      'blocked.title':    'Акаунт заблоковано',
      'blocked.subtitle': 'Account suspended',
      'blocked.reason':   'Причина блокування',
      'blocked.no_reason':'Причину не вказано',
      'blocked.appeal':   'Оскаржити рішення',
      'blocked.hint':     'Якщо ви вважаєте блокування помилковим — опишіть ситуацію і адміністратор розгляне ваш запит.',
      'blocked.msg_label':'Повідомлення',
      'blocked.msg_ph':   'Поясніть, чому ваш акаунт слід розблокувати...',
      'blocked.btn':      'Надіслати запит на розблокування',
      'blocked.logout':   '← Вийти з акаунту',

      // ── Common ─────────────────────────────────────────────
      'common.logout':  'Вийти',
      'common.loading': 'Завантаження...',
      'common.error':   'Помилка',
      'common.success': 'Успішно',
      'common.close':   '✕',
      'common.confirm': 'Підтвердити',
      'common.role.user':  'USER',
      'common.role.admin': 'ADMIN',
      'common.logout_toast': 'Ви вийшли з системи',
    },

    en: {
      // ── Brand ──────────────────────────────────────────────
      'brand.name':    'Vault',
      'brand.tagline': 'Private Banking Platform',

      // ── Auth ───────────────────────────────────────────────
      'auth.login.title':       'Sign In',
      'auth.login.sub':         'Welcome back',
      'auth.login.email':       'Email',
      'auth.login.password':    'Password',
      'auth.login.btn':         'Sign In',
      'auth.login.no_account':  'No account?',
      'auth.login.go_register': 'Register',
      'auth.login.pw_placeholder': '••••••••',

      'auth.register.title':      'Register',
      'auth.register.sub':        'Create your account',
      'auth.register.first_name': 'First name',
      'auth.register.last_name':  'Last name',
      'auth.register.phone':      'Phone',
      'auth.register.password':   'Password',
      'auth.register.btn':        'Create Account',
      'auth.register.has_account':'Already have an account?',
      'auth.register.go_login':   'Sign In',
      'auth.register.fn_ph':      'John',
      'auth.register.ln_ph':      'Smith',
      'auth.register.pw_ph':      'min. 8 characters',

      'auth.pwd.req.len':     'At least 8 characters',
      'auth.pwd.req.upper':   'Uppercase letter (A–Z)',
      'auth.pwd.req.lower':   'Lowercase letter (a–z)',
      'auth.pwd.req.digit':   'Digit (0–9)',
      'auth.pwd.req.special': 'Special character (!@#$%^&*…)',

      'auth.pwd.strength.1': 'Very weak',
      'auth.pwd.strength.2': 'Weak',
      'auth.pwd.strength.3': 'Fair',
      'auth.pwd.strength.4': 'Good',
      'auth.pwd.strength.5': 'Strong',

      // ── Navigation ─────────────────────────────────────────
      'nav.dashboard':    'Overview',
      'nav.accounts':     'Accounts',
      'nav.transfer':     'Transfer',
      'nav.transactions': 'Transactions',
      'nav.requests':     'Requests',
      'nav.profile':      'Profile',
      'nav.admin':        'Admin Panel',

      // ── Dashboard ──────────────────────────────────────────
      'dash.total_balance':   'Total Balance',
      'dash.all_accounts':    'All Accounts',
      'dash.accounts_count':  'Accounts',
      'dash.accounts_active': 'Active',
      'dash.last_tx':         'Last Transfer',
      'dash.my_accounts':     'My Accounts',
      'dash.add':             '+ Add',
      'dash.recent_tx':       'Recent Transactions',
      'dash.no_accounts':     'No accounts found. Add your first account.',
      'dash.no_tx':           'No transactions',

      // ── Accounts ───────────────────────────────────────────
      'acc.title':       'Bank Accounts',
      'acc.new':         '+ New Account',
      'acc.not_found':   'No accounts found',
      'acc.modal.title': 'New Account',
      'acc.modal.btn':   'Create Account',
      'acc.modal.currency': 'Currency',

      // ── Transfer ───────────────────────────────────────────
      'tf.title':    'Transfer Funds',
      'tf.sub':      'Instant transfer between accounts',
      'tf.from':     'From account',
      'tf.to':       'Recipient card number (16 digits)',
      'tf.to_ph':    '1234 5678 9012 3456',
      'tf.amount':   'Amount',
      'tf.desc':     'Description (optional)',
      'tf.desc_ph':  'What is this transfer for...',
      'tf.from_ph':  '— select account —',
      'tf.btn':      'Send Transfer',

      // ── Transactions ───────────────────────────────────────
      'tx.title':     'Transactions',
      'tx.col.date':  'Date',
      'tx.col.id':    'ID',
      'tx.col.type':  'Type',
      'tx.col.desc':  'Description',
      'tx.col.status':'Status',
      'tx.col.amount':'Amount',
      'tx.empty':     'No transactions',
      'tx.not_found': 'No transactions found',
      'tx.no_account':'Create an account first',
      'tx.type.transfer_in':  'Incoming',
      'tx.type.transfer_out': 'Transfer',
      'tx.type.income':       'Income',
      'tx.filter.new':        '↓ Newest',
      'tx.filter.old':        '↑ Oldest',
      'tx.filter.reset':      '✕ Reset',
      'tx.summary.income':    '↓ Incoming',
      'tx.summary.outcome':   '↑ Outgoing',
      'tx.summary.count':     'Transactions',

      // ── Requests ───────────────────────────────────────────
      'req.title':      'My Requests',
      'req.new':        '+ New Request',
      'req.empty':      'No requests. Click "+ New Request".',
      'req.modal.title':'New Request',
      'req.modal.acc':  'Account',
      'req.modal.type': 'Request type',
      'req.modal.msg':  'Message',
      'req.modal.ph':   'Describe the reason for your request...',
      'req.modal.btn':  'Submit Request',
      'req.modal.acc_ph': '— select account —',
      'req.type.unblock': 'Unblock',

      // ── Profile ────────────────────────────────────────────
      'profile.title':       'Profile',
      'profile.edit':        '✎ Edit Profile',
      'profile.copy_id':     'Copy ID',
      'profile.export_pdf':  '↓ Download Statement PDF',
      'profile.personal':    'Personal Info',
      'profile.first_name':  'First name',
      'profile.last_name':   'Last name',
      'profile.email':       'Email',
      'profile.phone':       'Phone',
      'profile.status':      'Status',
      'profile.block_reason':'Block reason',
      'profile.role':        'Role',
      'profile.registered':  'Registered',
      'profile.stats':       'Statistics',
      'profile.accounts_count': 'Accounts',
      'profile.active_count':   'Active',
      'profile.tx_count':       'Transactions',
      'profile.security':    'Security',
      'profile.password':    'Password',
      'profile.pw_protected':'Protected by password',
      'profile.pw_change':   'Change',
      'profile.activity':    'Recent Activity',
      'profile.save':        'Save',
      'profile.cancel':      'Cancel',
      'profile.bal_uah':     'UAH Balance',
      'profile.bal_usd':     'USD Balance',
      'profile.bal_eur':     'EUR Balance',
      'req.type.block':      'Block',
      'req.type.limit_change': 'Limit Change',
      'tx.tab.all':          '📋 All',
      'tx.filter.sort':      '📅 Sort by date',
      'tx.filter.search':    '🔍 Search by ID',

      'profile.pwd.current': 'Current password',
      'profile.pwd.new':     'New password',
      'profile.pwd.confirm': 'Confirm new password',
      'profile.pwd.btn':     'Change Password',
      'profile.pwd.req.diff':'Different from current password',
      'profile.pwd.match':   '✓ Passwords match',
      'profile.pwd.no_match':'✕ Passwords do not match',

      // ── Statuses ───────────────────────────────────────────
      'status.active':         'Active',
      'status.blocked':        'Blocked',
      'status.pending':        'Pending',
      'status.approved':       'Approved',
      'status.rejected':       'Rejected',
      'status.pending_review': 'In Review',
      'status.success':        'Success',

      // ── Blocked page ───────────────────────────────────────
      'blocked.title':    'Account Blocked',
      'blocked.subtitle': 'Account suspended',
      'blocked.reason':   'Block reason',
      'blocked.no_reason':'No reason provided',
      'blocked.appeal':   'Appeal decision',
      'blocked.hint':     'If you believe the block is a mistake, describe the situation and an administrator will review your request.',
      'blocked.msg_label':'Message',
      'blocked.msg_ph':   'Explain why your account should be unblocked...',
      'blocked.btn':      'Submit Unblock Request',
      'blocked.logout':   '← Sign Out',

      // ── Common ─────────────────────────────────────────────
      'common.logout':  'Sign Out',
      'common.loading': 'Loading...',
      'common.error':   'Error',
      'common.success': 'Success',
      'common.close':   '✕',
      'common.confirm': 'Confirm',
      'common.role.user':  'USER',
      'common.role.admin': 'ADMIN',
      'common.logout_toast': 'You have been signed out',
    },
  };

  // ── Відкладена ініціалізація мови — Store може ще не існувати ──────────────
  let _lang = 'uk';
  const _callbacks = [];

  function _loadLang() {
    try {
      const saved = typeof Store !== 'undefined' ? Store.get('lang') : localStorage.getItem('vault_lang');
      if (saved && DICT[saved]) _lang = saved;
    } catch {}
  }

  function _saveLang(lang) {
    try {
      if (typeof Store !== 'undefined') Store.set('lang', lang);
      else localStorage.setItem('vault_lang', lang);
    } catch {}
  }

  function t(key) {
    return (DICT[_lang] && DICT[_lang][key]) || (DICT['uk'] && DICT['uk'][key]) || key;
  }

  function getLang() { return _lang; }

  function onLangChange(fn) { _callbacks.push(fn); }

  function setLang(lang) {
    if (!DICT[lang]) return;
    _lang = lang;
    _saveLang(lang);
    _apply();
    _updateLangButtons();
    // Повідомляємо всіх підписників (наприклад App.navigateTo для оновлення заголовка)
    _callbacks.forEach(fn => { try { fn(lang); } catch {} });
  }

  function _apply() {
    // data-i18n — текстовий контент
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.dataset.i18n;
      const val = t(key);
      if (val && val !== key) el.textContent = val;
    });

    // data-i18n-html — innerHTML (для тегів всередині)
    document.querySelectorAll('[data-i18n-html]').forEach(el => {
      const key = el.dataset.i18nHtml;
      const val = t(key);
      if (val && val !== key) el.innerHTML = val;
    });

    // data-i18n-placeholder — placeholder для input/textarea
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
      const key = el.dataset.i18nPlaceholder;
      const val = t(key);
      if (val && val !== key) el.placeholder = val;
    });

    // data-i18n-title — title attribute
    document.querySelectorAll('[data-i18n-title]').forEach(el => {
      const key = el.dataset.i18nTitle;
      const val = t(key);
      if (val && val !== key) el.title = val;
    });

    // data-i18n-aria — aria-label
    document.querySelectorAll('[data-i18n-aria]').forEach(el => {
      const key = el.dataset.i18nAria;
      const val = t(key);
      if (val && val !== key) el.setAttribute('aria-label', val);
    });

    // Оновлюємо заголовок активної сторінки (якщо навігація вже відбулась)
    const titleEl = document.getElementById('page-title');
    if (titleEl && titleEl.dataset.i18nPage) {
      const pageKeys = {
        dashboard: 'nav.dashboard', accounts: 'nav.accounts',
        transfer: 'nav.transfer', transactions: 'nav.transactions',
        requests: 'nav.requests', profile: 'nav.profile',
      };
      const key = pageKeys[titleEl.dataset.i18nPage];
      if (key) titleEl.textContent = t(key);
    }

    document.documentElement.lang = _lang;
  }

  function _updateLangButtons() {
    document.querySelectorAll('.lang-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.lang === _lang);
    });
  }

  // ── Ініціалізація: прив'язати кнопки та застосувати переклад ───────────────
  function init() {
    _loadLang();

    document.querySelectorAll('.lang-btn').forEach(btn => {

      const fresh = btn.cloneNode(true);
      btn.parentNode.replaceChild(fresh, btn);
      fresh.addEventListener('click', () => setLang(fresh.dataset.lang));
    });

    _apply();
    _updateLangButtons();
  }

  return { t, setLang, getLang, init, apply: _apply, onLangChange };
})();