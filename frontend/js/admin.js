/**
 * admin.js — Повноцінна адмін-панель Vault.
 * Не залежить від ui.js — містить власні AdminUI утиліти.
 */

const API = 'http://localhost:8000';

// ══════════════════════════════════════════════════════════════════
// AdminUI — власні UI-утиліти (незалежні від ui.js)
// ══════════════════════════════════════════════════════════════════
const AdminUI = {
  toast(message, type = 'info', duration = 3500) {
    const ct = document.getElementById('toast-container');
    if (!ct) return;
    const el = document.createElement('div');
    el.className = `toast toast--${type}`;
    const icons = { success: '✓', error: '✕', info: '◆' };
    const color = type === 'success' ? 'var(--green)' : type === 'error' ? 'var(--red)' : 'var(--gold)';
    el.innerHTML = `<span style="color:${color}">${icons[type] || '◆'}</span><span>${message}</span>`;
    ct.appendChild(el);
    setTimeout(() => {
      el.style.animation = 'toast-out .25s ease forwards';
      el.addEventListener('animationend', () => el.remove(), { once: true });
    }, duration);
  },

  formatDate(dateStr) {
    if (!dateStr) return '—';
    const d = new Date(dateStr);
    return d.toLocaleDateString('uk-UA', { day: '2-digit', month: 'short', year: 'numeric' })
      + ' ' + d.toLocaleTimeString('uk-UA', { hour: '2-digit', minute: '2-digit' });
  },

  formatDateShort(dateStr) {
    if (!dateStr) return '—';
    const d = new Date(dateStr);
    return d.toLocaleDateString('uk-UA', { day: '2-digit', month: 'short' });
  },

  statusBadge(status) {
    const MAP = {
      success:        ['success', 'Успішно'],
      active:         ['success', 'Активний'],
      blocked:        ['error',   'Заблоковано'],
      pending:        ['pending', 'Очікує'],
      pending_review: ['pending', 'На перевірці'],
      approved:       ['success', 'Схвалено'],
      rejected:       ['error',   'Відхилено'],
    };
    const [cls, label] = MAP[status] || ['pending', status];
    return `<span class="badge badge--${cls}">${label}</span>`;
  },
};

// ══════════════════════════════════════════════════════════════════
// API helpers
// ══════════════════════════════════════════════════════════════════
async function adminFetch(path, options = {}) {
  const token = Store.get('accessToken');
  const headers = { 'Content-Type': 'application/json', ...options.headers };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${API}${path}`, { ...options, headers });

  if (res.status === 401) {
    const rt = Store.get('refreshToken');
    if (rt) {
      try {
        const rRes = await fetch(`${API}/users/refresh`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: rt }),
        });
        const rData = await rRes.json();
        if (rData.access_token) {
          Store.set('accessToken', rData.access_token);
          return adminFetch(path, options);
        }
      } catch {}
    }
    showGuard();
    throw new Error('Сесія завершена');
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    // Pydantic validation errors come as array in body.detail
    let detail = body.detail;
    if (Array.isArray(detail)) {
      // Extract human-readable messages from Pydantic error list
      detail = detail.map(e => {
        const field = e.loc ? e.loc[e.loc.length - 1] : '';
        return field ? `${field}: ${e.msg}` : e.msg;
      }).join('; ');
    }
    throw new Error(detail || `HTTP ${res.status}`);
  }
  if (res.status === 204) return null;
  return res.json();
}

const adminGet   = (path)       => adminFetch(path, { method: 'GET' });
const adminPatch = (path, body) => adminFetch(path, { method: 'PATCH', body: JSON.stringify(body) });

// ══════════════════════════════════════════════════════════════════
// STATE
// ══════════════════════════════════════════════════════════════════
let currentAdminId = null; // ID поточного адміна — захист від самоблокування

const State = {
  stats: null,
  usersPage: 0,    usersLimit: 15,  usersSearch: '', usersStatus: '',  usersTotal: 0,
  suspiciousPage: 0, suspiciousLimit: 10, suspiciousStatus: '', suspiciousTotal: 0,
  requestsPage: 0, requestsLimit: 10, requestsStatus: '', requestsTotal: 0,
  pendingUserId: null, pendingUserAction: null,
  pendingTxId: null,
  pendingRequestId: null,
};

// ══════════════════════════════════════════════════════════════════
// BOOT
// ══════════════════════════════════════════════════════════════════
document.addEventListener('DOMContentLoaded', async () => {
  if (!Store.isLoggedIn()) {
    try {
      const rt = Store.get('refreshToken');
      if (!rt) throw new Error('no rt');
      const res = await fetch(`${API}/users/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: rt }),
      });
      const data = await res.json();
      if (!data.access_token) throw new Error('no token');
      Store.set('accessToken', data.access_token);
    } catch {
      showGuard(); return;
    }
  }

  try {
    const user = await adminGet('/users/me');
    Store.setUser(user);
    if (user.role !== 'ADMIN') { showGuard(); return; }
    currentAdminId = user.id; // зберігаємо щоб не давати заблокувати себе
    document.getElementById('admin-email').textContent  = user.email;
    document.getElementById('admin-avatar').textContent = (user.email || 'A')[0].toUpperCase();
  } catch {
    showGuard(); return;
  }

  bindNav();
  bindSidebar();
  bindLogout();
  bindUserModal();
  bindReviewTxModal();
  bindReviewRequestModal();
  bindFilters();

  // PDF report button
  document.getElementById('admin-pdf-btn')?.addEventListener('click', () => {
    AdminPDF.generateReport();
  });

  await loadOverview();
});

function showGuard() {
  document.getElementById('admin-auth-guard').classList.remove('hidden');
  document.getElementById('admin-app').style.visibility = 'hidden';
}

// ══════════════════════════════════════════════════════════════════
// NAVIGATION
// ══════════════════════════════════════════════════════════════════
const PAGE_TITLES = {
  'admin-overview':   'Панель адміністратора',
  'admin-users':      'Управління користувачами',
  'admin-suspicious': 'Підозрілі перекази',
  'admin-requests':   'Запити користувачів',
};
const PAGE_LOADERS = {
  'admin-overview':   loadOverview,
  'admin-users':      () => loadUsers(0),
  'admin-suspicious': () => loadSuspicious(0),
  'admin-requests':   () => loadRequests(0),
};

function bindNav() {
  document.querySelectorAll('[data-page]').forEach(el => {
    el.addEventListener('click', e => {
      e.preventDefault();
      navigateTo(el.dataset.page);
    });
  });
}

