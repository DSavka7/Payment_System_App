const AccountsPage = (() => {

    let _accounts = [];

    async function load() {
        const user = Store.getUser();
        if (!user) return;

        const grid = document.getElementById('accounts-grid');
        grid.innerHTML = '<div class="empty-state skeleton" style="height:160px;border-radius:12px"></div>';

        try {
            _accounts = await Api.getUserAccounts(user.id);
            _render(_accounts, grid);
            _populateSelects(_accounts);
        } catch (err) {
            grid.innerHTML = `<div class="empty-state">Помилка: ${err.message}</div>`;
        }
    }

    function _render(accounts, grid) {
        grid.innerHTML = '';
        if (accounts.length === 0) {
            grid.innerHTML = '<div class="empty-state" style="grid-column:1/-1">У вас поки немає рахунків.</div>';
            return;
        }
        accounts.forEach(acc => grid.appendChild(_buildCard(acc)));
    }

    function _formatFull(num16) {
        return num16.replace(/(\d{4})(\d{4})(\d{4})(\d{4})/, '$1 $2 $3 $4');
    }

    function _buildCard(acc) {
        const el = document.createElement('div');
        el.className = `bank-card${acc.status === 'blocked' ? ' bank-card--blocked' : ''}`;
        const sym = { UAH: '₴', USD: '$', EUR: '€' }[acc.currency] || acc.currency;

        // Зберігаємо стан: показано чи приховано
        let _revealed = false;
        const maskedNum = acc.card_number;
        const fullNum = acc.card_number_full ? _formatFull(acc.card_number_full) : null;

        el.innerHTML = `
            <div class="bank-card__chip"></div>
            <div class="bank-card__number-wrap" style="display:flex;align-items:center;gap:8px;margin-bottom:16px">
                <div class="bank-card__number" style="margin-bottom:0;flex:1">${maskedNum}</div>
                ${fullNum ? `
                <button class="bank-card__reveal-btn" title="Показати/приховати номер" style="
                    background:rgba(255,255,255,0.08);
                    border:1px solid rgba(255,255,255,0.15);
                    border-radius:6px;
                    color:#8b96b0;
                    cursor:pointer;
                    padding:3px 7px;
                    font-size:.65rem;
                    letter-spacing:.05em;
                    transition:all 120ms ease;
                    flex-shrink:0;
                ">👁</button>` : ''}
            </div>
            <div class="bank-card__footer">
                <div>
                    <div class="bank-card__balance">${sym}${Number(acc.balance).toLocaleString('uk-UA',{minimumFractionDigits:2})}</div>
                    <div class="bank-card__status">${acc.status === 'active' ? '● Active' : '○ Blocked'}</div>
                </div>
                <div class="bank-card__currency">${acc.currency}</div>
            </div>
        `;

        // Логіка кнопки показу номера
        if (fullNum) {
            const numEl = el.querySelector('.bank-card__number');
            const btn = el.querySelector('.bank-card__reveal-btn');

            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                _revealed = !_revealed;

                if (_revealed) {
                    numEl.textContent = fullNum;
                    numEl.style.letterSpacing = '.18em';
                    numEl.style.color = 'var(--gold-light)';
                    btn.textContent = '🙈';
                    btn.style.borderColor = 'var(--gold)';
                    btn.style.color = 'var(--gold)';

                    // Автоматично ховаємо через 10 секунд
                    setTimeout(() => {
                        if (_revealed) {
                            _revealed = false;
                            numEl.textContent = maskedNum;
                            numEl.style.letterSpacing = '';
                            numEl.style.color = '';
                            btn.textContent = '👁';
                            btn.style.borderColor = '';
                            btn.style.color = '';
                        }
                    }, 10000);
                } else {
                    numEl.textContent = maskedNum;
                    numEl.style.letterSpacing = '';
                    numEl.style.color = '';
                    btn.textContent = '👁';
                    btn.style.borderColor = '';
                    btn.style.color = '';
                }
            });

            // Копіювання по довгому кліку / правій кнопці на номер
            numEl.addEventListener('click', (e) => {
                if (!_revealed || !fullNum) return;
                navigator.clipboard.writeText(acc.card_number_full).then(() => {
                    UI.toast('Номер картки скопійовано ✓', 'success', 2000);
                }).catch(() => {});
            });
            numEl.style.cursor = 'default';
        }

        return el;
    }

    function _populateSelects(accounts) {
        const tfFrom = document.getElementById('tf-from');
        const curVal = tfFrom.value;
        tfFrom.innerHTML = '<option value="">— оберіть рахунок —</option>';
        accounts.forEach(acc => {
            const opt = document.createElement('option');
            opt.value = acc.id;
            opt.textContent = `${acc.card_number} · ${UI.formatMoney(acc.balance, acc.currency)}`;
            opt.disabled = acc.status !== 'active';
            tfFrom.appendChild(opt);
        });
        if (curVal) tfFrom.value = curVal;

        const reqAcc = document.getElementById('req-account');
        reqAcc.innerHTML = '<option value="">— оберіть рахунок —</option>';
        accounts.forEach(acc => {
            const opt = document.createElement('option');
            opt.value = acc.id;
            opt.textContent = `${acc.card_number} (${acc.currency})`;
            reqAcc.appendChild(opt);
        });
    }

    document.getElementById('btn-open-add-account').addEventListener('click', () => {
        const form = document.getElementById('form-add-account');
        form.reset();
        UI.hideAlert('acc-error');
        // Приховуємо поле номера картки — генерується на бекенді
        const cardField = document.getElementById('acc-card');
        if (cardField) cardField.closest('.field') && (cardField.closest('.field').style.display = 'none');
        const regenBtn = document.getElementById('btn-regen-card');
        if (regenBtn) regenBtn.style.display = 'none';
        UI.openModal('modal-add-account');
    });

    document.getElementById('form-add-account').addEventListener('submit', async (e) => {
        e.preventDefault();
        const form = e.currentTarget;
        const currency = document.getElementById('acc-currency').value;
        const balance = parseFloat(document.getElementById('acc-balance').value) || 0;
        const user = Store.getUser();

        UI.clearErrors(form);
        UI.hideAlert('acc-error');
        UI.setLoading(form, true);

        try {
            await Api.createAccount({
                user_id: user.id,
                currency: currency,
                balance: balance,
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