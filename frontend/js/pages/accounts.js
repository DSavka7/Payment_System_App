const AccountsPage = (() => {

    let _accounts = [];
    let _filtered = [];

    // ── Стан фільтрів ─────────────────────────────────────────────────────
    let _filterCardQuery = '';
    let _filterCurrency  = '';
    let _filterStatus    = '';  // '' | 'active' | 'blocked'
    let _sortBy          = '';  // '' | 'card_asc' | 'card_desc' | 'balance_asc' | 'balance_desc'

    function generateCardNumber() {
        const seg = () => String(Math.floor(1000 + Math.random() * 9000));
        return seg() + seg() + seg() + seg();
    }

    function formatDisplay(num16) {
        return num16.replace(/(\d{4})(\d{4})(\d{4})(\d{4})/, '$1 $2 $3 $4');
    }

    function setCardNumber(num16) {
        const input = document.getElementById('acc-card');
        if (input) {
            input.value = formatDisplay(num16);
            input.dataset.full = num16;
        }
    }

    // ── Завантаження ──────────────────────────────────────────────────────
    async function load() {
        const user = Store.getUser();
        if (!user) return;

        const grid = document.getElementById('accounts-grid');
        grid.innerHTML = '<div class="empty-state skeleton" style="height:160px;border-radius:12px"></div>';

        try {
            _accounts = await Api.getUserAccounts(user.id);
            _filtered = [..._accounts];
            _buildFilterBar();
            _applyFilters();
            _populateSelects(_accounts);
        } catch (err) {
            grid.innerHTML = `<div class="empty-state">Помилка: ${err.message}</div>`;
        }
    }

    // ── Панель фільтрів ───────────────────────────────────────────────────
    function _buildFilterBar() {
        const old = document.getElementById('acc-filter-bar');
        if (old) old.remove();

        const bar = document.createElement('div');
        bar.id = 'acc-filter-bar';
        bar.className = 'acc-filter-bar';
        bar.innerHTML = `
          <div class="acc-filter-group">
            <label class="tx-filter-label">🔍 Пошук за номером картки</label>
            <input
              class="field__input tx-filter-input"
              id="acc-search-card"
              type="text"
              placeholder="Наприклад: 1234 або ****5678"
              value="${_filterCardQuery}"
            />
          </div>
          <div class="acc-filter-group">
            <label class="tx-filter-label">💱 Валюта рахунку</label>
            <div class="acc-currency-btns">
              <button class="tx-sort-btn${_filterCurrency === '' ? ' tx-sort-btn--active' : ''}" data-currency="">Всі</button>
              <button class="tx-sort-btn${_filterCurrency === 'UAH' ? ' tx-sort-btn--active' : ''}" data-currency="UAH">₴ UAH</button>
              <button class="tx-sort-btn${_filterCurrency === 'USD' ? ' tx-sort-btn--active' : ''}" data-currency="USD">$ USD</button>
              <button class="tx-sort-btn${_filterCurrency === 'EUR' ? ' tx-sort-btn--active' : ''}" data-currency="EUR">€ EUR</button>
            </div>
          </div>
          <div class="acc-filter-group">
            <label class="tx-filter-label">📊 Сортування</label>
            <select class="field__input field__select field__select--sm" id="acc-sort-select" style="width:auto">
              <option value="">— оберіть —</option>
              <optgroup label="За номером картки">
                <option value="card_asc"  ${_sortBy === 'card_asc'     ? 'selected' : ''}>Номер: А → Я</option>
                <option value="card_desc" ${_sortBy === 'card_desc'    ? 'selected' : ''}>Номер: Я → А</option>
              </optgroup>
              <optgroup label="За залишком коштів">
                <option value="balance_asc"  ${_sortBy === 'balance_asc'  ? 'selected' : ''}>Залишок: ↑ зростання</option>
                <option value="balance_desc" ${_sortBy === 'balance_desc' ? 'selected' : ''}>Залишок: ↓ спадання</option>
              </optgroup>
            </select>
          </div>
          <div class="acc-filter-group">
            <label class="tx-filter-label">🔒 Стан рахунку</label>
            <div class="acc-currency-btns">
              <button class="tx-sort-btn${_filterStatus === '' ? ' tx-sort-btn--active' : ''}" data-status="">Всі</button>
              <button class="tx-sort-btn acc-status-btn--active${_filterStatus === 'active' ? ' tx-sort-btn--active' : ''}" data-status="active">● Активні</button>
              <button class="tx-sort-btn acc-status-btn--blocked${_filterStatus === 'blocked' ? ' tx-sort-btn--active' : ''}" data-status="blocked">○ Заблоковані</button>
            </div>
          </div>
          <button class="tx-filter-reset btn btn--outline btn--sm" id="acc-filter-reset">✕ Скинути</button>
        `;

        // Вставити ПЕРЕД сіткою рахунків
        const section = document.getElementById('page-accounts');
        const grid    = document.getElementById('accounts-grid');
        section.insertBefore(bar, grid);

        // ── Events ──────────────────────────────────────────────────────

        // Пошук за номером
        let _timer;
        document.getElementById('acc-search-card').addEventListener('input', (e) => {
            clearTimeout(_timer);
            _timer = setTimeout(() => {
                _filterCardQuery = e.target.value.trim().toLowerCase().replace(/\s/g, '');
                _applyFilters();
            }, 250);
        });

        // Фільтр валюти
        bar.querySelectorAll('[data-currency]').forEach(btn => {
            btn.addEventListener('click', () => {
                _filterCurrency = btn.dataset.currency;
                bar.querySelectorAll('[data-currency]').forEach(b => b.classList.remove('tx-sort-btn--active'));
                btn.classList.add('tx-sort-btn--active');
                _applyFilters();
            });
        });

        // Фільтр стану рахунку
        bar.querySelectorAll('[data-status]').forEach(btn => {
            btn.addEventListener('click', () => {
                _filterStatus = btn.dataset.status;
                bar.querySelectorAll('[data-status]').forEach(b => b.classList.remove('tx-sort-btn--active'));
                btn.classList.add('tx-sort-btn--active');
                _applyFilters();
            });
        });

        // Сортування
        document.getElementById('acc-sort-select').addEventListener('change', (e) => {
            _sortBy = e.target.value;
            _applyFilters();
        });

        // Скидання
        document.getElementById('acc-filter-reset').addEventListener('click', () => {
            _filterCardQuery = '';
            _filterCurrency  = '';
            _filterStatus    = '';
            _sortBy          = '';
            document.getElementById('acc-search-card').value = '';
            document.getElementById('acc-sort-select').value = '';
            bar.querySelectorAll('[data-currency]').forEach(b =>
                b.classList.toggle('tx-sort-btn--active', b.dataset.currency === '')
            );
            bar.querySelectorAll('[data-status]').forEach(b =>
                b.classList.toggle('tx-sort-btn--active', b.dataset.status === '')
            );
            _applyFilters();
        });
    }

    // ── Застосування фільтрів ─────────────────────────────────────────────
    function _applyFilters() {
        let result = [..._accounts];

        // 1) Фільтр за номером картки (прибираємо пробіли для порівняння)
        if (_filterCardQuery) {
            result = result.filter(acc => {
                const normalized = (acc.card_number || '').replace(/\s/g, '').toLowerCase();
                return normalized.includes(_filterCardQuery);
            });
        }

        // 2) Фільтр за валютою
        if (_filterCurrency) {
            result = result.filter(acc => acc.currency === _filterCurrency);
        }

        // 3) Фільтр за станом
        if (_filterStatus) {
            result = result.filter(acc => acc.status === _filterStatus);
        }

        // 4) Сортування
        if (_sortBy === 'card_asc') {
            result.sort((a, b) => (a.card_number || '').localeCompare(b.card_number || ''));
        } else if (_sortBy === 'card_desc') {
            result.sort((a, b) => (b.card_number || '').localeCompare(a.card_number || ''));
        } else if (_sortBy === 'balance_asc') {
            result.sort((a, b) => a.balance - b.balance);
        } else if (_sortBy === 'balance_desc') {
            result.sort((a, b) => b.balance - a.balance);
        }

        _filtered = result;
        _renderGrid(_filtered);
        _updateFilterStatus(_filtered.length, _accounts.length);
    }

    function _updateFilterStatus(shown, total) {
        let statusEl = document.getElementById('acc-filter-status');
        if (!statusEl) {
            statusEl = document.createElement('div');
            statusEl.id = 'acc-filter-status';
            statusEl.className = 'tx-filter-status';
            const grid = document.getElementById('accounts-grid');
            grid.parentNode.insertBefore(statusEl, grid);
        }
        if (shown < total) {
            statusEl.textContent = `Показано ${shown} з ${total} рахунків`;
            statusEl.style.display = 'block';
        } else {
            statusEl.style.display = 'none';
        }
    }

    // ── Відображення сітки ────────────────────────────────────────────────
    function _renderGrid(accounts) {
        const grid = document.getElementById('accounts-grid');
        grid.innerHTML = '';
        if (accounts.length === 0) {
            grid.innerHTML = '<div class="empty-state" style="grid-column:1/-1">Рахунків не знайдено. Спробуйте змінити фільтри.</div>';
            return;
        }
        accounts.forEach(acc => grid.appendChild(_buildCard(acc)));
    }

    function _buildCard(acc) {
        const wrapper = document.createElement('div');
        wrapper.className = 'bank-card-wrapper';

        const el = document.createElement('div');
        el.className = `bank-card${acc.status === 'blocked' ? ' bank-card--blocked' : ''}`;
        const sym = { UAH: '₴', USD: '$', EUR: '€' }[acc.currency] || acc.currency;

        el.innerHTML = `
            <div class="bank-card__chip"></div>
            <div class="bank-card__number">${acc.card_number}</div>
            <div class="bank-card__footer">
                <div>
                    <div class="bank-card__balance">${sym}${Number(acc.balance).toLocaleString('uk-UA',{minimumFractionDigits:2})}</div>
                    <div class="bank-card__status">${acc.status === 'active' ? '● Active' : '○ Blocked'}</div>
                </div>
                <div class="bank-card__currency">${acc.currency}</div>
            </div>
        `;

        el.addEventListener('click', () => {
            if (acc.card_number_full) {
                UI.toast(`Повний номер: ${formatDisplay(acc.card_number_full)}`, 'info', 6000);
            }
        });

        // Кнопка поповнення — лише для активних рахунків
        const topupBtn = document.createElement('button');
        topupBtn.className = 'btn btn--topup';
        topupBtn.innerHTML = `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="14" height="14">
                <path d="M12 5v14M5 12h14"/>
            </svg>
            Поповнити рахунок
        `;
        topupBtn.disabled = acc.status === 'blocked';
        topupBtn.title = acc.status === 'blocked' ? 'Рахунок заблоковано' : 'Поповнити рахунок';

        topupBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            _openTopupModal(acc);
        });

        wrapper.appendChild(el);
        wrapper.appendChild(topupBtn);
        return wrapper;
    }

    function _populateSelects(accounts) {
        // tf-from
        const tfFrom = document.getElementById('tf-from');
        const curVal = tfFrom.value;
        tfFrom.innerHTML = '<option value="">— оберіть рахунок —</option>';
        accounts.forEach(acc => {
            const opt = document.createElement('option');
            opt.value = acc.id;
            const masked = acc.card_number || '**** **** **** ****';
            opt.textContent = `${masked} · ${UI.formatMoney(acc.balance, acc.currency)}`;
            opt.disabled = acc.status !== 'active';
            tfFrom.appendChild(opt);
        });
        if (curVal) tfFrom.value = curVal;

        // req-account
        const reqAcc = document.getElementById('req-account');
        reqAcc.innerHTML = '<option value="">— оберіть рахунок —</option>';
        accounts.forEach(acc => {
            const opt = document.createElement('option');
            opt.value = acc.id;
            opt.textContent = `${acc.card_number} (${acc.currency})`;
            reqAcc.appendChild(opt);
        });
    }

    // ── Модал поповнення рахунку ──────────────────────────────────────────
    function _openTopupModal(acc) {
        const sym = { UAH: '₴', USD: '$', EUR: '€' }[acc.currency] || acc.currency;

        // Заповнюємо дані модалу
        document.getElementById('topup-acc-id').value       = acc.id;
        document.getElementById('topup-acc-number').textContent = acc.card_number;
        document.getElementById('topup-acc-balance').textContent =
            `Поточний баланс: ${sym}${Number(acc.balance).toLocaleString('uk-UA', { minimumFractionDigits: 2 })}`;
        document.getElementById('topup-currency-badge').textContent = sym;
        document.getElementById('topup-amount').value = '';
        document.getElementById('topup-desc').value   = '';
        UI.hideAlert('topup-error');
        UI.hideAlert('topup-success');

        // Зберігаємо поточний баланс і валюту для розрахунку
        document.getElementById('topup-acc-id').dataset.balance  = acc.balance;
        document.getElementById('topup-acc-id').dataset.currency = acc.currency;

        UI.openModal('modal-topup');
    }

    document.getElementById('form-topup').addEventListener('submit', async (e) => {
        e.preventDefault();
        const form     = e.currentTarget;
        const accId    = document.getElementById('topup-acc-id').value;
        const amount   = parseFloat(document.getElementById('topup-amount').value);
        const desc     = document.getElementById('topup-desc').value.trim();
        const oldBal   = parseFloat(document.getElementById('topup-acc-id').dataset.balance) || 0;
        const currency = document.getElementById('topup-acc-id').dataset.currency || 'UAH';
        const sym      = { UAH: '₴', USD: '$', EUR: '€' }[currency] || currency;

        UI.clearErrors(form);
        UI.hideAlert('topup-error');
        UI.hideAlert('topup-success');

        if (!amount || amount <= 0) {
            UI.showError('topup-amount', 'Введіть суму більше 0');
            return;
        }
        if (amount > 1_000_000) {
            UI.showError('topup-amount', 'Максимальна сума поповнення — 1 000 000');
            return;
        }

        UI.setLoading(form, true);

        try {
            const newBalance = +(oldBal + amount).toFixed(2);
            await Api.patch(`/accounts/${accId}`, { balance: newBalance });

            UI.showAlert('topup-success',
                `✓ Рахунок поповнено на ${sym}${amount.toLocaleString('uk-UA', { minimumFractionDigits: 2 })}`
            );

            // Оновлюємо відображення поточного балансу у модалі
            document.getElementById('topup-acc-balance').textContent =
                `Поточний баланс: ${sym}${newBalance.toLocaleString('uk-UA', { minimumFractionDigits: 2 })}`;
            document.getElementById('topup-acc-id').dataset.balance = newBalance;

            setTimeout(async () => {
                UI.closeModal('modal-topup');
                await load();
                DashboardPage.load();
            }, 1200);

            UI.toast(`Поповнення ${sym}${amount.toLocaleString('uk-UA', { minimumFractionDigits: 2 })} виконано ✓`, 'success');
        } catch (err) {
            UI.showAlert('topup-error', err.message || 'Помилка поповнення');
        } finally {
            UI.setLoading(form, false);
        }
    });

    // ── Обробники кнопок створення рахунку ───────────────────────────────
    document.getElementById('btn-open-add-account').addEventListener('click', () => {
        const form = document.getElementById('form-add-account');
        form.reset();
        UI.hideAlert('acc-error');

        const num = generateCardNumber();
        setCardNumber(num);

        UI.openModal('modal-add-account');
    });

    document.getElementById('btn-regen-card').addEventListener('click', () => {
        const num = generateCardNumber();
        setCardNumber(num);
    });

    document.getElementById('form-add-account').addEventListener('submit', async (e) => {
        e.preventDefault();
        const form     = e.currentTarget;
        const currency = document.getElementById('acc-currency').value;
        const user     = Store.getUser();

        UI.clearErrors(form);
        UI.hideAlert('acc-error');
        UI.setLoading(form, true);

        try {
            await Api.createAccount({
                user_id:  user.id,
                currency: currency,
                balance:  0,          // Завжди 0 — поповнення через окрему форму
            });

            UI.closeModal('modal-add-account');
            UI.toast('Рахунок успішно створено ✓', 'success');

            await load();
            DashboardPage.load();
        } catch (err) {
            UI.showAlert('acc-error', err.message || 'Не вдалося створити рахунок');
        } finally {
            UI.setLoading(form, false);
        }
    });

    function getAccounts() { return _accounts; }

    return { load, getAccounts };
})();