// transfer.js
const TransferPage = (() => {

  document.getElementById('form-transfer').addEventListener('submit', async (e) => {
    e.preventDefault();
    const form      = e.currentTarget;
    const fromId    = document.getElementById('tf-from').value;
    let toCard      = document.getElementById('tf-to').value.trim();
    toCard = toCard.replace(/\s+/g, '').replace(/\D/g, '');

    const amount    = parseFloat(document.getElementById('tf-amount').value);
    const desc      = document.getElementById('tf-desc').value.trim();

    UI.clearErrors(form);
    UI.hideAlert('tf-error');
    UI.hideAlert('tf-success');

    let valid = true;

    if (!fromId) { UI.showError('tf-from', 'Оберіть рахунок відправника'); valid = false; }
    if (toCard.length !== 16 || !/^\d{16}$/.test(toCard)) {
      UI.showError('tf-to', 'Номер картки має містити рівно 16 цифр');
      valid = false;
    }
    if (!amount || amount <= 0) { UI.showError('tf-amount', 'Введіть суму більше 0'); valid = false; }

    if (valid) {
      const accounts = AccountsPage.getAccounts();
      const fromAcc  = accounts.find(a => a.id === fromId);
      if (fromAcc && fromAcc.card_number_full === toCard) {
        UI.showError('tf-to', 'Не можна переказувати на той самий рахунок');
        valid = false;
      }
    }

    if (!valid) return;

    UI.setLoading(form, true);

    try {
      const tx = await Api.transfer({
        from_account_id: fromId,
        to_card_number: toCard,
        amount,
        description: desc || undefined,
      });

      // === ВИПРАВЛЕННЯ ДЛЯ ПІДОЗРІЛИХ ТРАНЗАКЦІЙ ===
      if (tx.is_suspicious || tx.status === 'pending_review') {
        UI.showAlert('tf-success',
          `⚠️ Транзакція на суму ${UI.formatMoney(tx.amount, tx.currency)} очікує перевірки адміністратора.`
        );
      } else {
        UI.showAlert('tf-success',
          `✓ Переказ ${UI.formatMoney(tx.amount, tx.currency)} виконано успішно!`
        );
      }

      form.reset();
      document.getElementById('tf-currency-badge').textContent = '₴';

      await AccountsPage.load();
      DashboardPage.load();
      UI.toast('Операція виконана', 'success');

    } catch (err) {
      UI.showAlert('tf-error', err.message || 'Помилка переказу');
    } finally {
      UI.setLoading(form, false);
    }
  });

  return {};
})();