/**
 * admin.js — Панель адміністратора Vault
 */

const API = 'http://localhost:8000';

/* ═══════════════════════════════════════════════════════════════════════════
   ХЕЛПЕРИ UI
   ══════════════════════════════════════════════════════════════════════════ */

const AdminUI = {
  formatDate(dateStr) {
    if (!dateStr) return '—';
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString('uk-UA', { day: '2-digit', month: 'short', year: 'numeric' })
        + ' ' + d.toLocaleTimeString('uk-UA', { hour: '2-digit', minute: '2-digit' });
    } catch { return String(dateStr); }
  },

  formatDateShort(dateStr) {
    if (!dateStr) return '—';
    try {
      return new Date(dateStr).toLocaleDateString('uk-UA', { day: '2-digit', month: 'short', year: 'numeric' });
    } catch { return String(dateStr); }
  },

  statusBadge(status) {
    const MAP = {
      success:  ['success', 'Успішно'],
      active:   ['success', 'Активний'],
      blocked:  ['error',   'Заблоковано'],
      pending:  ['pending', 'Очікує'],
      approved: ['success', 'Схвалено'],
      rejected: ['error',   'Відхилено'],
    };
    const [cls, label] = MAP[String(status)] || ['pending', String(status || '—')];
    return `<span class="badge badge--${cls}">${label}</span>`;
  },

  toast(message, type = 'info', duration = 3500) {
    const ct = document.getElementById('toast-container');
    if (!ct) return;
    const el = document.createElement('div');
    el.className = `toast toast--${type}`;
    const icons = { success: '✓', error: '✕', info: '◆' };
    const color = type === 'success' ? 'var(--green)' : type === 'error' ? 'var(--red)' : 'var(--gold)';
    el.innerHTML = `<span style="color:${color}">${icons[type] || '◆'}</span><span>${esc(String(message))}</span>`;
    ct.appendChild(el);
    setTimeout(() => {
      el.style.animation = 'toast-out .25s ease forwards';
      el.addEventListener('animationend', () => el.remove(), { once: true });
    }, duration);
  },
};

/* ═══════════════════════════════════════════════════════════════════════════
   ОТРИМАННЯ ТЕКСТУ ПОМИЛКИ
   Обробляє будь-який тип: Error, string, {detail:...}, {message:...}
   ══════════════════════════════════════════════════════════════════════════ */

function errMsg(err) {
  if (!err) return 'Невідома помилка';
  if (typeof err === 'string') return err;
  if (err instanceof Error) return err.message || String(err);
  if (typeof err === 'object') {
    if (err.detail) {
      return Array.isArray(err.detail)
        ? err.detail.map(e => e.msg || JSON.stringify(e)).join('; ')
        : String(err.detail);
    }
    if (err.message) return String(err.message);
    try { return JSON.stringify(err); } catch { return '[object Object]'; }
  }
  return String(err);
}

/* ═══════════════════════════════════════════════════════════════════════════
   HTTP
   ══════════════════════════════════════════════════════════════════════════ */

async function apiFetch(path, options = {}) {
  const token = Store.get('accessToken');
  const headers = { 'Content-Type': 'application/json', ...options.headers };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  let res;
  try {
    res = await fetch(`${API}${path}`, { ...options, headers });
  } catch {
    throw new Error('Сервер недоступний. Перевірте підключення.');
  }

  if (res.status === 401) {
    const refreshed = await tryRefresh();
    if (refreshed) return apiFetch(path, options);
    showGuard();
    throw new Error('Сесія закінчилась. Увійдіть знову.');
  }

  if (res.status === 204) return null;

  let body;
  try { body = await res.json(); } catch { body = {}; }

  if (!res.ok) {
    // Pydantic може повернути масив або рядок у detail
    let detail = body?.detail;
    if (Array.isArray(detail)) {
      detail = detail.map(e => e.msg || JSON.stringify(e)).join('; ');
    }
    throw new Error(detail || `HTTP ${res.status}`);
  }

  return body;
}

