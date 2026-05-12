// accounts.js — FINAL

const AccountsPage = (() => {
  let _accounts = [];

  // ── Генерація номера (для модалки) ───────────────────────────────
  function _randSeg() {
    return String(Math.floor(1000 + Math.random() * 9000));
  }

  function _genNum() {
    return _randSeg() + _randSeg() + _randSeg() + _randSeg();
  }

  function _fmt(n16) {
    return n16.replace(/(\d{4})(\d{4})(\d{4})(\d{4})/, '$1 $2 $3 $4');
  }

  function _setCardDisplay(num16) {
    const el = document.getElementById('acc-card');
    if (el) {
      el.value = _fmt(num16);
      el.dataset.full = num16;
    }
  }

  // ── Завантаження ──────────────────────────────────────────────────
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

  // ── Рендер ────────────────────────────────────────────────────────
  function _render(accounts, grid) {
    grid.innerHTML = '';
    if (!accounts.length) {
      grid.innerHTML = '<div class="empty-state" style="grid-column:1/-1">Рахунків немає. Створіть перший!</div>';
      return;
    }
    accounts.forEach(acc => grid.appendChild(_buildCard(acc)));
  }

  // ── Картка рахунку ────────────────────────────────────────────────
  function _buildCard(acc) {
    const wrap = document.createElement('div');
    wrap.className = `bank-card${acc.status === 'blocked' ? ' bank-card--blocked' : ''}`;
    wrap.style.cursor = 'pointer';

    const sym = { UAH: '₴', USD: '$', EUR: '€' }[acc.currency] || acc.currency;
    const masked = acc.card_number || '**** **** **** ****';

    // Повний номер (якщо приходить з бекенду)
    const fullNum = acc.card_number_full || null;
    const fullDisplay = fullNum ? _fmt(fullNum) : masked;

    wrap.innerHTML = `
      <div class="bank-card__chip"></div>
      <div class="bank-card__number">${masked}</div>
      <div class="bank-card__footer">
        <div>
          <div class="bank-card__balance">${sym}${Number(acc.balance).toLocaleString('uk-UA',{minimumFractionDigits:2})}</div>
          <div class="bank-card__status">${acc.status === 'active' ? '● Active' : '○ Blocked'}</div>
        </div>
        <div class="bank-card__currency">${acc.currency}</div>
      </div>
      <div style="position:absolute;bottom:10px;left:50%;transform:translateX(-50%);
                  font-size:.58rem;letter-spacing:.05em;color:rgba(255,255,255,.22);
                  white-space:nowrap;pointer-events:none;">
        📋 натисніть щоб скопіювати номер
      </div>
    `;

    // Клік по картці
    wrap.addEventListener('click', function() {
      const numEl = wrap.querySelector('.bank-card__number');

      // Показуємо повний номер тимчасово
      numEl.textContent = fullDisplay;
      numEl.style.color = 'var(--gold-light)';
      numEl.style.transition = 'color .3s';

      setTimeout(() => {
        numEl.textContent = masked;
        numEl.style.color = '';
      }, 4000);

      // Копіюємо
      const copyText = fullNum || masked.replace(/\s/g, '');
      _copy(copyText, fullDisplay);
    });

    return wrap;
  }

  function _copy(text, display) {
    const done = () => UI.toast('📋 Скопійовано: ' + display, 'success', 4000);

    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(text).then(done).catch(() => _execCopy(text, display));
    } else {
      _execCopy(text, display);
    }
  }

  function _execCopy(text, display) {
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.style.cssText = 'position:fixed;top:0;left:0;width:1px;height:1px;opacity:0';
    document.body.appendChild(ta);
    ta.focus();
    ta.select();
    const ok = document.execCommand('copy');
    document.body.removeChild(ta);

    UI.toast(
      ok ? '📋 Скопійовано: ' + display : 'Номер: ' + display,
      ok ? 'success' : 'info',
      4000
    );
  }

  // ── Populate Selects ──────────────────────────────────────────────
  function _populateSelects(accounts) {
    const tfFrom = document.getElementById('tf-from');
    if (tfFrom) {
      const saved = tfFrom.value;
      tfFrom.innerHTML = '<option value="">— оберіть рахунок —</option>';
      accounts.forEach(acc => {
        const o = document.createElement('option');
        o.value = acc.id;
        o.textContent = `${acc.card_number || '****'} · ${UI.formatMoney(acc.balance, acc.currency)}`;
        o.disabled = acc.status !== 'active';
        tfFrom.appendChild(o);
      });
      if (saved) tfFrom.value = saved;
    }

    const reqAcc = document.getElementById('req-account');
    if (reqAcc) {
      reqAcc.innerHTML = '<option value="">— оберіть рахунок —</option>';
      accounts.forEach(acc => {
        const o = document.createElement('option');
        o.value = acc.id;
        o.textContent = `${acc.card_number} (${acc.currency})`;
        reqAcc.appendChild(o);
      });
    }
  }

  // ── Модалка: новий рахунок ────────────────────────────────────────
  const btnOpen = document.getElementById('btn-open-add-account');
  if (btnOpen) {
    btnOpen.addEventListener('click', () => {
      document.getElementById('form-add-account').reset();
      UI.hideAlert('acc-error');
      _setCardDisplay(_genNum());
      UI.openModal('modal-add-account');
    });
  }

  const btnRegen = document.getElementById('btn-regen-card');
  if (btnRegen) {
    btnRegen.addEventListener('click', () => _setCardDisplay(_genNum()));
  }

  const formAdd = document.getElementById('form-add-account');
  if (formAdd) {
    formAdd.addEventListener('submit', async (e) => {
      e.preventDefault();
      const currency = document.getElementById('acc-currency').value;
      const balance = parseFloat(document.getElementById('acc-balance').value) || 0;
      const user = Store.getUser();

      UI.clearErrors(formAdd);
      UI.hideAlert('acc-error');
      UI.setLoading(formAdd, true);

      try {
        await Api.createAccount({ user_id: user.id, currency, balance });
        UI.closeModal('modal-add-account');
        UI.toast('Рахунок створено ✓', 'success');
        await load();
        if (typeof DashboardPage !== 'undefined') DashboardPage.load();
      } catch (err) {
        let msg = err.message || 'Помилка';
        try {
          const p = JSON.parse(msg);
          if (Array.isArray(p)) msg = p.map(e => e.msg || e.message).join('; ');
          else if (p && p.detail) msg = typeof p.detail === 'string' ? p.detail : JSON.stringify(p.detail);
        } catch {}
        UI.showAlert('acc-error', msg);
      } finally {
        UI.setLoading(formAdd, false);
      }
    });
  }

  function getAccounts() {
    return _accounts;
  }

  return { load, getAccounts };
})();