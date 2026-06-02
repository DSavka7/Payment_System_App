const UI = (() => {

  // ── Toast ──────────────────────────────────────────────────────────────────
  function toast(message, type = 'info', duration = 3500) {
    const ct = document.getElementById('toast-container');
    const el = document.createElement('div');
    el.className = `toast toast--${type}`;

    const icons = { success: '✓', error: '✕', info: '◆' };
    el.innerHTML = `<span style="color:${type === 'success' ? 'var(--green)' : type === 'error' ? 'var(--red)' : 'var(--gold)'}">${icons[type] || '◆'}</span><span>${message}</span>`;

    ct.appendChild(el);
    setTimeout(() => {
      el.style.animation = 'toast-out .25s ease forwards';
      el.addEventListener('animationend', () => el.remove(), { once: true });
    }, duration);
  }

  // ── Modal ──────────────────────────────────────────────────────────────────
  function openModal(id) {
    document.getElementById('modal-backdrop').classList.remove('hidden');
    document.getElementById(id).classList.remove('hidden');
  }

  function closeModal(id) {
    document.getElementById(id).classList.add('hidden');
    const open = document.querySelectorAll('.modal:not(.hidden)');
    if (!open.length) document.getElementById('modal-backdrop').classList.add('hidden');
  }

  document.getElementById('modal-backdrop').addEventListener('click', (e) => {
    if (e.target === e.currentTarget) {
      document.querySelectorAll('.modal:not(.hidden)').forEach(m => closeModal(m.id));
    }
  });

  document.querySelectorAll('[data-close-modal]').forEach(btn => {
    btn.addEventListener('click', () => closeModal(btn.dataset.closeModal));
  });

  // ── Form helpers ───────────────────────────────────────────────────────────
  function setLoading(form, loading) {
    const btn = form.querySelector('.btn--primary');
    if (!btn) return;
    const text   = btn.querySelector('.btn__text');
    const loader = btn.querySelector('.btn__loader');
    btn.disabled = loading;
    text?.classList.toggle('hidden', loading);
    loader?.classList.toggle('hidden', !loading);
  }

  function clearErrors(form) {
    form.querySelectorAll('.field__error').forEach(el => el.textContent = '');
    form.querySelectorAll('.field__input').forEach(el => el.classList.remove('error'));
    form.querySelectorAll('.alert').forEach(el => el.classList.add('hidden'));
  }

  function showError(fieldId, message) {
    const errEl = document.getElementById(`${fieldId}-err`);
    const inputEl = document.getElementById(fieldId);
    if (errEl) errEl.textContent = message;
    if (inputEl) inputEl.classList.add('error');
  }

  function showAlert(id, message) {
    const el = document.getElementById(id);
    if (el) { el.textContent = message; el.classList.remove('hidden'); }
  }

  function hideAlert(id) {
    const el = document.getElementById(id);
    if (el) el.classList.add('hidden');
  }

  // ── Formatters ─────────────────────────────────────────────────────────────
  const CURRENCY_SYMBOLS = { UAH: '₴', USD: '$', EUR: '€' };

  function formatMoney(amount, currency = 'UAH') {
    const sym = CURRENCY_SYMBOLS[currency] || currency;
    return `${sym}${Number(amount).toLocaleString('uk-UA', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  }

  function formatDate(dateStr) {
    if (!dateStr) return '—';
    const d    = new Date(dateStr);
    const lang = (typeof I18n !== 'undefined') ? I18n.getLang() : 'uk';
    const loc  = lang === 'en' ? 'en-GB' : 'uk-UA';
    return d.toLocaleDateString(loc, { day: '2-digit', month: 'short', year: 'numeric' })
      + ' ' + d.toLocaleTimeString(loc, { hour: '2-digit', minute: '2-digit' });
  }

  function formatDateShort(dateStr) {
    if (!dateStr) return '—';
    const d    = new Date(dateStr);
    const lang = (typeof I18n !== 'undefined') ? I18n.getLang() : 'uk';
    const loc  = lang === 'en' ? 'en-GB' : 'uk-UA';
    return d.toLocaleDateString(loc, { day: '2-digit', month: 'short' });
  }

  // ── Translatable labels ────────────────────────────────────────────────────
  // Всі рядки йдуть через I18n — якщо недоступний, фолбек на UA
  function _t(key, fallback) {
    return (typeof I18n !== 'undefined') ? I18n.t(key) : fallback;
  }

  function typeLabel(type) {
    const MAP = {
      transfer: _t('tx.type.transfer_out', 'Переказ'),
      payment:  _t('tx.type.transfer_out', 'Оплата'),
      income:   _t('tx.type.income',       'Надходження'),
    };
    return MAP[type] || type;
  }

  function typeLabelDirectional(type, isIncome) {
    if (type === 'transfer' || type === 'income') {
      return isIncome
        ? _t('tx.type.transfer_in',  'Надходження')
        : _t('tx.type.transfer_out', 'Переказ');
    }
    return typeLabel(type);
  }

  function requestTypeLabel(type) {
    const MAP = {
      BLOCK:        _t('req.type.block',        'Блокування'),
      UNBLOCK:      _t('req.type.unblock',       'Розблокування'),
      LIMIT_CHANGE: _t('req.type.limit_change',  'Зміна ліміту'),
    };
    return MAP[type] || type;
  }

  function statusBadge(status) {
    const MAP = {
      success:  ['success', _t('status.success',  'Успішно')],
      active:   ['success', _t('status.active',   'Активний')],
      blocked:  ['error',   _t('status.blocked',  'Заблоковано')],
      pending:  ['pending', _t('status.pending',  'Очікує')],
      approved: ['success', _t('status.approved', 'Схвалено')],
      rejected: ['error',   _t('status.rejected', 'Відхилено')],
    };
    const [cls, label] = MAP[status] || ['pending', status];
    return `<span class="badge badge--${cls}">${label}</span>`;
  }

  // ── Bank card renderer ──────────────────────────────────────────────────────
  function renderBankCard(acc, onClick) {
    const el = document.createElement('div');
    el.className = `bank-card${acc.status === 'blocked' ? ' bank-card--blocked' : ''}`;
    el.dataset.id = acc.id;
    const activeLabel  = _t('status.active',  'Active');
    const blockedLabel = _t('status.blocked', 'Blocked');
    el.innerHTML = `
      <div class="bank-card__chip"></div>
      <div class="bank-card__number">${acc.card_number || '**** **** **** ****'}</div>
      <div class="bank-card__footer">
        <div>
          <div class="bank-card__balance">${formatMoney(acc.balance, acc.currency)}</div>
          <div class="bank-card__status">${acc.status === 'active' ? `● ${activeLabel}` : `○ ${blockedLabel}`}</div>
        </div>
        <div class="bank-card__currency">${acc.currency}</div>
      </div>
    `;
    if (onClick) el.addEventListener('click', () => onClick(acc));
    return el;
  }

  return {
    toast, openModal, closeModal,
    setLoading, clearErrors, showError, showAlert, hideAlert,
    formatMoney, formatDate, formatDateShort,
    typeLabel, typeLabelDirectional, requestTypeLabel, statusBadge,
    renderBankCard,
  };
})();