function navigateTo(pageId) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

  const page = document.getElementById(`page-${pageId}`);
  const nav  = document.querySelector(`.nav-item[data-page="${pageId}"]`);
  if (page) page.classList.add('active');
  if (nav)  nav.classList.add('active');

  const title = document.getElementById('admin-page-title');
  if (title) title.textContent = PAGE_TITLES[pageId] || '';

  const loader = PAGE_LOADERS[pageId];
  if (loader) loader();
}

function bindSidebar() {
  const burger  = document.getElementById('sidebar-toggle');
  const sidebar = document.querySelector('.sidebar');
  const overlay = document.getElementById('sidebar-overlay');
  if (!burger) return;
  burger.addEventListener('click', () => {
    const open = sidebar.classList.toggle('open');
    overlay.classList.toggle('visible', open);
    burger.classList.toggle('open', open);
  });
  overlay.addEventListener('click', () => {
    sidebar.classList.remove('open');
    overlay.classList.remove('visible');
    burger.classList.remove('open');
  });
  document.querySelectorAll('.nav-item[data-page]').forEach(el => {
    el.addEventListener('click', () => {
      sidebar.classList.remove('open');
      overlay.classList.remove('visible');
      burger.classList.remove('open');
    });
  });
}

function bindLogout() {
  document.getElementById('admin-btn-logout').addEventListener('click', async () => {
    try { await adminFetch('/users/logout', { method: 'POST', body: JSON.stringify({ refresh_token: Store.get('refreshToken') }) }); } catch {}
    Store.clear();
    window.location.href = 'index.html';
  });
}

function bindFilters() {
  let searchTimer;
  document.getElementById('users-search').addEventListener('input', e => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => { State.usersSearch = e.target.value.trim(); loadUsers(0); }, 350);
  });
  document.getElementById('users-status-filter').addEventListener('change', e => {
    State.usersStatus = e.target.value;
    loadUsers(0);
  });

  document.querySelectorAll('.admin-tab').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.admin-tab').forEach(b => b.classList.remove('admin-tab--active'));
      btn.classList.add('admin-tab--active');
      State.suspiciousStatus = btn.dataset.status;
      loadSuspicious(0);
    });
  });

  document.getElementById('req-status-filter').addEventListener('change', e => {
    State.requestsStatus = e.target.value;
    loadRequests(0);
  });
}

// ══════════════════════════════════════════════════════════════════
// OVERVIEW
// ══════════════════════════════════════════════════════════════════
async function loadOverview() {
  try {
    const stats = await adminGet('/admin/stats');
    State.stats = stats;

    document.getElementById('stat-total-users').textContent      = stats.total_users;
    document.getElementById('stat-users-sub').textContent        = `${stats.active_users} активних / ${stats.blocked_users} заблоковано`;
    document.getElementById('stat-blocked-users').textContent    = stats.blocked_users;
    document.getElementById('stat-pending-review').textContent   = stats.pending_review_transactions;
    document.getElementById('stat-pending-requests').textContent = stats.pending_requests;
    document.getElementById('stat-total-accounts').textContent   = stats.total_accounts;
    document.getElementById('stat-total-tx').textContent         = stats.total_transactions;

    setBadge('nav-badge-blocked',    stats.blocked_users);
    setBadge('nav-badge-suspicious', stats.pending_review_transactions);
    setBadge('nav-badge-requests',   stats.pending_requests);

    const suspData = await adminGet('/admin/suspicious?status=pending_review&limit=3&offset=0');
    renderSuspiciousCards(suspData.items || [], 'overview-suspicious-list', true);

    const reqData = await adminGet('/admin/requests?status=pending&limit=5&offset=0');
    renderRequestCards(reqData.items || [], 'overview-requests-list', true);

  } catch (err) {
    AdminUI.toast('Помилка завантаження: ' + err.message, 'error');
  }
}

function setBadge(id, count) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = count > 0 ? count : '';
}

// ══════════════════════════════════════════════════════════════════
// USERS
// ══════════════════════════════════════════════════════════════════
async function loadUsers(offset = 0) {
  State.usersPage = offset;
  const tbody = document.getElementById('users-tbody');
  tbody.innerHTML = `<tr><td colspan="7"><div class="skeleton" style="height:40px;border-radius:6px;margin:4px 0"></div></td></tr>`.repeat(5);

  try {
    const params = new URLSearchParams({ limit: State.usersLimit, offset });
    if (State.usersSearch) params.append('search', State.usersSearch);
    if (State.usersStatus) params.append('status', State.usersStatus);

    const data = await adminGet(`/admin/users?${params}`);
    State.usersTotal = data.total;
    renderUsersTable(data.items || []);
    renderPagination('users-pagination', data.total, State.usersLimit, offset, loadUsers);
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="7" class="table-empty">Помилка: ${err.message}</td></tr>`;
  }
}

function renderUsersTable(users) {
  const tbody = document.getElementById('users-tbody');
  if (!users.length) {
    tbody.innerHTML = '<tr><td colspan="7" class="table-empty">Користувачів не знайдено</td></tr>';
    return;
  }
  tbody.innerHTML = '';
  users.forEach(u => {
    const isBlocked = u.status === 'blocked';
    const isSelf    = u.id === currentAdminId;
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>
        <div class="user-name-cell">${escHtml(u.first_name)} ${escHtml(u.last_name)}</div>
        <div class="user-email-cell">${escHtml(u.email)}</div>
      </td>
      <td style="font-family:var(--font-mono);font-size:.78rem;color:var(--silver)">${escHtml(u.phone || '—')}</td>
      <td><span class="badge ${u.role === 'ADMIN' ? 'badge--error' : 'badge--pending'}">${u.role}</span></td>
      <td style="font-family:var(--font-mono);text-align:center">${u.accounts_count}</td>
      <td>${AdminUI.statusBadge(u.status)}</td>
      <td class="tx-date-cell">${AdminUI.formatDateShort(u.created_at)}</td>
      <td>
        <div class="action-btns">
          ${isSelf ? '' : `
          <button class="action-btn ${isBlocked ? 'action-btn--success' : 'action-btn--danger'}" data-action="toggle-status">
            ${isBlocked ? '🔓 Розблокувати' : '🔒 Заблокувати'}
          </button>`}
        </div>
      </td>
    `;
    if (!isSelf) {
      tr.querySelector('[data-action="toggle-status"]').addEventListener('click', (e) => { e.stopPropagation(); openUserStatusModal(u); });
      tr.style.cursor = 'pointer';
      tr.addEventListener('click', () => openUserDetails(u.id));
    }
    tbody.appendChild(tr);
  });
}

// ── User status modal ──────────────────────────────────────────────
function bindUserModal() {
  document.getElementById('close-user-modal').addEventListener('click', closeUserModal);
  document.getElementById('cancel-user-modal').addEventListener('click', closeUserModal);
  document.getElementById('modal-user-status-backdrop').addEventListener('click', e => {
    if (e.target === e.currentTarget) closeUserModal();
  });
  document.getElementById('confirm-user-status').addEventListener('click', confirmUserStatus);
}

