const TransferPage = (() => {

  document.getElementById('form-transfer').addEventListener('submit', async (e) => {
    e.preventDefault();
    const form   = e.currentTarget;
    const fromId = document.getElementById('tf-from').value;
    const toId   = document.getElementById('tf-to').value.trim();
    const amount = parseFloat(document.getElementById('tf-amount').value);
    const desc   = document.getElementById('tf-desc').value.trim();

    UI.clearErrors(form);
    let valid = true;
    if (!fromId) { UI.showError('tf-from', 'Оберіть рахунок відправника'); valid = false; }
    if (!toId)   { UI.showError('tf-to', 'Введіть ID рахунку отримувача'); valid = false; }
    if (!amount || amount <= 0) { UI.showError('tf-amount', 'Введіть суму більше 0'); valid = false; }
    if (fromId && toId && fromId === toId) {
      UI.showError('tf-to', 'Не можна переказувати на той самий рахунок');
      valid = false;
    }
    if (!valid) return;

    UI.setLoading(form, true);
    UI.hideAlert('tf-error');
    UI.hideAlert('tf-success');
    try {
      const tx = await Api.transfer({
        from_account_id: fromId,
        to_account_id:   toId,
        amount,
        description: desc || undefined,
      });

      UI.showAlert('tf-success',
        `✓ Переказ ${UI.formatMoney(tx.amount, tx.currency)} виконано успішно!`
      );
      form.reset();
      document.getElementById('tf-currency-badge').textContent = '₴';

      // Refresh accounts balance
      await AccountsPage.load();
      DashboardPage.load();
      UI.toast('Переказ виконано', 'success');
    } catch (err) {
      UI.showAlert('tf-error', err.message);
    } finally {
      UI.setLoading(form, false);
    }
  });

  return {};
})();