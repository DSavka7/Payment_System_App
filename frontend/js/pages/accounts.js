
const AccountsPage = (() => {

  let _accounts = [];


  function generateCardNumber() {
    const rand4 = () => Math.floor(1000 + Math.random() * 9000);
    const first = rand4();
    const last  = rand4();
    return `${first} **** **** ${last}`;
  }

  // ── Load accounts ───────────────────────────────────────────────────────────
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
      grid.innerHTML = '<div class="empty-state" style="grid-column:1/-1">У вас поки немає рахунків. Натисніть "+ Новий рахунок".</div>';
      return;
    }
    grid.classList.add('stagger');
    accounts.forEach(acc => {
      const card = UI.renderBankCard(acc);
      card.style.animation = 'fade-up .4s ease both';
      card.addEventListener('click', () => {
        UI.toast(`ID: ${acc.id} · ${UI.formatMoney(acc.balance, acc.currency)} · ${acc.status}`, 'info', 5000);
      });
      grid.appendChild(card);
    });
  }

  function _populateSelects(accounts) {
    // Transfer from-select
    const tfFrom = document.getElementById('tf-from');
    const currentVal = tfFrom.value;
    tfFrom.innerHTML = '<option value="">— оберіть рахунок —</option>';
    accounts.forEach(acc => {
      const opt = document.createElement('option');
      opt.value = acc.id;
      opt.textContent = `${acc.card_number} · ${UI.formatMoney(acc.balance, acc.currency)}`;
      opt.disabled = acc.status !== 'active';
      tfFrom.appendChild(opt);
    });
    if (currentVal) tfFrom.value = currentVal;

    // TX filter select
    const txFilter = document.getElementById('tx-account-filter');
    txFilter.innerHTML = '<option value="">— оберіть рахунок —</option>';
    accounts.forEach(acc => {
      const opt = document.createElement('option');
      opt.value = acc.id;
      opt.textContent = `${acc.card_number} (${acc.currency})`;
      txFilter.appendChild(opt);
    });

    // Request account select
    const reqAcc = document.getElementById('req-account');
    reqAcc.innerHTML = '<option value="">— оберіть рахунок —</option>';
    accounts.forEach(acc => {
      const opt = document.createElement('option');
      opt.value = acc.id;
      opt.textContent = `${acc.card_number} (${acc.currency})`;
      reqAcc.appendChild(opt);
    });
  }

  // Update currency badge in transfer when account selected
  document.getElementById('tf-from').addEventListener('change', function () {
    const acc = _accounts.find(a => a.id === this.value);
    const sym = { UAH: '₴', USD: '$', EUR: '€' };
    document.getElementById('tf-currency-badge').textContent = acc ? (sym[acc.currency] || acc.currency) : '₴';
  });

  // Кнопка перегенерации номера карты
  document.addEventListener('click', (e) => {
    if (e.target && e.target.id === 'btn-regen-card') {
      document.getElementById('acc-card').value = generateCardNumber();
    }
  });

  // Open modal — автоматически генерируем номер карты
  document.getElementById('btn-open-add-account').addEventListener('click', () => {
    // Вставляем сгенерированный номер в поле
    document.getElementById('acc-card').value = generateCardNumber();
    UI.openModal('modal-add-account');
  });

  // Кнопка для повторной генерации номера
  const cardInput = document.getElementById('acc-card');
  if (cardInput) {
    cardInput.addEventListener('dblclick', () => {
      cardInput.value = generateCardNumber();
    });
  }

  // Add account form
  document.getElementById('form-add-account').addEventListener('submit', async (e) => {
    e.preventDefault();
    const form    = e.currentTarget;
    const card    = document.getElementById('acc-card').value.trim();
    const curr    = document.getElementById('acc-currency').value;
    const balance = parseFloat(document.getElementById('acc-balance').value) || 0;
    const user    = Store.getUser();

    UI.clearErrors(form);
    let valid = true;
    if (!/^\d{4} \*{4} \*{4} \d{4}$/.test(card)) {
      UI.showError('acc-card', 'Формат: 1234 **** **** 5678');
      valid = false;
    }
    if (!valid) return undefined;

    UI.setLoading(form, true);
    try {
      await Api.createAccount({
        user_id: user.id,
        card_number: card,
        currency: curr,
        balance,
      });
      UI.closeModal('modal-add-account');
      form.reset();
      UI.toast('Рахунок успішно створено ✓', 'success');
      await load();
      DashboardPage.load();
    } catch (err) {
      UI.showAlert('acc-error', err.message);
    } finally {
      UI.setLoading(form, false);
    }
  });

  function getAccounts() { return _accounts; }

  return { load, getAccounts };
})();