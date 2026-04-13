
const DashboardPage = (() => {

  async function load() {
    const user = Store.getUser();
    if (!user) return;

    try {
      const accounts = await Api.getUserAccounts(user.id);

      // Stats
      const total = accounts.reduce((s, a) => s + (a.currency === 'UAH' ? a.balance : 0), 0);
      const active = accounts.filter(a => a.status === 'active').length;
      document.getElementById('stat-total').textContent    = UI.formatMoney(total, 'UAH');
      document.getElementById('stat-accounts').textContent = active;

      // Mini account cards
      const row = document.getElementById('dash-accounts-list');
      if (accounts.length === 0) {
        row.innerHTML = '<div class="empty-state">Рахунки не знайдено. Додайте перший рахунок.</div>';
      } else {
        row.innerHTML = '';
        row.classList.add('stagger');
        accounts.forEach(acc => {
          const card = UI.renderBankCard(acc, () => {
            // Navigate to accounts page on click
            document.querySelector('[data-page="accounts"]').click();
          });
          card.style.animation = 'fade-up .4s ease both';
          row.appendChild(card);
        });
      }

      // Recent transactions (first account)
      const txList = document.getElementById('dash-tx-list');
      if (accounts.length > 0) {
        try {
          const { items } = await Api.getAccountTx(accounts[0].id, 5, 0);
          if (items.length === 0) {
            txList.innerHTML = '<div class="empty-state">Транзакцій немає</div>';
          } else {
            txList.innerHTML = '';
            items.forEach(tx => txList.appendChild(_txItem(tx, accounts[0].id)));

            // Last tx stat
            const last = items[0];
            document.getElementById('stat-last-tx').textContent =
              (last.is_income ? '+' : '-') + UI.formatMoney(last.amount, last.currency);
            document.getElementById('stat-last-tx-date').textContent =
              UI.formatDateShort(last.created_at);
          }
        } catch {}
      } else {
        txList.innerHTML = '<div class="empty-state">Немає рахунків для відображення транзакцій</div>';
      }

    } catch (err) {
      UI.toast('Помилка завантаження дашборду: ' + err.message, 'error');
    }
  }

  function _txItem(tx, myAccountId) {
    const isOut = tx.from_account_id === myAccountId;
    const div = document.createElement('div');
    div.className = 'tx-item';
    div.innerHTML = `
      <div class="tx-item__icon ${isOut ? 'tx-item__icon--out' : 'tx-item__icon--in'}">
        ${isOut ? 'OUT' : 'IN'}
      </div>
      <div class="tx-item__body">
        <div class="tx-item__desc">${tx.description || UI.typeLabel(tx.type)}</div>
        <div class="tx-item__date">${UI.formatDate(tx.created_at)}</div>
      </div>
      <div class="tx-item__amount ${isOut ? 'tx-item__amount--out' : 'tx-item__amount--in'}">
        ${isOut ? '-' : '+'}${UI.formatMoney(tx.amount, tx.currency)}
      </div>
    `;
    return div;
  }

  // Add account from dashboard shortcut
  document.getElementById('dash-add-account').addEventListener('click', () => {
    UI.openModal('modal-add-account');
  });

  return { load };
})();