function openUserStatusModal(user) {
  if (user.id === currentAdminId) return; // не можна заблокувати себе
  State.pendingUserId     = user.id;
  State.pendingUserAction = user.status === 'active' ? 'blocked' : 'active';

  const isBlocking = State.pendingUserAction === 'blocked';
  document.getElementById('modal-user-title').textContent = isBlocking
    ? '🔒 Блокування користувача'
    : '🔓 Розблокування користувача';

  document.getElementById('modal-user-info').innerHTML = `
    <div class="review-row"><span class="review-row__label">Ім'я</span><span class="review-row__val">${escHtml(user.first_name)} ${escHtml(user.last_name)}</span></div>
    <div class="review-row"><span class="review-row__label">Email</span><span class="review-row__val review-row__val--mono">${escHtml(user.email)}</span></div>
    <div class="review-row"><span class="review-row__label">Телефон</span><span class="review-row__val review-row__val--mono">${escHtml(user.phone || '—')}</span></div>
    <div class="review-row"><span class="review-row__label">Рахунки</span><span class="review-row__val">${user.accounts_count}</span></div>
    <div class="review-row"><span class="review-row__label">Зараз</span><span class="review-row__val">${AdminUI.statusBadge(user.status)}</span></div>
  `;

  const confirmBtn = document.getElementById('confirm-user-status');
  confirmBtn.textContent = isBlocking ? '🔒 Заблокувати' : '🔓 Розблокувати';
  confirmBtn.style.background = isBlocking
    ? 'linear-gradient(135deg,var(--red),#b91c1c)'
    : 'linear-gradient(135deg,var(--green),#2da870)';

  document.getElementById('block-reason').value = '';
  document.getElementById('user-modal-error').classList.add('hidden');
  document.getElementById('modal-user-status-backdrop').classList.remove('hidden');
}

function closeUserModal() {
  document.getElementById('modal-user-status-backdrop').classList.add('hidden');
  State.pendingUserId = null;
  State.pendingUserAction = null;
}

async function confirmUserStatus() {
  if (!State.pendingUserId || !State.pendingUserAction) return;
  const reason = document.getElementById('block-reason').value.trim();
  const errEl  = document.getElementById('user-modal-error');
  const btn    = document.getElementById('confirm-user-status');

  // Клієнтська валідація: причина обов'язкова (мін. 5 символів)
  if (!reason || reason.length < 5) {
    errEl.textContent = 'Введіть причину (мінімум 5 символів) — це обов\'язкове поле';
    errEl.classList.remove('hidden');
    document.getElementById('block-reason').focus();
    return;
  }

  errEl.classList.add('hidden');
  btn.disabled = true;

  try {
    await adminPatch(`/admin/users/${State.pendingUserId}/status`, {
      status: State.pendingUserAction,
      reason: reason,
    });
    const action = State.pendingUserAction === 'blocked' ? 'заблоковано' : 'розблоковано';
    AdminUI.toast(`Користувача ${action} ✓`, State.pendingUserAction === 'blocked' ? 'error' : 'success');
    closeUserModal();
    await loadUsers(State.usersPage);
    await refreshStats();
  } catch (err) {
    // Розбираємо помилку від FastAPI (може бути {detail: "..."} або масив помилок валідації)
    let msg = err.message || 'Невідома помилка';
    try {
      const parsed = JSON.parse(msg);
      if (parsed.detail) {
        msg = typeof parsed.detail === 'string'
          ? parsed.detail
          : parsed.detail.map(e => e.msg).join('; ');
      }
    } catch {}
    errEl.textContent = msg;
    errEl.classList.remove('hidden');
  } finally {
    btn.disabled = false;
  }
}

// ══════════════════════════════════════════════════════════════════
// SUSPICIOUS TRANSACTIONS
// ══════════════════════════════════════════════════════════════════
async function loadSuspicious(offset = 0) {
  State.suspiciousPage = offset;
  const container = document.getElementById('suspicious-list');
  container.innerHTML = '<div class="skeleton" style="height:100px;border-radius:12px;margin-bottom:12px"></div>'.repeat(3);

  try {
    const params = new URLSearchParams({ limit: State.suspiciousLimit, offset });
    if (State.suspiciousStatus) params.append('status', State.suspiciousStatus);

    const data = await adminGet(`/admin/suspicious?${params}`);
    State.suspiciousTotal = data.total;
    renderSuspiciousCards(data.items || [], 'suspicious-list', false);
    renderPagination('suspicious-pagination', data.total, State.suspiciousLimit, offset, loadSuspicious);
  } catch (err) {
    container.innerHTML = `<div class="empty-state">Помилка: ${err.message}</div>`;
  }
}

function renderSuspiciousCards(items, containerId, compact = false) {
  const container = document.getElementById(containerId);
  if (!items.length) {
    container.innerHTML = '<div class="empty-state">Підозрілих переказів не знайдено</div>';
    return;
  }
  container.innerHTML = '';
  items.forEach((tx, i) => {
    const card = buildSuspiciousCard(tx, compact);
    card.style.animationDelay = `${i * 50}ms`;
    container.appendChild(card);
  });
}

function buildSuspiciousCard(tx, compact = false) {
  const card = document.createElement('div');
  card.className = `suspicious-card suspicious-card--${tx.status}`;

  const statusLabels = {
    pending_review: '<span class="admin-section-badge admin-section-badge--amber">⏳ Очікує перевірки</span>',
    approved:       '<span class="admin-section-badge admin-section-badge--green">✓ Схвалено</span>',
    rejected:       '<span class="admin-section-badge admin-section-badge--red">✕ Відхилено</span>',
  };
  const sym = { UAH: '₴', USD: '$', EUR: '€' }[tx.currency] || '';

  card.innerHTML = `
    <div class="suspicious-card__icon">⚠️</div>
    <div>
      <div class="suspicious-card__amount">${sym}${Number(tx.amount).toLocaleString('uk-UA', { minimumFractionDigits: 2 })}</div>
      <div class="suspicious-card__meta">
        ${statusLabels[tx.status] || ''}
        <span style="font-size:.72rem;font-family:var(--font-mono);color:var(--silver)">${AdminUI.formatDate(tx.created_at)}</span>
      </div>
      <div class="suspicious-card__accounts">
        ↑ від: ···${tx.from_account_id.slice(-6)}
        → до: ···${(tx.to_account_id || '?').slice(-6)}
      </div>
      ${tx.description ? `<div style="font-size:.8rem;color:var(--silver);margin-top:6px">${escHtml(tx.description)}</div>` : ''}
      ${tx.review_comment ? `<div class="suspicious-card__comment">💬 Адмін: ${escHtml(tx.review_comment)}</div>` : ''}
    </div>
    <div class="suspicious-card__actions">
      ${tx.status === 'pending_review'
        ? `<button class="action-btn action-btn--success btn-review-tx">Розглянути</button>`
        : `<span style="font-size:.7rem;font-family:var(--font-mono);color:var(--silver)">${tx.reviewed_at ? AdminUI.formatDateShort(tx.reviewed_at) : ''}</span>`
      }
    </div>
  `;

  const btn = card.querySelector('.btn-review-tx');
  if (btn) btn.addEventListener('click', () => openReviewTxModal(tx));
  return card;
}

