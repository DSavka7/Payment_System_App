
/* ── API extensions for admin ────────────────────────────────────────────────
   Admin uses the same API base but hits endpoints that require ADMIN role.    */
const AdminApi = {
  getUser:          (id)           => Api.getMe(),          // reuse base
  updateUser:       (id, data)     => _adminPatch(`/users/${id}`, data),
  deleteUser:       (id)           => _adminDel(`/users/${id}`),
  getRequests:      (userId)       => Api.getUserRequests(userId),
  updateReqStatus:  (id, payload)  => _adminPatch(`/requests/${id}/status`, payload),
};

async function _adminPatch(path, body) {
  const token = Store.get('accessToken');
  const res = await fetch(`http://localhost:8000${path}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: JSON.stringify(body),
  });
  if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || `HTTP ${res.status}`); }
  return res.status === 204 ? null : res.json();
}

async function _adminDel(path) {
  const token = Store.get('accessToken');
  const res = await fetch(`http://localhost:8000${path}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || `HTTP ${res.status}`); }
  return null;
}

/* ═══════════════════════════════════════════════════════════════════════════
   STATE
   ══════════════════════════════════════════════════════════════════════════ */
let _allRequests = [];
let _pendingReviewId = null;

/* ═══════════════════════════════════════════════════════════════════════════
   BOOT
   ══════════════════════════════════════════════════════════════════════════ */
(async function boot() {
  // Check auth + role
  if (!Store.isLoggedIn()) {
    try {
      const rt = Store.get('refreshToken');
      if (!rt) throw new Error('no token');
      const res = await fetch('http://localhost:8000/users/refresh', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: rt }),
      });
      const data = await res.json();
      Store.set('accessToken', data.access_token);
    } catch {
      showGuard(); return;
    }
  }

  try {
    const user = await Api.getMe();
    Store.setUser(user);
    if (user.role !== 'ADMIN') { showGuard(); return; }

    document.getElementById('admin-email').textContent  = user.email;
    document.getElementById('admin-avatar').textContent = user.email[0].toUpperCase();
  } catch {
    showGuard(); return;
  }

  // Wire navigation
  document.querySelectorAll('[data-page]').forEach(el => {
    el.addEventListener('click', (e) => { e.preventDefault(); navigateTo(el.dataset.page); });
  });

  document.getElementById('admin-btn-logout').addEventListener('click', async () => {
    try { await Api.logout(Store.get('refreshToken')); } catch {}
    Store.clear();
    window.location.href = 'index.html';
  });

  document.getElementById('close-review-modal').addEventListener('click', closeReviewModal);
  document.getElementById('admin-modal-backdrop').addEventListener('click', (e) => {
    if (e.target === e.currentTarget) closeReviewModal();
  });

  document.getElementById('btn-approve').addEventListener('click', () => submitReview('approved'));
  document.getElementById('btn-reject').addEventListener('click',  () => submitReview('rejected'));

  // User search
  document.getElementById('user-search').addEventListener('input', debounce(filterUsers, 300));

  // Request filter
  document.getElementById('req-status-filter').addEventListener('change', renderFilteredRequests);

  // Mobile sidebar
  const burger  = document.getElementById('sidebar-toggle');
  const sidebar = document.querySelector('.sidebar');
  const overlay = document.getElementById('sidebar-overlay');
  if (burger) {
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
  }

  await loadOverview();
})();

function showGuard() {
  document.getElementById('admin-auth-guard').classList.remove('hidden');
  document.getElementById('admin-app').style.visibility = 'hidden';
}

/* ═══════════════════════════════════════════════════════════════════════════
   ROUTING
   ══════════════════════════════════════════════════════════════════════════ */
const PAGE_TITLES = {
  'admin-overview':  'Панель адміністратора',
  'admin-users':     'Управління користувачами',
  'admin-requests':  'Запити користувачів',
};
const PAGE_LOADERS = {
  'admin-overview':  loadOverview,
  'admin-users':     loadUsers,
  'admin-requests':  loadAllRequests,
};

function navigateTo(pageId) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

  const page = document.getElementById(`page-${pageId}`);
  const nav  = document.querySelector(`[data-page="${pageId}"]`);
  if (page) page.classList.add('active');
  if (nav)  nav.classList.add('active');

  document.getElementById('admin-page-title').textContent = PAGE_TITLES[pageId] || pageId;
  const loader = PAGE_LOADERS[pageId];
  if (loader) loader();
}

/* ═══════════════════════════════════════════════════════════════════════════
   OVERVIEW
   ══════════════════════════════════════════════════════════════════════════ */
