
const RequestsPage = (() => {

  async function load() {
    const user = Store.getUser();
    if (!user) return;

    const list = document.getElementById('requests-list');
    list.innerHTML = '<div class="empty-state skeleton" style="height:80px;border-radius:12px"></div>';

    try {
      const requests = await Api.getUserRequests(user.id);
      _render(requests, list);
    } catch (err) {
      list.innerHTML = `<div class="empty-state">Помилка: ${err.message}</div>`;
    }
  }

  function _render(requests, list) {
    list.innerHTML = '';
    if (requests.length === 0) {
      list.innerHTML = '<div class="empty-state">Запитів немає. Натисніть "+ Новий запит".</div>';
      return;
    }
    list.classList.add('stagger');
    requests.forEach(req => {
      const card = document.createElement('div');
      card.className = 'request-card';
      card.style.animation = 'fade-up .4s ease both';
      card.innerHTML = `
        <div class="request-card__type">${UI.requestTypeLabel(req.type)}</div>
        <div class="request-card__body">
          <div class="request-card__message">${req.message}</div>
          <div class="request-card__footer">
            ${UI.statusBadge(req.status)}
            <span class="request-card__meta">${UI.formatDate(req.created_at)}</span>
          </div>
          ${req.admin_comment ? `<div class="request-card__comment">Коментар адміна: ${req.admin_comment}</div>` : ''}
        </div>
      `;
      list.appendChild(card);
    });
  }

  document.getElementById('btn-open-add-request').addEventListener('click', () => {
    UI.openModal('modal-add-request');
  });

  document.getElementById('form-add-request').addEventListener('submit', async (e) => {
    e.preventDefault();
    const form    = e.currentTarget;
    const accId   = document.getElementById('req-account').value;
    const type    = document.getElementById('req-type').value;
    const message = document.getElementById('req-message').value.trim();
    const user    = Store.getUser();

    UI.clearErrors(form);
    let valid = true;
    if (!accId)   { UI.showError('req-account', 'Оберіть рахунок'); valid = false; }
    if (!message) { UI.showError('req-message', 'Введіть повідомлення'); valid = false; }
    if (!valid) return;

    UI.setLoading(form, true);
    UI.hideAlert('req-error');
    UI.hideAlert('req-success');
    try {
      await Api.createRequest({ user_id: user.id, account_id: accId, type, message });
      UI.showAlert('req-success', '✓ Запит надіслано адміністратору');
      form.reset();
      setTimeout(async () => {
        UI.closeModal('modal-add-request');
        await load();
      }, 1200);
    } catch (err) {
      UI.showAlert('req-error', err.message);
    } finally {
      UI.setLoading(form, false);
    }
  });

  return { load };
})();