// ── Review Tx Modal ───────────────────────────────────────────────
function bindReviewTxModal() {
  document.getElementById('close-review-tx-modal').addEventListener('click', closeReviewTxModal);
  document.getElementById('modal-review-backdrop').addEventListener('click', e => {
    if (e.target === e.currentTarget) closeReviewTxModal();
  });
  document.getElementById('btn-approve-tx').addEventListener('click', () => submitTxReview('approve'));
  document.getElementById('btn-reject-tx').addEventListener('click',  () => submitTxReview('reject'));
}

function openReviewTxModal(tx) {
  State.pendingTxId = tx.id;
  const sym = { UAH: '₴', USD: '$', EUR: '€' }[tx.currency] || '';

  document.getElementById('review-tx-info').innerHTML = `
    <div class="review-row"><span class="review-row__label">Сума</span><span class="review-row__val review-row__val--big">${sym}${Number(tx.amount).toLocaleString('uk-UA', { minimumFractionDigits: 2 })}</span></div>
    <div class="review-row"><span class="review-row__label">Валюта</span><span class="review-row__val">${tx.currency}</span></div>
    <div class="review-row"><span class="review-row__label">Від рахунку</span><span class="review-row__val review-row__val--mono">···${tx.from_account_id.slice(-10)}</span></div>
    <div class="review-row"><span class="review-row__label">На рахунок</span><span class="review-row__val review-row__val--mono">···${(tx.to_account_id || '?').slice(-10)}</span></div>
    <div class="review-row"><span class="review-row__label">Дата</span><span class="review-row__val">${AdminUI.formatDate(tx.created_at)}</span></div>
    ${tx.description ? `<div class="review-row"><span class="review-row__label">Призначення</span><span class="review-row__val">${escHtml(tx.description)}</span></div>` : ''}
    <div class="review-row" style="margin-top:8px;padding-top:8px;border-top:1px solid var(--ink-3)">
      <span class="review-row__label" style="color:var(--amber)">⚠️ Увага</span>
      <span class="review-row__val" style="color:var(--amber);font-size:.82rem">
        При <strong>схваленні</strong> кошти будуть списані та зараховані.<br>
        При <strong>відхиленні</strong> кошти залишаться у відправника.
      </span>
    </div>
  `;

  document.getElementById('review-tx-comment').value = '';
  document.getElementById('review-tx-error').classList.add('hidden');
  document.getElementById('btn-approve-tx').disabled = false;
  document.getElementById('btn-reject-tx').disabled  = false;
  document.getElementById('modal-review-backdrop').classList.remove('hidden');
}

function closeReviewTxModal() {
  document.getElementById('modal-review-backdrop').classList.add('hidden');
  State.pendingTxId = null;
}

async function submitTxReview(action) {
  if (!State.pendingTxId) return;
  const comment    = document.getElementById('review-tx-comment').value.trim();
  const errEl      = document.getElementById('review-tx-error');
  const btnApprove = document.getElementById('btn-approve-tx');
  const btnReject  = document.getElementById('btn-reject-tx');
  errEl.classList.add('hidden');
  btnApprove.disabled = btnReject.disabled = true;

  try {
    await adminPatch(`/admin/suspicious/${State.pendingTxId}/review`, {
      action,
      comment: comment || undefined,
    });
    AdminUI.toast(
      action === 'approve' ? '✓ Переказ схвалено та виконано' : '✕ Переказ відхилено',
      action === 'approve' ? 'success' : 'error',
    );
    closeReviewTxModal();
    await loadSuspicious(State.suspiciousPage);
    await refreshStats();
  } catch (err) {
    errEl.textContent = typeof err.message === "string" ? err.message : JSON.stringify(err.message);
    errEl.classList.remove('hidden');
    btnApprove.disabled = btnReject.disabled = false;
  }
}

// ══════════════════════════════════════════════════════════════════
// REQUESTS
// ══════════════════════════════════════════════════════════════════
async function loadRequests(offset = 0) {
  State.requestsPage = offset;
  const container = document.getElementById('admin-requests-list');
  container.innerHTML = '<div class="skeleton" style="height:80px;border-radius:12px;margin-bottom:12px"></div>'.repeat(3);

  try {
    const params = new URLSearchParams({ limit: State.requestsLimit, offset });
    if (State.requestsStatus) params.append('status', State.requestsStatus);

    const data = await adminGet(`/admin/requests?${params}`);
    State.requestsTotal = data.total;
    renderRequestCards(data.items || [], 'admin-requests-list', false);
    renderPagination('requests-pagination', data.total, State.requestsLimit, offset, loadRequests);
  } catch (err) {
    container.innerHTML = `<div class="empty-state">Помилка: ${err.message}</div>`;
  }
}

function renderRequestCards(items, containerId, compact = false) {
  const container = document.getElementById(containerId);
  if (!items.length) {
    container.innerHTML = '<div class="empty-state">Запитів не знайдено</div>';
    return;
  }
  container.innerHTML = '';
  items.forEach((req, i) => {
    const card = buildRequestCard(req, compact);
    card.style.animationDelay = `${i * 40}ms`;
    container.appendChild(card);
  });
}