async function loadOverview() {
  // We can fetch our own user's requests as a sample — real admin would
  // have a GET /requests endpoint. Here we show whatever we can access.
  const user = Store.getUser();

  // Stats placeholders — populated as data loads
  document.getElementById('stat-users-total').textContent    = '—';
  document.getElementById('stat-pending-reqs').textContent   = '—';
  document.getElementById('stat-approved-today').textContent = '—';

  try {
    const requests = await Api.getUserRequests(user.id);
    _allRequests = requests;

    const pending  = requests.filter(r => r.status === 'pending').length;
    const today    = new Date().toDateString();
    const approved = requests.filter(r =>
      r.status === 'approved' && new Date(r.resolved_at).toDateString() === today
    ).length;

    document.getElementById('stat-users-total').textContent    = '1+';
    document.getElementById('stat-pending-reqs').textContent   = pending;
    document.getElementById('stat-approved-today').textContent = approved;

    // Badge
    const badge = document.getElementById('nav-requests-badge');
    badge.textContent = pending > 0 ? pending : '';

    // Recent requests
    const container = document.getElementById('admin-recent-requests');
    const recent = requests.slice(0, 5);
    if (recent.length === 0) {
      container.innerHTML = '<div class="empty-state">Запитів немає</div>';
    } else {
      container.innerHTML = '';
      recent.forEach((req, i) => {
        const card = buildRequestCard(req, true);
        card.style.setProperty('--i', i);
        container.appendChild(card);
      });
    }
  } catch (err) {
    UI.toast('Помилка завантаження: ' + err.message, 'error');
  }
}

/* ═══════════════════════════════════════════════════════════════════════════
   USERS
   ══════════════════════════════════════════════════════════════════════════ */
let _usersCache = [];

async function loadUsers() {
  const tbody = document.getElementById('users-table-body');
  tbody.innerHTML = '<tr><td colspan="6" class="empty-state skeleton" style="height:60px"></td></tr>';

  // In a real system we'd call GET /users (admin endpoint).
  // Here we show the currently authenticated admin user as a demonstration.
  const user = Store.getUser();
  _usersCache = [user];
  renderUsersTable(_usersCache);
}

