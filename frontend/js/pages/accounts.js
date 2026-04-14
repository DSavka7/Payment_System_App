

const AccountsPage = (() => {

    let _accounts = [];

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

    async function load() {
        const user = Store.getUser();
        if (!user) return;

        const grid = document.getElementById('accounts-grid');
        grid.innerHTML = '<div class="empty-state skeleton" style="height:160px;border-radius:12px"></div>';

        try {
            _accounts = await Api.createAccount ? await Api.getUserAccounts(user.id) : [];
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

    function _buildCard(acc) {
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

        return el;
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

    // Обработчики
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
                balance: balance

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