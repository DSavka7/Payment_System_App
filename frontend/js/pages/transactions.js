
const TransactionsPage = (() => {
  const LIMIT = 30;
  let _accounts    = [];
  let _activeAccId = 'all';
  let _offset      = 0;
  let _total       = 0;

  // ── Головна точка входу ───────────────────────────────────────────────────
  async function load() {
    _accounts    = AccountsPage.getAccounts();
    _activeAccId = 'all';
    _offset      = 0;

    _buildTabs();

    if (_accounts.length === 0) {
      _showEmpty('Спочатку створіть рахунок');
      return;
    }

    await _loadTab('all');
  }

  // ── Таби ──────────────────────────────────────────────────────────────────
  function _buildTabs() {
    // Видалити старі таби
    const old = document.getElementById('tx-tab-bar');
    if (old) old.remove();

    const tabBar = document.createElement('div');
    tabBar.id = 'tx-tab-bar';
    tabBar.className = 'tx-tab-bar';

    tabBar.appendChild(_makeTab('all', '📋 Всі'));

    _accounts.forEach(acc => {
      const sym   = { UAH: '₴', USD: '$', EUR: '€' }[acc.currency] || '';
      const last4 = acc.card_number ? acc.card_number.replace(/\s/g, '').slice(-4) : '????';
      tabBar.appendChild(_makeTab(acc.id, `${sym} ···${last4}`));
    });

    // Вставити перед таблицею
    const section = document.getElementById('page-transactions');
    const tableWrap = section.querySelector('.tx-table-wrap');
    section.insertBefore(tabBar, tableWrap);
  }

  function _makeTab(accId, label) {
    const btn = document.createElement('button');
    btn.className = `tx-tab${accId === _activeAccId ? ' tx-tab--active' : ''}`;
    btn.dataset.accId = accId;
    btn.textContent = label;
    btn.addEventListener('click', () => _loadTab(accId, 0));
    return btn;
  }

  function _setActiveTab(accId) {
    _activeAccId = accId;
    document.querySelectorAll('.tx-tab').forEach(b =>
      b.classList.toggle('tx-tab--active', b.dataset.accId === accId)
    );
  }

  // ── Завантаження ──────────────────────────────────────────────────────────
  async function _loadTab(accId, offset = 0) {
    _setActiveTab(accId);
    _offset = offset;
    _showLoading();
    _removeSummary();

    try {
      if (accId === 'all') {
        await _loadAll();
      } else {
        await _loadOne(accId, offset);
      }
    } catch (err) {
      _showEmpty('Помилка завантаження: ' + err.message);
      console.error(err);
    }
  }

  // Всі транзакції по всіх рахунках
  async function _loadAll() {
    if (_accounts.length === 0) {
      _showEmpty('Немає рахунків');
      return;
    }

    const results = await Promise.allSettled(
      _accounts.map(acc => Api.getAccountTx(acc.id, 100, 0))
    );

    // Збираємо унікальні транзакції
    const seen = new Set();
    const all  = [];
    results.forEach(r => {
      if (r.status === 'fulfilled') {
        (r.value.items || []).forEach(tx => {
          if (!seen.has(tx.id)) { seen.add(tx.id); all.push(tx); }
        });
      }
    });

    all.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    _total = all.length;

    // Рахуємо summary для всіх рахунків
    let income = 0, outcome = 0;
    _accounts.forEach(acc => {
      all.forEach(tx => {
        if (tx.to_account_id   === acc.id) income  += tx.amount;
        if (tx.from_account_id === acc.id) outcome += tx.amount;
      });
    });

    _insertSummary(income, outcome, all.length, 'UAH');
    _renderRows(all, null);
    _clearPagination();
  }

  // Транзакції одного рахунку
  async function _loadOne(accId, offset) {
    const { items, total } = await Api.getAccountTx(accId, LIMIT, offset);
    _total = total;

    const acc = _accounts.find(a => a.id === accId);
    const currency = acc ? acc.currency : 'UAH';

    // Рахуємо: to_account_id === accId → надходження, from_account_id === accId → витрати
    let income = 0, outcome = 0;
    (items || []).forEach(tx => {
      if (tx.to_account_id   === accId) income  += tx.amount;
      if (tx.from_account_id === accId) outcome += tx.amount;
    });

    _insertSummary(income, outcome, total, currency);
    _renderRows(items || [], accId);
    _renderPagination(accId);
  }

  // ── Summary ───────────────────────────────────────────────────────────────
  function _removeSummary() {
    const old = document.getElementById('tx-summary');
    if (old) old.remove();
  }

  function _insertSummary(income, outcome, count, currency) {
    _removeSummary();

    const div = document.createElement('div');
    div.id = 'tx-summary';
    div.className = 'tx-summary';
    div.innerHTML = `
      <div class="tx-summary__card tx-summary__card--income">
        <div class="tx-summary__label">↓ Надходження</div>
        <div class="tx-summary__value">+${UI.formatMoney(income, currency)}</div>
      </div>
      <div class="tx-summary__card tx-summary__card--outcome">
        <div class="tx-summary__label">↑ Витрати</div>
        <div class="tx-summary__value">−${UI.formatMoney(outcome, currency)}</div>
      </div>
      <div class="tx-summary__card">
        <div class="tx-summary__label">Транзакцій</div>
        <div class="tx-summary__value">${count}</div>
      </div>
    `;

    // Вставити перед tx-table-wrap
    const section   = document.getElementById('page-transactions');
    const tableWrap = section.querySelector('.tx-table-wrap');
    section.insertBefore(div, tableWrap);
  }

  // ── Рядки таблиці ─────────────────────────────────────────────────────────
  function _renderRows(items, myAccId) {
    const tbody = document.getElementById('tx-table-body');
    if (!tbody) return;

    if (!items || items.length === 0) {
      tbody.innerHTML = '<tr><td colspan="5" class="empty-state">Транзакцій немає</td></tr>';
      return;
    }

    tbody.innerHTML = '';
    items.forEach(tx => {
      let isIncome;
      if (myAccId) {
        isIncome = tx.to_account_id === myAccId;
      } else {
        // На вкладці "всі": якщо транзакція між своїми рахунками — показуємо як витрату
        const myIds = _accounts.map(a => a.id);
        isIncome = myIds.includes(tx.to_account_id) && !myIds.includes(tx.from_account_id);
      }

      const amountClass = isIncome ? 'tx-amount--in' : 'tx-amount--out';
      const amountSign  = isIncome ? '+' : '−';

      // Скорочений ID контрагента
      let counterpart = '';
      if (myAccId) {
        const otherId = isIncome ? tx.from_account_id : tx.to_account_id;
        counterpart = otherId ? `${isIncome ? '← від' : '→ до'} ···${otherId.slice(-6)}` : '';
      }

      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td class="tx-date-cell">${UI.formatDate(tx.created_at)}</td>
        <td>${UI.typeLabel(tx.type)}</td>
        <td>
          <div style="font-size:.85rem;color:var(--mist);max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">
            ${tx.description || tx.category || UI.typeLabel(tx.type)}
          </div>
          ${counterpart ? `<div style="font-size:.7rem;color:var(--silver);font-family:var(--font-mono)">${counterpart}</div>` : ''}
        </td>
        <td>${UI.statusBadge(tx.status)}</td>
        <td class="text-right ${amountClass}" style="font-family:var(--font-mono);font-weight:500;white-space:nowrap">
          ${amountSign}${UI.formatMoney(tx.amount, tx.currency)}
        </td>
      `;
      tbody.appendChild(tr);
    });
  }

  // ── Пагінація ─────────────────────────────────────────────────────────────
  function _clearPagination() {
    const pg = document.getElementById('tx-pagination');
    if (pg) pg.innerHTML = '';
  }

  function _renderPagination(accId) {
    const pg = document.getElementById('tx-pagination');
    if (!pg) return;
    pg.innerHTML = '';
    if (_total <= LIMIT) return;

    const totalPages = Math.ceil(_total / LIMIT);
    const curPage    = Math.floor(_offset / LIMIT);

    const prev = document.createElement('button');
    prev.className = 'page-btn';
    prev.textContent = '←';
    prev.disabled = curPage === 0;
    prev.onclick = () => _loadTab(accId, (curPage - 1) * LIMIT);
    pg.appendChild(prev);

    const maxBtns = Math.min(totalPages, 7);
    for (let i = 0; i < maxBtns; i++) {
      const btn = document.createElement('button');
      btn.className = `page-btn${i === curPage ? ' active' : ''}`;
      btn.textContent = i + 1;
      btn.onclick = () => _loadTab(accId, i * LIMIT);
      pg.appendChild(btn);
    }

    const next = document.createElement('button');
    next.className = 'page-btn';
    next.textContent = '→';
    next.disabled = curPage >= totalPages - 1;
    next.onclick = () => _loadTab(accId, (curPage + 1) * LIMIT);
    pg.appendChild(next);
  }

  // ── Helpers ───────────────────────────────────────────────────────────────
  function _showLoading() {
    const tbody = document.getElementById('tx-table-body');
    if (tbody) tbody.innerHTML =
      `<tr><td colspan="5"><div class="skeleton" style="height:50px;margin:8px 0;border-radius:6px"></div></td></tr>`.repeat(4);
  }

  function _showEmpty(msg) {
    const tbody = document.getElementById('tx-table-body');
    if (tbody) tbody.innerHTML = `<tr><td colspan="5" class="empty-state">${msg}</td></tr>`;
  }

  return { load };
})();