function buildRequestCard(req, compact = false) {
  const typeMap      = { BLOCK: 'BLOCK', UNBLOCK: 'UNBL', LIMIT_CHANGE: 'LIMIT' };
  const typeLabelMap = { BLOCK: 'Блокування', UNBLOCK: 'Розблокування', LIMIT_CHANGE: 'Зміна ліміту' };

  const card = document.createElement('div');
  card.className = `admin-request-card admin-request-card--${req.status}`;
  card.style.animation = 'fade-up .4s ease both';

  card.innerHTML = `
    <div class="admin-req__type">${typeMap[req.type] || req.type}</div>
    <div class="admin-req__body">
      <div class="admin-req__user">
        ${req.user_email ? `<span style="color:var(--gold-light)">${escHtml(req.user_email)}</span> · ` : ''}
        account: ···${req.account_id.slice(-8)}
      </div>
      <div style="font-size:.8rem;color:var(--mist);margin-bottom:4px">${typeLabelMap[req.type] || req.type}</div>
      <div class="admin-req__message">${escHtml(req.message)}</div>
      <div class="admin-req__meta">
        ${AdminUI.statusBadge(req.status)}
        <span class="admin-req__date">${AdminUI.formatDate(req.created_at)}</span>
      </div>
      ${req.admin_comment ? `<div class="admin-req__comment">💬 ${escHtml(req.admin_comment)}</div>` : ''}
    </div>
    <div class="admin-req__actions">
      ${req.status === 'pending'
        ? `<button class="action-btn action-btn--success btn-review-req">Розглянути</button>`
        : `<span style="font-size:.7rem;color:var(--silver);font-family:var(--font-mono)">${req.resolved_at ? AdminUI.formatDateShort(req.resolved_at) : ''}</span>`
      }
    </div>
  `;

  const btn = card.querySelector('.btn-review-req');
  if (btn) btn.addEventListener('click', () => openReviewRequestModal(req));
  return card;
}

// ── Review Request Modal ──────────────────────────────────────────
function bindReviewRequestModal() {
  document.getElementById('close-review-modal').addEventListener('click', closeReviewRequestModal);
  document.getElementById('admin-modal-backdrop').addEventListener('click', e => {
    if (e.target === e.currentTarget) closeReviewRequestModal();
  });
  document.getElementById('btn-approve').addEventListener('click', () => submitRequestReview('approved'));
  document.getElementById('btn-reject').addEventListener('click',  () => submitRequestReview('rejected'));
}

function openReviewRequestModal(req) {
  State.pendingRequestId = req.id;
  const typeLabelMap = { BLOCK: 'Блокування', UNBLOCK: 'Розблокування', LIMIT_CHANGE: 'Зміна ліміту' };

  document.getElementById('rv-type').textContent       = typeLabelMap[req.type] || req.type;
  document.getElementById('rv-account').textContent    = req.account_id;
  document.getElementById('rv-user-email').textContent = req.user_email || '—';
  document.getElementById('rv-message').textContent    = req.message;
  document.getElementById('rv-date').textContent       = AdminUI.formatDate(req.created_at);
  document.getElementById('rv-status').innerHTML       = AdminUI.statusBadge(req.status);
  document.getElementById('rv-comment').value          = req.admin_comment || '';
  document.getElementById('rv-error').classList.add('hidden');

  const isPending = req.status === 'pending';
  document.getElementById('btn-approve').disabled = !isPending;
  document.getElementById('btn-reject').disabled  = !isPending;

  document.getElementById('admin-modal-backdrop').classList.remove('hidden');
  document.getElementById('modal-review-request').classList.remove('hidden');
}

function closeReviewRequestModal() {
  document.getElementById('admin-modal-backdrop').classList.add('hidden');
  document.getElementById('modal-review-request').classList.add('hidden');
  State.pendingRequestId = null;
}

async function submitRequestReview(status) {
  if (!State.pendingRequestId) return;
  const comment    = document.getElementById('rv-comment').value.trim();
  const errEl      = document.getElementById('rv-error');
  const btnApprove = document.getElementById('btn-approve');
  const btnReject  = document.getElementById('btn-reject');
  errEl.classList.add('hidden');
  btnApprove.disabled = btnReject.disabled = true;

  try {
    await adminPatch(`/requests/${State.pendingRequestId}/status`, {
      status,
      admin_comment: comment || undefined,
    });
    AdminUI.toast(
      status === 'approved' ? '✓ Запит схвалено' : '✕ Запит відхилено',
      status === 'approved' ? 'success' : 'error',
    );
    closeReviewRequestModal();
    await loadRequests(State.requestsPage);
    await refreshStats();
  } catch (err) {
    errEl.textContent = typeof err.message === "string" ? err.message : JSON.stringify(err.message);
    errEl.classList.remove('hidden');
    btnApprove.disabled = btnReject.disabled = false;
  }
}

// ══════════════════════════════════════════════════════════════════
// HELPERS
// ══════════════════════════════════════════════════════════════════
async function refreshStats() {
  try {
    const stats = await adminGet('/admin/stats');
    State.stats = stats;
    setBadge('nav-badge-blocked',    stats.blocked_users);
    setBadge('nav-badge-suspicious', stats.pending_review_transactions);
    setBadge('nav-badge-requests',   stats.pending_requests);

    const overviewPage = document.getElementById('page-admin-overview');
    if (overviewPage && overviewPage.classList.contains('active')) {
      document.getElementById('stat-total-users').textContent      = stats.total_users;
      document.getElementById('stat-users-sub').textContent        = `${stats.active_users} активних / ${stats.blocked_users} заблоковано`;
      document.getElementById('stat-blocked-users').textContent    = stats.blocked_users;
      document.getElementById('stat-pending-review').textContent   = stats.pending_review_transactions;
      document.getElementById('stat-pending-requests').textContent = stats.pending_requests;
      document.getElementById('stat-total-accounts').textContent   = stats.total_accounts;
      document.getElementById('stat-total-tx').textContent         = stats.total_transactions;
    }
  } catch {}
}

function renderPagination(containerId, total, limit, currentOffset, loader) {
  const container = document.getElementById(containerId);
  if (!container) return;
  container.innerHTML = '';
  if (total <= limit) return;

  const totalPages = Math.ceil(total / limit);
  const curPage    = Math.floor(currentOffset / limit);

  const prev = document.createElement('button');
  prev.className = 'page-btn';
  prev.textContent = '←';
  prev.disabled = curPage === 0;
  prev.onclick = () => loader((curPage - 1) * limit);
  container.appendChild(prev);

  const maxBtns = Math.min(totalPages, 7);
  for (let i = 0; i < maxBtns; i++) {
    const btn = document.createElement('button');
    btn.className = `page-btn${i === curPage ? ' active' : ''}`;
    btn.textContent = i + 1;
    btn.onclick = () => loader(i * limit);
    container.appendChild(btn);
  }

  const next = document.createElement('button');
  next.className = 'page-btn';
  next.textContent = '→';
  next.disabled = curPage >= totalPages - 1;
  next.onclick = () => loader((curPage + 1) * limit);
  container.appendChild(next);
}

function escHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// ══════════════════════════════════════════════════════════════════
// USER DETAILS MODAL
// ══════════════════════════════════════════════════════════════════
let _detailsModal = null;