function renderUsersTable(users) {
  const tbody = document.getElementById('users-table-body');
  if (users.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6" class="empty-state">Користувачів не знайдено</td></tr>';
    return;
  }
  tbody.innerHTML = '';
  users.forEach(u => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td style="font-family:var(--font-mono);font-size:.82rem">${u.email}</td>
      <td style="font-family:var(--font-mono);font-size:.8rem;color:var(--silver)">${u.phone || '—'}</td>
      <td><span class="badge ${u.role === 'ADMIN' ? 'badge--error' : 'badge--pending'}">${u.role}</span></td>
      <td>${UI.statusBadge(u.status)}</td>
      <td class="tx-date-cell">${UI.formatDateShort(u.created_at)}</td>
      <td>
        <div class="action-btns">
          <button class="action-btn action-btn--danger" data-user-id="${u.id}" data-action="block">
            ${u.status === 'active' ? 'Блок.' : 'Розблок.'}
          </button>
        </div>
      </td>
    `;
    // Block/unblock action
    tr.querySelector('[data-action="block"]').addEventListener('click', async (e) => {
      const btn = e.currentTarget;
      const newStatus = u.status === 'active' ? 'blocked' : 'active';
      btn.disabled = true;
      try {
        await _adminPatch(`/users/${u.id}`, { status: newStatus });
        u.status = newStatus;
        renderUsersTable(_usersCache);
        UI.toast(`Статус користувача оновлено: ${newStatus}`, 'success');
      } catch (err) {
        UI.toast('Помилка: ' + err.message, 'error');
        btn.disabled = false;
      }
    });
    tbody.appendChild(tr);
  });
}

let _usersFilterTerm = '';
function filterUsers(e) {
  _usersFilterTerm = e.target.value.toLowerCase();
  const filtered = _usersCache.filter(u =>
    u.email.toLowerCase().includes(_usersFilterTerm) ||
    (u.phone || '').includes(_usersFilterTerm)
  );
  renderUsersTable(filtered);
}

/* ═══════════════════════════════════════════════════════════════════════════
   REQUESTS
   ══════════════════════════════════════════════════════════════════════════ */
async function loadAllRequests() {
  const container = document.getElementById('admin-requests-list');
  container.innerHTML = '<div class="empty-state skeleton" style="height:120px;border-radius:12px"></div>';

  const user = Store.getUser();
  try {
    _allRequests = await Api.getUserRequests(user.id);
    renderFilteredRequests();
  } catch (err) {
    container.innerHTML = `<div class="empty-state">Помилка: ${err.message}</div>`;
  }
}

function renderFilteredRequests() {
  const filter    = document.getElementById('req-status-filter').value;
  const container = document.getElementById('admin-requests-list');

  const filtered = filter
    ? _allRequests.filter(r => r.status === filter)
    : _allRequests;

  container.innerHTML = '';
  if (filtered.length === 0) {
    container.innerHTML = '<div class="empty-state">Запитів не знайдено</div>';
    return;
  }

  filtered.forEach((req, i) => {
    const card = buildRequestCard(req, false);
    card.style.setProperty('--i', i);
    container.appendChild(card);
  });
}

function buildRequestCard(req, compact) {
  const card = document.createElement('div');
  card.className = `admin-request-card admin-request-card--${req.status}`;

  const typeShort = { BLOCK: 'BLOCK', UNBLOCK: 'UNBL', LIMIT_CHANGE: 'LIMIT' };

  card.innerHTML = `
    <div class="admin-req__type">${typeShort[req.type] || req.type}</div>
    <div class="admin-req__body">
      <div class="admin-req__user">account: ${req.account_id}</div>
      <div class="admin-req__message">${req.message}</div>
      <div class="admin-req__meta">
        ${UI.statusBadge(req.status)}
        <span class="admin-req__date">${UI.formatDate(req.created_at)}</span>
      </div>
      ${req.admin_comment ? `<div class="admin-req__comment">💬 ${req.admin_comment}</div>` : ''}
    </div>
    <div class="admin-req__actions">
      ${req.status === 'pending'
        ? `<button class="action-btn action-btn--success review-btn" data-id="${req.id}">Розглянути</button>`
        : `<span style="font-size:.72rem;color:var(--silver);font-family:var(--font-mono)">${req.resolved_at ? UI.formatDateShort(req.resolved_at) : ''}</span>`
      }
    </div>
  `;

  const reviewBtn = card.querySelector('.review-btn');
  if (reviewBtn) reviewBtn.addEventListener('click', () => openReviewModal(req));

  return card;
}

/* ═══════════════════════════════════════════════════════════════════════════
   REVIEW MODAL
   ══════════════════════════════════════════════════════════════════════════ */
function openReviewModal(req) {
  _pendingReviewId = req.id;

  const typeLabels = { BLOCK: 'Блокування', UNBLOCK: 'Розблокування', LIMIT_CHANGE: 'Зміна ліміту' };
  document.getElementById('rv-type').textContent    = typeLabels[req.type] || req.type;
  document.getElementById('rv-account').textContent = req.account_id;
  document.getElementById('rv-message').textContent = req.message;
  document.getElementById('rv-date').textContent    = UI.formatDate(req.created_at);
  document.getElementById('rv-status').innerHTML    = UI.statusBadge(req.status);
  document.getElementById('rv-comment').value       = req.admin_comment || '';
  document.getElementById('rv-error').classList.add('hidden');

  // Disable actions if already resolved
  const isPending = req.status === 'pending';
  document.getElementById('btn-approve').disabled = !isPending;
  document.getElementById('btn-reject').disabled  = !isPending;

  document.getElementById('admin-modal-backdrop').classList.remove('hidden');
  document.getElementById('modal-review-request').classList.remove('hidden');
}

function closeReviewModal() {
  document.getElementById('admin-modal-backdrop').classList.add('hidden');
  document.getElementById('modal-review-request').classList.add('hidden');
  _pendingReviewId = null;
}

async function submitReview(status) {
  if (!_pendingReviewId) return;

  const comment = document.getElementById('rv-comment').value.trim();
  const errEl   = document.getElementById('rv-error');
  errEl.classList.add('hidden');

  const btnApprove = document.getElementById('btn-approve');
  const btnReject  = document.getElementById('btn-reject');
  btnApprove.disabled = btnReject.disabled = true;

  try {
    await _adminPatch(`/requests/${_pendingReviewId}/status`, {
      status,
      admin_comment: comment || undefined,
    });

    // Update local cache
    const req = _allRequests.find(r => r.id === _pendingReviewId);
    if (req) { req.status = status; req.admin_comment = comment || null; }

    closeReviewModal();
    UI.toast(
      status === 'approved' ? '✓ Запит схвалено' : '✕ Запит відхилено',
      status === 'approved' ? 'success' : 'error'
    );

    // Refresh current view
    renderFilteredRequests();
    await loadOverview();
  } catch (err) {
    errEl.textContent = err.message;
    errEl.classList.remove('hidden');
    btnApprove.disabled = btnReject.disabled = false;
  }
}

/* ═══════════════════════════════════════════════════════════════════════════
   UTILS
   ══════════════════════════════════════════════════════════════════════════ */
function debounce(fn, ms) {
  let t;
  return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); };
}