async function tryRefresh() {
  const rt = Store.get('refreshToken');
  if (!rt) return false;
  try {
    const data = await fetch(`${API}/users/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: rt }),
    }).then(r => r.json());
    if (data.access_token) { Store.set('accessToken', data.access_token); return true; }
  } catch {}
  return false;
}

const adminGet   = (path)       => apiFetch(path, { method: 'GET' });
const adminPatch = (path, body) => apiFetch(path, { method: 'PATCH', body: JSON.stringify(body) });
const adminPost  = (path, body) => apiFetch(path, { method: 'POST',  body: JSON.stringify(body) });

/* ═══════════════════════════════════════════════════════════════════════════
   СТАН
   ══════════════════════════════════════════════════════════════════════════ */

let _allRequests  = [];
let _allUsers     = [];
let _reviewingReq = null;

/* ═══════════════════════════════════════════════════════════════════════════
   BOOT
   ══════════════════════════════════════════════════════════════════════════ */

(async function boot() {
  if (!Store.isLoggedIn()) {
    const ok = await tryRefresh();
    if (!ok) { showGuard(); return; }
  }

  let user;
  try {
    user = await adminGet('/users/me');
    if (!user) { showGuard(); return; }
    Store.setUser(user);
  } catch (err) {
    console.error('Auth error:', errMsg(err));
    showGuard();
    return;
  }

  if (user.role !== 'ADMIN') { showGuard(); return; }

  document.getElementById('admin-email').textContent  = user.email;
  document.getElementById('admin-avatar').textContent = user.email[0].toUpperCase();

  // Навігація
  document.querySelectorAll('[data-page]').forEach(el => {
    el.addEventListener('click', e => { e.preventDefault(); navigateTo(el.dataset.page); });
  });

  // Вихід
  async function doLogout() {
    try { await adminPost('/users/logout', { refresh_token: Store.get('refreshToken') }); } catch {}
    Store.clear();
    window.location.href = 'index.html';
  }
  document.getElementById('admin-btn-logout')?.addEventListener('click', doLogout);
  document.getElementById('topbar-btn-logout')?.addEventListener('click', doLogout);

  // Модальне вікно
  document.getElementById('close-review-modal').addEventListener('click', closeReviewModal);
  document.getElementById('admin-modal-backdrop').addEventListener('click', e => {
    if (e.target === e.currentTarget) closeReviewModal();
  });
  document.getElementById('btn-approve').addEventListener('click', () => submitReview('approved'));
  document.getElementById('btn-reject').addEventListener('click',  () => submitReview('rejected'));

  // Фільтри
  document.getElementById('user-search').addEventListener('input', debounce(filterUsers, 280));
  document.getElementById('req-status-filter').addEventListener('change', renderFilteredRequests);

  document.getElementById('view-all-requests')?.addEventListener('click', e => {
    e.preventDefault();
    navigateTo('admin-requests');
  });

  // Мобільний sidebar
  const burger  = document.getElementById('sidebar-toggle');
  const sidebar = document.querySelector('.sidebar');
  const overlay = document.getElementById('sidebar-overlay');
  burger?.addEventListener('click', () => {
    const open = sidebar.classList.toggle('open');
    overlay.classList.toggle('visible', open);
    burger.classList.toggle('open', open);
  });
  overlay?.addEventListener('click', () => {
    sidebar.classList.remove('open');
    overlay.classList.remove('visible');
    burger?.classList.remove('open');
  });

  await loadOverview();
})();

function showGuard() {
  document.getElementById('admin-auth-guard').classList.remove('hidden');
  document.getElementById('admin-app').style.visibility = 'hidden';
}

/* ═══════════════════════════════════════════════════════════════════════════
   РОУТИНГ
   ══════════════════════════════════════════════════════════════════════════ */

const PAGE_TITLES = {
  'admin-overview': 'Панель адміністратора',
  'admin-users':    'Управління користувачами',
  'admin-requests': 'Запити користувачів',
};
const PAGE_LOADERS = {
  'admin-overview': loadOverview,
  'admin-users':    loadUsers,
  'admin-requests': loadAllRequests,
};

function navigateTo(pageId) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.getElementById(`page-${pageId}`)?.classList.add('active');
  document.querySelector(`[data-page="${pageId}"]`)?.classList.add('active');
  document.getElementById('admin-page-title').textContent = PAGE_TITLES[pageId] || pageId;
  PAGE_LOADERS[pageId]?.();
}

/* ═══════════════════════════════════════════════════════════════════════════
   ОГЛЯД
   ══════════════════════════════════════════════════════════════════════════ */

async function loadOverview() {
  setStat('stat-users-total',    '…');
  setStat('stat-pending-reqs',   '…');
  setStat('stat-approved-today', '…');

  // Promise.allSettled — один упавший endpoint не блокирует другой
  const [reqResult, usersResult] = await Promise.allSettled([
    adminGet('/requests/?limit=100'),
    adminGet('/users/?limit=100'),
  ]);

  _allRequests = (reqResult.status === 'fulfilled' && Array.isArray(reqResult.value))
    ? reqResult.value : [];

  _allUsers = (usersResult.status === 'fulfilled' && Array.isArray(usersResult.value))
    ? usersResult.value : [];

  if (reqResult.status === 'rejected') {
    console.warn('GET /requests/ failed:', errMsg(reqResult.reason));
  }
  if (usersResult.status === 'rejected') {
    console.warn('GET /users/ failed:', errMsg(usersResult.reason));
  }

  const pending  = _allRequests.filter(r => r.status === 'pending').length;
  const today    = new Date().toDateString();
  const approved = _allRequests.filter(r =>
    r.status === 'approved' && r.resolved_at &&
    new Date(r.resolved_at).toDateString() === today
  ).length;

  setStat('stat-users-total',    _allUsers.length);
  setStat('stat-pending-reqs',   pending);
  setStat('stat-approved-today', approved);

  updateBadge();
  renderRecentRequests(_allRequests.slice(0, 5));

  // Підказка якщо endpoint-и не знайдені
  if (reqResult.status === 'rejected' || usersResult.status === 'rejected') {
    const failedEndpoints = [
      reqResult.status === 'rejected'   && 'GET /requests/',
      usersResult.status === 'rejected' && 'GET /users/',
    ].filter(Boolean).join(', ');

    AdminUI.toast(
      `Бекенд не повертає дані для: ${failedEndpoints}. Перевірте чи додані нові ендпоінти.`,
      'error', 8000,
    );
  }
}

function setStat(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

function renderRecentRequests(requests) {
  const container = document.getElementById('admin-recent-requests');
  if (!container) return;
  container.innerHTML = '';
  if (!requests.length) {
    container.innerHTML = '<div class="empty-state">Запитів ще немає</div>';
    return;
  }
  requests.forEach((req, i) => {
    const card = buildRequestCard(req);
    card.style.setProperty('--i', i);
    container.appendChild(card);
  });
}

/* ═══════════════════════════════════════════════════════════════════════════
   КОРИСТУВАЧІ
   ══════════════════════════════════════════════════════════════════════════ */

async function loadUsers() {
  const tbody = document.getElementById('users-table-body');
  tbody.innerHTML = `<tr><td colspan="6" class="skeleton" style="height:60px;display:table-cell"></td></tr>`;

  try {
    const data = await adminGet('/users/?limit=100');
    _allUsers = Array.isArray(data) ? data : [];
    renderUsersTable(_allUsers);
  } catch (err) {
    const msg = errMsg(err);
    console.error('loadUsers:', msg);
    tbody.innerHTML = `<tr><td colspan="6" class="empty-state" style="color:var(--red)">
      Помилка: ${esc(msg)}
    </td></tr>`;
  }
}

function renderUsersTable(users) {
  const tbody = document.getElementById('users-table-body');
  if (!users.length) {
    tbody.innerHTML = '<tr><td colspan="6" class="empty-state">Користувачів не знайдено</td></tr>';
    return;
  }
  tbody.innerHTML = '';
  users.forEach(u => {
    const isAdmin = u.role === 'ADMIN';
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td style="font-family:var(--font-mono);font-size:.82rem">${esc(u.email)}</td>
      <td style="font-family:var(--font-mono);font-size:.8rem;color:var(--silver)">${esc(u.phone || '—')}</td>
      <td><span class="badge ${isAdmin ? 'badge--error' : 'badge--pending'}">${esc(u.role)}</span></td>
      <td>${AdminUI.statusBadge(u.status)}</td>
      <td class="tx-date-cell">${AdminUI.formatDateShort(u.created_at)}</td>
      <td>
        <div class="action-btns">
          ${isAdmin
            ? `<span style="font-size:.72rem;color:var(--silver);font-family:var(--font-mono)">—</span>`
            : `<button class="action-btn ${u.status === 'active' ? 'action-btn--danger' : 'action-btn--success'}"
                       data-uid="${esc(u.id)}" data-status="${esc(u.status)}">
                 ${u.status === 'active' ? 'Заблокувати' : 'Розблокувати'}
               </button>`
          }
        </div>
      </td>
    `;

    if (!isAdmin) {
      tr.querySelector('[data-uid]')?.addEventListener('click', async function () {
        const btn       = this;
        const uid       = btn.dataset.uid;
        const curStatus = btn.dataset.status;
        const newStatus = curStatus === 'active' ? 'blocked' : 'active';
        btn.disabled    = true;
        btn.textContent = '…';
        try {
          await adminPatch(`/users/${uid}`, { status: newStatus });
          const idx = _allUsers.findIndex(x => x.id === uid);
          if (idx !== -1) _allUsers[idx].status = newStatus;
          renderUsersTable(_allUsers);
          AdminUI.toast(`Статус оновлено: ${newStatus}`, 'success');
        } catch (err) {
          AdminUI.toast('Помилка: ' + errMsg(err), 'error');
          btn.disabled    = false;
          btn.textContent = curStatus === 'active' ? 'Заблокувати' : 'Розблокувати';
        }
      });
    }
    tbody.appendChild(tr);
  });
}