function openUserDetails(userId) {
  console.log('[openUserDetails] called with userId:', userId);

  // Видаляємо стару модалку якщо є (щоб уникнути дублювання)
  const existing = document.getElementById('modal-user-details-backdrop');
  if (existing) existing.remove();

  // Створюємо модалку з нуля
  const backdrop = document.createElement('div');
  backdrop.id = 'modal-user-details-backdrop';
  // НЕ використовуємо клас modal-backdrop щоб уникнути конфліктів з CSS
  // Встановлюємо всі стилі вручну
  backdrop.style.cssText = [
    'position:fixed',
    'inset:0',
    'background:rgba(0,0,0,.65)',
    'backdrop-filter:blur(4px)',
    'z-index:500',
    'display:flex',
    'align-items:flex-start',
    'justify-content:center',
    'padding:20px',
    'overflow-y:auto',
  ].join(';');

  backdrop.innerHTML = `
    <div id="modal-user-details" style="
      background:var(--ink-1);
      border:1px solid var(--ink-3);
      border-radius:var(--radius-lg);
      padding:32px;
      width:100%;
      max-width:720px;
      box-shadow:var(--shadow-modal);
      animation:modal-in .35s ease both;
      margin:auto;
      flex-shrink:0;
    ">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:24px;gap:12px">
        <h3 style="font-family:var(--font-display);font-size:1.5rem;font-weight:400;color:var(--white);flex:1">
          Деталі користувача
        </h3>
        <button id="close-user-details" style="
          background:transparent;border:1px solid var(--ink-3);
          color:var(--silver);font-size:1rem;cursor:pointer;
          padding:6px 12px;border-radius:var(--radius-sm);
          transition:all .12s;flex-shrink:0;
        ">✕ Закрити</button>
      </div>
      <div id="user-details-content">
        <div class="skeleton" style="height:80px;border-radius:8px;margin-bottom:12px"></div>
        <div class="skeleton" style="height:140px;border-radius:8px;margin-bottom:12px"></div>
        <div class="skeleton" style="height:200px;border-radius:8px"></div>
      </div>
    </div>
  `;

  document.body.appendChild(backdrop);
  document.body.style.overflow = 'hidden';

  document.getElementById('close-user-details').addEventListener('click', closeUserDetails);
  backdrop.addEventListener('click', e => {
    if (e.target === backdrop) closeUserDetails();
  });

  // Escape key closes modal
  const onEsc = (e) => { if (e.key === 'Escape') { closeUserDetails(); document.removeEventListener('keydown', onEsc); } };
  document.addEventListener('keydown', onEsc);

  _loadUserDetails(userId);
}

function closeUserDetails() {
  const backdrop = document.getElementById('modal-user-details-backdrop');
  if (backdrop) {
    backdrop.remove();
    document.body.style.overflow = '';
  }
}

async function _loadUserDetails(userId) {
  const content = document.getElementById('user-details-content');
  if (!content) {
    console.error('[Details] user-details-content not found in DOM');
    return;
  }
  content.innerHTML = `
    <div class="skeleton" style="height:80px;border-radius:8px;margin-bottom:12px"></div>
    <div class="skeleton" style="height:140px;border-radius:8px;margin-bottom:12px"></div>
    <div class="skeleton" style="height:220px;border-radius:8px"></div>
  `;

  console.log('[Details] loading user:', userId);

  try {
    const u = await adminGet('/admin/users/' + userId + '/details');
    console.log('[Details] received:', u);
    if (!u || !u.id) {
      throw new Error('Сервер повернув порожню відповідь');
    }
    _renderUserDetails(u);
  } catch (err) {
    console.error('[Details] error:', err);
    content.innerHTML = `
      <div style="padding:24px;text-align:center">
        <div style="font-size:2rem;margin-bottom:12px">⚠️</div>
        <div style="color:var(--red);margin-bottom:8px">${escHtml(err.message)}</div>
        <div style="font-size:.78rem;color:var(--silver)">
          Перевірте що ендпоінт <code style="font-family:var(--font-mono)">/admin/users/{id}/details</code> існує в backend
        </div>
        <button onclick="_loadUserDetails('${userId}')" class="btn btn--outline btn--sm" style="margin-top:16px">
          Спробувати ще раз
        </button>
      </div>
    `;
  }
}

