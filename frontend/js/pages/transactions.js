const TransactionsPage = (() => {
  const LIMIT = 30;
  let _accounts    = [];
  let _activeAccId = 'all';
  let _offset      = 0;
  let _total       = 0;

  let _filterIdQuery = '';
  let _sortOrder     = 'desc';
  let _allTxCache    = [];

  async function load() {
    _accounts    = AccountsPage.getAccounts();
    _activeAccId = 'all';
    _offset      = 0;

    _buildTabs();
    _buildFilterBar();

    if (_accounts.length === 0) {
      _showEmpty(I18n.t('tx.no_account'));
      return;
    }

    await _loadTab('all');
  }

  // --- Filter bar ---

  function _buildFilterBar() {
    const old = document.getElementById('tx-filter-bar');
    if (old) old.remove();

    const bar = document.createElement('div');
    bar.id = 'tx-filter-bar';
    bar.className = 'tx-filter-bar';
    bar.innerHTML = `
      <div class="tx-filter-group">
        <label class="tx-filter-label">${I18n.t('tx.filter.search')}</label>
        <input
          class="field__input tx-filter-input"
          id="tx-search-id"
          type="text"
          placeholder="${I18n.t('tx.filter.search_ph')}"
          value="${_filterIdQuery}"
        />
      </div>
      <div class="tx-filter-group">
        <label class="tx-filter-label">${I18n.t('tx.filter.sort')}</label>
        <div class="tx-sort-btns">
          <button class="tx-sort-btn${_sortOrder === 'desc' ? ' tx-sort-btn--active' : ''}" data-order="desc">${I18n.t('tx.filter.new')}</button>
          <button class="tx-sort-btn${_sortOrder === 'asc'  ? ' tx-sort-btn--active' : ''}" data-order="asc">${I18n.t('tx.filter.old')}</button>
        </div>
      </div>
      <div style="margin-left:auto;display:flex;align-items:flex-end;gap:8px">
        <button class="tx-filter-reset btn btn--outline btn--sm" id="tx-filter-reset">${I18n.t('tx.filter.reset')}</button>
      </div>
    `;

    const section = document.getElementById('page-transactions');
    const tabBar  = document.getElementById('tx-tab-bar');
    const ref = tabBar || section.querySelector('.tx-table-wrap');
    section.insertBefore(bar, ref);

    let _searchTimer;
    document.getElementById('tx-search-id').addEventListener('input', (e) => {
      clearTimeout(_searchTimer);
      _searchTimer = setTimeout(() => {
        _filterIdQuery = e.target.value.trim().toLowerCase();
        _applyClientFilters();
      }, 250);
    });

    bar.querySelectorAll('.tx-sort-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        _sortOrder = btn.dataset.order;
        bar.querySelectorAll('.tx-sort-btn').forEach(b => b.classList.remove('tx-sort-btn--active'));
        btn.classList.add('tx-sort-btn--active');
        _applyClientFilters();
      });
    });

    document.getElementById('tx-filter-reset').addEventListener('click', () => {
      _filterIdQuery = '';
      _sortOrder = 'desc';
      document.getElementById('tx-search-id').value = '';
      bar.querySelectorAll('.tx-sort-btn').forEach(b => {
        b.classList.toggle('tx-sort-btn--active', b.dataset.order === 'desc');
      });
      _applyClientFilters();
    });

  }

  function _getVisibleTransactions() {
    let result = [..._allTxCache];
    if (_filterIdQuery) {
      result = result.filter(tx => tx.id && tx.id.toLowerCase().includes(_filterIdQuery));
    }
    result.sort((a, b) => {
      const da = new Date(a.created_at), db = new Date(b.created_at);
      return _sortOrder === 'asc' ? da - db : db - da;
    });
    return result;
  }

  function _applyClientFilters() {
    let filtered = [..._allTxCache];
    if (_filterIdQuery) {
      filtered = filtered.filter(tx => tx.id && tx.id.toLowerCase().includes(_filterIdQuery));
    }
    filtered.sort((a, b) => {
      const da = new Date(a.created_at), db = new Date(b.created_at);
      return _sortOrder === 'asc' ? da - db : db - da;
    });
    const myAccId = _activeAccId === 'all' ? null : _activeAccId;
    _renderRows(filtered, myAccId);
    _updateFilterStatus(filtered.length, _allTxCache.length);
  }

  function _updateFilterStatus(shown, total) {
    let statusEl = document.getElementById('tx-filter-status');
    if (!statusEl) {
      statusEl = document.createElement('div');
      statusEl.id = 'tx-filter-status';
      statusEl.className = 'tx-filter-status';
      const tableWrap = document.querySelector('#page-transactions .tx-table-wrap');
      if (tableWrap) tableWrap.parentNode.insertBefore(statusEl, tableWrap);
    }
    statusEl.style.display = shown < total ? 'block' : 'none';
    if (shown < total) statusEl.textContent = `Показано ${shown} з ${total} транзакцій`;
  }

  // --- Tabs ---

  function _buildTabs() {
    const old = document.getElementById('tx-tab-bar');
    if (old) old.remove();

    const tabBar = document.createElement('div');
    tabBar.id = 'tx-tab-bar';
    tabBar.className = 'tx-tab-bar';

    tabBar.appendChild(_makeTab('all', I18n.t('tx.tab.all')));
    _accounts.forEach(acc => {
      const sym   = { UAH: '₴', USD: '$', EUR: '€' }[acc.currency] || '';
      const last4 = acc.card_number ? acc.card_number.replace(/\s/g, '').slice(-4) : '????';
      tabBar.appendChild(_makeTab(acc.id, `${sym} ···${last4}`));
    });

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

  // --- Load data ---

  async function _loadTab(accId, offset = 0) {
    _setActiveTab(accId);
    _offset = offset;
    _showLoading();
    _removeSummary();

    _filterIdQuery = '';
    const searchInput = document.getElementById('tx-search-id');
    if (searchInput) searchInput.value = '';

    try {
      if (accId === 'all') await _loadAll();
      else await _loadOne(accId, offset);
    } catch (err) {
      _showEmpty(I18n.t('common.error') + ': ' + err.message);
    }
  }

  async function _loadAll() {
    if (_accounts.length === 0) { _showEmpty(I18n.t('tx.no_account')); return; }

    const results = await Promise.allSettled(
      _accounts.map(acc => Api.getAccountTx(acc.id, 100, 0))
    );

    const seen = new Set(), all = [];
    results.forEach(r => {
      if (r.status === 'fulfilled') {
        (r.value.items || []).forEach(tx => {
          if (!seen.has(tx.id)) { seen.add(tx.id); all.push(tx); }
        });
      }
    });

    _allTxCache = all;
    _total = all.length;

    // Calculate income/outcome across all accounts
    const myIds = _accounts.map(a => a.id);
    let income = 0, outcome = 0;
    all.forEach(tx => {
      if (myIds.includes(tx.to_account_id) && !myIds.includes(tx.from_account_id)) income += tx.amount;
      if (myIds.includes(tx.from_account_id)) outcome += tx.amount;
    });

    _insertSummary(income, outcome, all.length, 'UAH');
    _applyClientFilters();
    _clearPagination();
  }

  async function _loadOne(accId, offset) {
    const { items, total } = await Api.getAccountTx(accId, LIMIT, offset);
    _total = total;

    const acc = _accounts.find(a => a.id === accId);
    const currency = acc ? acc.currency : 'UAH';

    let income = 0, outcome = 0;
    (items || []).forEach(tx => {
      if (tx.to_account_id   === accId) income  += tx.amount;
      if (tx.from_account_id === accId) outcome += tx.amount;
    });

    _allTxCache = items || [];
    _insertSummary(income, outcome, total, currency);
    _applyClientFilters();
    _renderPagination(accId);
  }

  // --- Summary ---

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
        <div class="tx-summary__label">${I18n.t('tx.summary.income')}</div>
        <div class="tx-summary__value">+${UI.formatMoney(income, currency)}</div>
      </div>
      <div class="tx-summary__card tx-summary__card--outcome">
        <div class="tx-summary__label">${I18n.t('tx.summary.outcome')}</div>
        <div class="tx-summary__value">−${UI.formatMoney(outcome, currency)}</div>
      </div>
      <div class="tx-summary__card">
        <div class="tx-summary__label">${I18n.t('tx.summary.count')}</div>
        <div class="tx-summary__value">${count}</div>
      </div>
    `;
    const section   = document.getElementById('page-transactions');
    const tableWrap = section.querySelector('.tx-table-wrap');
    section.insertBefore(div, tableWrap);
  }

  // --- Table rows ---

  function _renderRows(items, myAccId) {
    const tbody = document.getElementById('tx-table-body');
    if (!tbody) return;

    if (!items || items.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" class="empty-state">${I18n.t('tx.not_found')}</td></tr>`;
      return;
    }

    const myIds = _accounts.map(a => a.id);

    tbody.innerHTML = '';
    items.forEach(tx => {
      // Determine direction: income = money coming IN to my account(s)
      let isIncome;
      if (myAccId) {
        isIncome = tx.to_account_id === myAccId;
      } else {
        isIncome = myIds.includes(tx.to_account_id) && !myIds.includes(tx.from_account_id);
      }

      // Type label: show "Надходження" for incoming, "Переказ" for outgoing transfers
      const typeLabel = UI.typeLabelDirectional(tx.type, isIncome);

      const amountClass = isIncome ? 'tx-amount--in' : 'tx-amount--out';
      const amountSign  = isIncome ? '+' : '−';

      let counterpart = '';
      if (myAccId) {
        const otherId = isIncome ? tx.from_account_id : tx.to_account_id;
        counterpart = otherId ? `${isIncome ? '←' : '→'} ···${otherId.slice(-6)}` : '';
      }

      const shortId = tx.id ? tx.id.slice(-8) : '—';

      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td class="tx-date-cell">${UI.formatDate(tx.created_at)}</td>
        <td><span class="tx-id-badge" title="${tx.id || ''}">#${shortId}</span></td>
        <td>${typeLabel}</td>
        <td>
          <div style="font-size:.85rem;color:var(--mist);max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">
            ${tx.description || tx.category || typeLabel}
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

  // --- Pagination ---

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

  // --- Helpers ---

  function _showLoading() {
    const tbody = document.getElementById('tx-table-body');
    if (tbody) tbody.innerHTML =
      `<tr><td colspan="6"><div class="skeleton" style="height:50px;margin:8px 0;border-radius:6px"></div></td></tr>`.repeat(4);
  }

  function _showEmpty(msg) {
    const tbody = document.getElementById('tx-table-body');
    if (tbody) tbody.innerHTML = `<tr><td colspan="6" class="empty-state">${msg}</td></tr>`;
  }

  // Re-render filter bar labels on language change
  if (typeof I18n !== 'undefined') {
    I18n.onLangChange(() => {
      const bar = document.getElementById('tx-filter-bar');
      if (!bar) return;
      const searchLabel = bar.querySelector('.tx-filter-label');
      const sortLabel   = bar.querySelectorAll('.tx-filter-label')[1];
      const [btnDesc, btnAsc] = bar.querySelectorAll('.tx-sort-btn');
      const resetBtn = document.getElementById('tx-filter-reset');
      const searchInput = document.getElementById('tx-search-id');
      if (searchLabel) searchLabel.textContent = I18n.t('tx.filter.search');
      if (sortLabel)   sortLabel.textContent   = I18n.t('tx.filter.sort');
      if (btnDesc)     btnDesc.textContent      = I18n.t('tx.filter.new');
      if (btnAsc)      btnAsc.textContent       = I18n.t('tx.filter.old');
      if (resetBtn)    resetBtn.textContent     = I18n.t('tx.filter.reset');
      if (searchInput) searchInput.placeholder  = I18n.t('tx.filter.search_ph');

      // Re-render summary labels
      const summaryLabels = document.querySelectorAll('#tx-summary .tx-summary__label');
      if (summaryLabels[0]) summaryLabels[0].textContent = I18n.t('tx.summary.income');
      if (summaryLabels[1]) summaryLabels[1].textContent = I18n.t('tx.summary.outcome');
      if (summaryLabels[2]) summaryLabels[2].textContent = I18n.t('tx.summary.count');

      // Re-render tab "All" label
      const allTab = document.querySelector('.tx-tab[data-acc-id="all"]');
      if (allTab) allTab.textContent = I18n.t('tx.tab.all');

      // Re-render table rows (statusBadge + typeLabel depend on lang)
      _applyClientFilters();
    });
  }

  return { load };
})();