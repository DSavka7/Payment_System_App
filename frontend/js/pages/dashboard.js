const DashboardPage = (() => {

  async function load() {
    const user = Store.getUser();
    if (!user) return;

    try {
      const accounts = await Api.getUserAccounts(user.id);

      // ── Статистика балансів по валютах ──────────────────────────────
      const active = accounts.filter(a => a.status === 'active').length;
      document.getElementById('stat-accounts').textContent = active;

      // Групуємо баланси по валютах
      const balances = {};
      accounts.forEach(a => {
        if (!balances[a.currency]) balances[a.currency] = 0;
        balances[a.currency] += a.balance;
      });

      const sym = { UAH: '₴', USD: '$', EUR: '€' };
      const currencies = ['UAH', 'USD', 'EUR'].filter(c => balances[c] !== undefined);

      if (currencies.length === 0) {
        document.getElementById('stat-total').textContent = '0,00 ₴';
      } else if (currencies.length === 1) {
        const c = currencies[0];
        document.getElementById('stat-total').textContent = UI.formatMoney(balances[c], c);
      } else {
        // Кілька валют — показуємо кожну на новому рядку
        document.getElementById('stat-total').innerHTML = currencies
          .map(c => `<div style="font-size:${currencies.length > 2 ? '1.1rem' : '1.3rem'};line-height:1.4">${UI.formatMoney(balances[c], c)}</div>`)
          .join('');
      }

      // ── Картки рахунків ─────────────────────────────────────────────
      const row = document.getElementById('dash-accounts-list');
      if (accounts.length === 0) {
        row.innerHTML = '<div class="empty-state">Рахунки не знайдено. Додайте перший рахунок.</div>';
      } else {
        row.innerHTML = '';
        row.classList.add('stagger');
        accounts.forEach(acc => {
          const card = UI.renderBankCard(acc, () => {
            document.querySelector('[data-page="accounts"]').click();
          });
          card.style.animation = 'fade-up .4s ease both';
          row.appendChild(card);
        });
      }

      // ── Останні транзакції з УСІХ рахунків ─────────────────────────
      const txList = document.getElementById('dash-tx-list');
      const myAccountIds = accounts.map(a => a.id);

      if (accounts.length === 0) {
        txList.innerHTML = '<div class="empty-state">Немає рахунків для відображення транзакцій</div>';
        return;
      }

      try {
        // Завантажуємо транзакції з усіх рахунків паралельно
        const results = await Promise.allSettled(
          accounts.map(acc => Api.getAccountTx(acc.id, 20, 0))
        );

        // Збираємо унікальні транзакції
        const seen = new Set();
        const allTx = [];
        results.forEach(r => {
          if (r.status === 'fulfilled') {
            (r.value.items || []).forEach(tx => {
              if (!seen.has(tx.id)) {
                seen.add(tx.id);
                allTx.push(tx);
              }
            });
          }
        });

        // Сортуємо за датою (найновіші першими)
        allTx.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));

        // Беремо топ-5
        const recent = allTx.slice(0, 5);

        if (recent.length === 0) {
          txList.innerHTML = '<div class="empty-state">Транзакцій немає</div>';
          document.getElementById('stat-last-tx').textContent = '—';
          document.getElementById('stat-last-tx-date').textContent = '—';
        } else {
          txList.innerHTML = '';
          recent.forEach(tx => txList.appendChild(_txItem(tx, myAccountIds)));

          // Останній переказ — найновіша транзакція де юзер відправник або отримувач
          const last = recent[0];
          const lastIsOut = myAccountIds.includes(last.from_account_id) && !myAccountIds.includes(last.to_account_id)
            || (myAccountIds.includes(last.from_account_id) && myAccountIds.includes(last.to_account_id) && last.from_account_id !== last.to_account_id);
          // Спрощена логіка: якщо from_account_id належить нам — витрата
          const isOutgoing = myAccountIds.includes(last.from_account_id);
          document.getElementById('stat-last-tx').textContent =
            (isOutgoing ? '-' : '+') + UI.formatMoney(last.amount, last.currency);
          document.getElementById('stat-last-tx-date').textContent =
            UI.formatDateShort(last.created_at);
        }
      } catch (err) {
        txList.innerHTML = '<div class="empty-state">Помилка завантаження транзакцій</div>';
      }

    } catch (err) {
      UI.toast('Помилка завантаження дашборду: ' + err.message, 'error');
    }
  }

  function _txItem(tx, myAccountIds) {
    // isOut = гроші ВИХОДЯТЬ з наших рахунків
    const isOut = myAccountIds.includes(tx.from_account_id);
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