function _renderUserDetails(u) {
  const content = document.getElementById('user-details-content');
  const isBlocked = u.status === 'blocked';
  const sym = { UAH: '₴', USD: '$', EUR: '€' };

  content.innerHTML = `
    <!-- Профіль -->
    <div style="background:var(--ink-2);border:1px solid var(--ink-3);border-radius:var(--radius-md);padding:20px;margin-bottom:16px">
      <div style="display:flex;align-items:center;gap:16px;margin-bottom:16px">
        <div style="
          width:52px;height:52px;border-radius:50%;
          background:linear-gradient(135deg,var(--gold),#b8942e);
          color:var(--ink);font-size:1.2rem;font-weight:600;
          display:flex;align-items:center;justify-content:center;
          text-transform:uppercase;flex-shrink:0
        ">${(u.first_name || 'U')[0]}</div>
        <div>
          <div style="font-size:1.1rem;font-weight:500;color:var(--white)">${escHtml(u.first_name)} ${escHtml(u.last_name)}</div>
          <div style="font-family:var(--font-mono);font-size:.8rem;color:var(--silver)">${escHtml(u.email)}</div>
          <div style="font-family:var(--font-mono);font-size:.75rem;color:var(--silver)">${escHtml(u.phone)}</div>
        </div>
        <div style="margin-left:auto;display:flex;flex-direction:column;align-items:flex-end;gap:6px">
          ${AdminUI.statusBadge(u.status)}
          <span class="badge ${u.role === 'ADMIN' ? 'badge--error' : 'badge--pending'}">${u.role}</span>
        </div>
      </div>
      ${isBlocked && u.block_reason ? `
        <div style="background:var(--red-dim);border:1px solid rgba(239,68,68,.25);border-radius:var(--radius-sm);padding:12px 14px">
          <div style="font-size:.68rem;letter-spacing:.08em;text-transform:uppercase;color:var(--red);margin-bottom:4px">Причина блокування</div>
          <div style="font-size:.87rem;color:var(--mist)">${escHtml(u.block_reason)}</div>
        </div>
      ` : ''}
      <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:14px">
        <div style="text-align:center;padding:10px;background:var(--ink-3);border-radius:var(--radius-sm)">
          <div style="font-size:1.3rem;font-family:var(--font-display);color:var(--white)">${u.accounts.length}</div>
          <div style="font-size:.7rem;color:var(--silver)">Рахунків</div>
        </div>
        <div style="text-align:center;padding:10px;background:var(--ink-3);border-radius:var(--radius-sm)">
          <div style="font-size:1.3rem;font-family:var(--font-display);color:var(--white)">${u.total_transactions}</div>
          <div style="font-size:.7rem;color:var(--silver)">Транзакцій</div>
        </div>
        <div style="text-align:center;padding:10px;background:var(--ink-3);border-radius:var(--radius-sm)">
          <div style="font-size:1.1rem;font-family:var(--font-display);color:var(--gold)">₴${Number(u.total_balance_uah).toLocaleString('uk-UA',{minimumFractionDigits:2})}</div>
          <div style="font-size:.7rem;color:var(--silver)">Баланс UAH</div>
        </div>
      </div>
      <div style="margin-top:14px;display:flex;gap:8px;justify-content:flex-end">
        ${u.id === currentAdminId ? '' : `
        <button
          id="details-toggle-status-btn"
          class="btn btn--sm ${isBlocked ? 'btn--outline' : 'btn--outline'}"
          style="${isBlocked ? 'border-color:var(--green);color:var(--green)' : 'border-color:var(--red);color:var(--red)'}"
          data-user-id="${u.id}" data-user-status="${u.status}"
          data-first="${escHtml(u.first_name)}" data-last="${escHtml(u.last_name)}"
          data-email="${escHtml(u.email)}" data-phone="${escHtml(u.phone)}"
          data-accounts="${u.accounts.length}"
        >
          ${isBlocked ? '🔓 Розблокувати користувача' : '🔒 Заблокувати користувача'}
        </button>`}
      </div>
    </div>

    <!-- Рахунки -->
    <div style="margin-bottom:16px">
      <div style="font-size:.7rem;letter-spacing:.1em;text-transform:uppercase;color:var(--silver);margin-bottom:10px">
        Рахунки (${u.accounts.length})
      </div>
      ${u.accounts.length === 0
        ? '<div class="empty-state" style="padding:20px">Рахунків немає</div>'
        : u.accounts.map(acc => `
          <div style="
            background:var(--ink-2);border:1px solid var(--ink-3);
            border-left:3px solid ${acc.status === 'blocked' ? 'var(--red)' : 'var(--green)'};
            border-radius:var(--radius-md);padding:14px 16px;margin-bottom:8px;
            display:flex;align-items:center;gap:12px
          ">
            <div style="flex:1;min-width:0">
              <div style="font-family:var(--font-mono);font-size:.82rem;color:var(--mist)">${escHtml(acc.card_number)}</div>
              <div style="font-size:.75rem;color:var(--silver);margin-top:2px">${acc.currency} · ${AdminUI.formatDateShort(acc.created_at)}</div>
            </div>
            <div style="font-family:var(--font-display);font-size:1.1rem;color:var(--white)">
              ${sym[acc.currency] || ''}${Number(acc.balance).toLocaleString('uk-UA',{minimumFractionDigits:2})}
            </div>
            ${AdminUI.statusBadge(acc.status)}
            <button
              class="action-btn ${acc.status === 'blocked' ? 'action-btn--success' : 'action-btn--danger'} btn-toggle-account"
              data-acc-id="${acc.id}"
              data-acc-status="${acc.status}"
              style="flex-shrink:0"
            >
              ${acc.status === 'blocked' ? '🔓' : '🔒'}
            </button>
          </div>
          ${acc.block_reason ? `<div style="margin-top:5px;font-size:.74rem;color:var(--red);padding:5px 10px;background:var(--red-dim);border-radius:4px">🔒 ${escHtml(acc.block_reason)}</div>` : ''}
        `).join('')
      }
    </div>

    <!-- Транзакції -->
    <div>
      <div style="font-size:.7rem;letter-spacing:.1em;text-transform:uppercase;color:var(--silver);margin-bottom:10px">
        Останні транзакції (${u.recent_transactions.length} з ${u.total_transactions})
      </div>
      ${u.recent_transactions.length === 0
        ? '<div class="empty-state" style="padding:20px">Транзакцій немає</div>'
        : `<div style="background:var(--ink-2);border:1px solid var(--ink-3);border-radius:var(--radius-md);overflow:hidden">
            <table style="width:100%;border-collapse:collapse;font-size:.82rem">
              <thead>
                <tr style="background:var(--ink-3)">
                  <th style="padding:10px 14px;text-align:left;color:var(--silver);font-weight:500;font-size:.68rem;letter-spacing:.07em;text-transform:uppercase">Дата</th>
                  <th style="padding:10px 14px;text-align:left;color:var(--silver);font-weight:500;font-size:.68rem;letter-spacing:.07em;text-transform:uppercase">Сума</th>
                  <th style="padding:10px 14px;text-align:left;color:var(--silver);font-weight:500;font-size:.68rem;letter-spacing:.07em;text-transform:uppercase">Статус</th>
                  <th style="padding:10px 14px;text-align:left;color:var(--silver);font-weight:500;font-size:.68rem;letter-spacing:.07em;text-transform:uppercase">Опис</th>
                </tr>
              </thead>
              <tbody>
                ${u.recent_transactions.map(tx => `
                  <tr style="border-top:1px solid var(--ink-3)">
                    <td style="padding:10px 14px;font-family:var(--font-mono);font-size:.72rem;color:var(--silver);white-space:nowrap">${AdminUI.formatDateShort(tx.created_at)}</td>
                    <td style="padding:10px 14px;font-family:var(--font-mono);font-weight:500;color:${tx.is_suspicious ? 'var(--amber)' : 'var(--mist)'}">
                      ${sym[tx.currency] || ''}${Number(tx.amount).toLocaleString('uk-UA',{minimumFractionDigits:2})}
                      ${tx.is_suspicious ? ' ⚠️' : ''}
                    </td>
                    <td style="padding:10px 14px">${AdminUI.statusBadge(tx.status)}</td>
                    <td style="padding:10px 14px;color:var(--silver);max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${escHtml(tx.description || tx.type)}</td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>`
      }
    </div>
  `;

  // Bind toggle user status button
  const toggleBtn = document.getElementById('details-toggle-status-btn');
  if (toggleBtn) {
    toggleBtn.addEventListener('click', () => {
      const fakeUser = {
        id:           toggleBtn.dataset.userId,
        status:       toggleBtn.dataset.userStatus,
        first_name:   toggleBtn.dataset.first,
        last_name:    toggleBtn.dataset.last,
        email:        toggleBtn.dataset.email,
        phone:        toggleBtn.dataset.phone,
        accounts_count: parseInt(toggleBtn.dataset.accounts) || 0,
      };
      closeUserDetails();
      openUserStatusModal(fakeUser);
    });
  }

  // Bind account toggle buttons
  content.querySelectorAll('.btn-toggle-account').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.stopPropagation();
      const accId     = btn.dataset.accId;
      const accStatus = btn.dataset.accStatus;
      const newStatus = accStatus === 'active' ? 'blocked' : 'active';

      if (newStatus === 'blocked') {
        // Відкриваємо власну красиву модалку замість prompt()
        _openAccountBlockModal(accId, u.id);
      } else {
        // Розблокування — одразу без модалки
        btn.disabled = true;
        try {
          await adminPatch('/admin/accounts/' + accId + '/status', { status: 'active' });
          AdminUI.toast('🔓 Рахунок розблоковано', 'success');
          await _loadUserDetails(u.id);
        } catch (err) {
          AdminUI.toast('Помилка: ' + err.message, 'error');
          btn.disabled = false;
        }
      }
    });
  });
}

// ══════════════════════════════════════════════════════════════════
// ACCOUNT BLOCK MODAL
// Власна модалка для блокування рахунку з полем причини
// ══════════════════════════════════════════════════════════════════

let _accBlockAccId  = null;
let _accBlockUserId = null;

function _openAccountBlockModal(accId, userId) {
  _accBlockAccId  = accId;
  _accBlockUserId = userId;

  // Видаляємо стару якщо є
  const old = document.getElementById('modal-acc-block-backdrop');
  if (old) old.remove();

  const backdrop = document.createElement('div');
  backdrop.id = 'modal-acc-block-backdrop';
  backdrop.style.cssText = [
    'position:fixed', 'inset:0',
    'background:rgba(0,0,0,.7)',
    'backdrop-filter:blur(4px)',
    'z-index:600',
    'display:flex',
    'align-items:center',
    'justify-content:center',
    'padding:20px',
  ].join(';');

  backdrop.innerHTML = `
    <div style="
      background:var(--ink-1);
      border:1px solid rgba(239,68,68,.3);
      border-top:3px solid var(--red);
      border-radius:var(--radius-lg);
      padding:28px;
      width:100%;
      max-width:420px;
      box-shadow:var(--shadow-modal);
      animation:modal-in .3s ease both;
    ">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:20px">
        <h3 style="font-family:var(--font-display);font-size:1.4rem;font-weight:400;color:var(--white)">
          🔒 Блокування рахунку
        </h3>
        <button id="acc-block-close" style="
          background:transparent;border:none;color:var(--silver);
          font-size:1.1rem;cursor:pointer;padding:4px 8px;
          border-radius:var(--radius-sm)
        ">✕</button>
      </div>

      <div style="
        background:var(--red-dim);border:1px solid rgba(239,68,68,.2);
        border-radius:var(--radius-sm);padding:12px 14px;margin-bottom:18px;
        font-size:.82rem;color:var(--mist);
      ">
        Рахунок <code style="font-family:var(--font-mono);color:var(--red)">···${accId.slice(-8)}</code>
        буде заблоковано. Власник не зможе проводити операції.
      </div>

      <div style="margin-bottom:16px">
        <label style="
          display:block;font-size:.72rem;letter-spacing:.08em;
          text-transform:uppercase;color:var(--silver);margin-bottom:6px
        ">
          Причина блокування
          <span style="color:var(--silver);font-weight:400;text-transform:none;letter-spacing:0">
            (необов'язково)
          </span>
        </label>
        <textarea
          id="acc-block-reason"
          style="
            width:100%;background:var(--ink-2);border:1px solid var(--ink-3);
            border-radius:var(--radius-sm);color:var(--white);
            padding:10px 14px;font-family:inherit;font-size:.87rem;
            resize:vertical;min-height:72px;outline:none;
            transition:border-color .12s;
          "
          placeholder="Наприклад: підозрілі транзакції, запит власника..."
          maxlength="500"
          onfocus="this.style.borderColor='var(--red)'"
          onblur="this.style.borderColor='var(--ink-3)'"
        ></textarea>
        <div style="font-size:.7rem;color:var(--silver);margin-top:4px">
          Причина буде збережена і показана власнику рахунку
        </div>
      </div>

      <div id="acc-block-error" style="
        display:none;background:var(--red-dim);border:1px solid rgba(239,68,68,.25);
        border-radius:var(--radius-sm);padding:10px 14px;
        font-size:.83rem;color:#fca5a5;margin-bottom:12px
      "></div>

      <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
        <button id="acc-block-cancel" style="
          background:transparent;border:1px solid var(--ink-3);
          color:var(--mist);padding:10px 20px;border-radius:var(--radius-sm);
          font-family:inherit;font-size:.875rem;cursor:pointer;
          transition:all .15s;
        ">Скасувати</button>
        <button id="acc-block-confirm" style="
          background:linear-gradient(135deg,var(--red),#b91c1c);
          border:none;color:#fff;padding:10px 20px;
          border-radius:var(--radius-sm);font-family:inherit;
          font-size:.875rem;font-weight:500;cursor:pointer;
          transition:all .15s;
        ">🔒 Заблокувати</button>
      </div>
    </div>
  `;

  document.body.appendChild(backdrop);
  document.body.style.overflow = 'hidden';

  // Focus на textarea
  setTimeout(() => document.getElementById('acc-block-reason')?.focus(), 100);

  // Events
  document.getElementById('acc-block-close').addEventListener('click', _closeAccountBlockModal);
  document.getElementById('acc-block-cancel').addEventListener('click', _closeAccountBlockModal);
  backdrop.addEventListener('click', e => { if (e.target === backdrop) _closeAccountBlockModal(); });

  document.getElementById('acc-block-confirm').addEventListener('click', async () => {
    const reason  = (document.getElementById('acc-block-reason').value || '').trim() || null;
    const errEl   = document.getElementById('acc-block-error');
    const confirmBtn = document.getElementById('acc-block-confirm');

    errEl.style.display = 'none';
    confirmBtn.disabled = true;
    confirmBtn.textContent = 'Блокування...';

    try {
      await adminPatch('/admin/accounts/' + _accBlockAccId + '/status', {
        status: 'blocked',
        ...(reason ? { reason } : {}),
      });
      AdminUI.toast('🔒 Рахунок заблоковано', 'error');
      _closeAccountBlockModal();
      if (_accBlockUserId) await _loadUserDetails(_accBlockUserId);
    } catch (err) {
      errEl.textContent = err.message;
      errEl.style.display = 'block';
      confirmBtn.disabled = false;
      confirmBtn.textContent = '🔒 Заблокувати';
    }
  });

  // Escape key
  const onEsc = e => {
    if (e.key === 'Escape') { _closeAccountBlockModal(); document.removeEventListener('keydown', onEsc); }
  };
  document.addEventListener('keydown', onEsc);
}

function _closeAccountBlockModal() {
  const backdrop = document.getElementById('modal-acc-block-backdrop');
  if (backdrop) { backdrop.remove(); document.body.style.overflow = ''; }
  _accBlockAccId  = null;
  _accBlockUserId = null;
}