function filterUsers(e) {
  const term = e.target.value.toLowerCase();
  renderUsersTable(
    _allUsers.filter(u =>
      u.email.toLowerCase().includes(term) || (u.phone || '').includes(term)
    )
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   ЗАПИТИ
   ══════════════════════════════════════════════════════════════════════════ */

async function loadAllRequests() {
  const container = document.getElementById('admin-requests-list');
  container.innerHTML = `<div class="skeleton" style="height:120px;border-radius:12px"></div>`;

  try {
    const data = await adminGet('/requests/?limit=100');
    _allRequests = Array.isArray(data) ? data : [];
    renderFilteredRequests();
    updateBadge();
  } catch (err) {
    const msg = errMsg(err);
    console.error('loadAllRequests:', msg);
    container.innerHTML = `<div class="empty-state" style="color:var(--red)">Помилка: ${esc(msg)}</div>`;
  }
}

function renderFilteredRequests() {
  const filter    = document.getElementById('req-status-filter')?.value || '';
  const container = document.getElementById('admin-requests-list');
  if (!container) return;
  const list = filter ? _allRequests.filter(r => r.status === filter) : _allRequests;
  container.innerHTML = '';
  if (!list.length) {
    container.innerHTML = '<div class="empty-state">Запитів не знайдено</div>';
    return;
  }
  list.forEach((req, i) => {
    const card = buildRequestCard(req);
    card.style.setProperty('--i', i);
    container.appendChild(card);
  });
}

function updateBadge() {
  const pending = _allRequests.filter(r => r.status === 'pending').length;
  const badge   = document.getElementById('nav-requests-badge');
  if (badge) badge.textContent = pending > 0 ? String(pending) : '';
}

/* ── Картка запиту ───────────────────────────────────────────────────────── */

function buildRequestCard(req) {
  const TYPE_SHORT = { BLOCK: 'BLOCK', UNBLOCK: 'UNBL', LIMIT_CHANGE: 'LIMIT' };
  const TYPE_LABEL = { BLOCK: 'Блокування', UNBLOCK: 'Розблокування', LIMIT_CHANGE: 'Зміна ліміту' };
  const userEmail  = _allUsers.find(u => u.id === req.user_id)?.email || req.user_id || '—';

  const card = document.createElement('div');
  card.className = `admin-request-card admin-request-card--${req.status}`;
  card.innerHTML = `
    <div class="admin-req__type">${esc(TYPE_SHORT[req.type] || req.type)}</div>
    <div class="admin-req__body">
      <div class="admin-req__user">
        <span style="color:var(--gold);font-size:.7rem;font-family:var(--font-mono)">${esc(TYPE_LABEL[req.type] || req.type)}</span>
        &nbsp;·&nbsp;
        <span style="font-size:.78rem">${esc(userEmail)}</span>
      </div>
      <div style="font-size:.7rem;color:var(--silver);font-family:var(--font-mono);margin-bottom:6px;word-break:break-all">
        ${esc(req.account_id || '—')}
      </div>
      <div class="admin-req__message">${esc(req.message || '')}</div>
      <div class="admin-req__meta">
        ${AdminUI.statusBadge(req.status)}
        <span class="admin-req__date">${AdminUI.formatDate(req.created_at)}</span>
        ${req.resolved_at ? `<span class="admin-req__date" style="color:var(--silver)">→ ${AdminUI.formatDate(req.resolved_at)}</span>` : ''}
      </div>
      ${req.admin_comment ? `<div class="admin-req__comment">💬 ${esc(req.admin_comment)}</div>` : ''}
    </div>
    <div class="admin-req__actions">
      ${req.status === 'pending'
        ? `<button class="action-btn action-btn--success review-btn">Розглянути</button>`
        : `<span style="font-size:.72rem;font-family:var(--font-mono);color:var(--silver)">
             ${req.status === 'approved' ? '✓ Схвалено' : '✕ Відхилено'}
           </span>`}
    </div>
  `;
  card.querySelector('.review-btn')?.addEventListener('click', () => openReviewModal(req));
  return card;
}

/* ═══════════════════════════════════════════════════════════════════════════
   МОДАЛЬНЕ ВІКНО
   ══════════════════════════════════════════════════════════════════════════ */

function openReviewModal(req) {
  _reviewingReq = req;
  const TYPE_LABEL = { BLOCK: 'Блокування', UNBLOCK: 'Розблокування', LIMIT_CHANGE: 'Зміна ліміту' };
  const userEmail  = _allUsers.find(u => u.id === req.user_id)?.email || req.user_id || '—';

  document.getElementById('rv-type').textContent    = TYPE_LABEL[req.type] || req.type;
  document.getElementById('rv-user').textContent    = userEmail;
  document.getElementById('rv-account').textContent = req.account_id || '—';
  document.getElementById('rv-message').textContent = req.message    || '—';
  document.getElementById('rv-date').textContent    = AdminUI.formatDate(req.created_at);
  document.getElementById('rv-status').innerHTML    = AdminUI.statusBadge(req.status);
  document.getElementById('rv-comment').value       = req.admin_comment || '';
  document.getElementById('rv-error').classList.add('hidden');

  const isPending = req.status === 'pending';
  document.getElementById('btn-approve').disabled = !isPending;
  document.getElementById('btn-reject').disabled  = !isPending;

  document.getElementById('admin-modal-backdrop').classList.remove('hidden');
  document.getElementById('modal-review-request').classList.remove('hidden');
}

function closeReviewModal() {
  document.getElementById('admin-modal-backdrop').classList.add('hidden');
  document.getElementById('modal-review-request').classList.add('hidden');
  _reviewingReq = null;
}

async function submitReview(status) {
  if (!_reviewingReq) return;

  const comment    = document.getElementById('rv-comment').value.trim();
  const errEl      = document.getElementById('rv-error');
  const btnApprove = document.getElementById('btn-approve');
  const btnReject  = document.getElementById('btn-reject');

  errEl.classList.add('hidden');
  btnApprove.disabled = btnReject.disabled = true;

  try {
    const updated = await adminPatch(`/requests/${_reviewingReq.id}/status`, {
      status,
      admin_comment: comment || undefined,
    });

    const idx = _allRequests.findIndex(r => r.id === _reviewingReq.id);
    if (idx !== -1 && updated) _allRequests[idx] = updated;

    closeReviewModal();
    AdminUI.toast(
      status === 'approved' ? '✓ Запит схвалено — статус рахунку оновлено' : '✕ Запит відхилено',
      status === 'approved' ? 'success' : 'error',
    );

    updateBadge();
    renderFilteredRequests();
    renderRecentRequests(_allRequests.slice(0, 5));

    const pending  = _allRequests.filter(r => r.status === 'pending').length;
    const today    = new Date().toDateString();
    const approved = _allRequests.filter(r =>
      r.status === 'approved' && r.resolved_at &&
      new Date(r.resolved_at).toDateString() === today
    ).length;
    setStat('stat-pending-reqs',   pending);
    setStat('stat-approved-today', approved);

  } catch (err) {
    errEl.textContent = errMsg(err);
    errEl.classList.remove('hidden');
    btnApprove.disabled = btnReject.disabled = false;
  }
}

/* ═══════════════════════════════════════════════════════════════════════════
   УТИЛІТИ
   ══════════════════════════════════════════════════════════════════════════ */

function debounce(fn, ms) {
  let t;
  return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); };
}

function esc(str) {
  return String(str ?? '')
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
