const API_BASE = 'http://localhost:8000';

const Api = (() => {
    async function _fetch(path, options = {}, retry = true) {
        const accessToken = Store.get('accessToken');
        const headers = { 'Content-Type': 'application/json', ...options.headers };
        if (accessToken) headers['Authorization'] = `Bearer ${accessToken}`;

        const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

        if (res.status === 401 && retry) {
            const refreshed = await _tryRefresh();
            if (refreshed) return _fetch(path, options, false);
            Store.clear();
            App.showAuth();
            throw new Error('Session expired');
        }

        if (!res.ok) {
            let detail = `HTTP ${res.status}`;
            try {
                const body = await res.json();
                detail = body.detail || JSON.stringify(body);
            } catch {}
            throw new Error(detail);
        }

        if (res.status === 204) return null;
        return res.json();
    }

    async function _tryRefresh() {
        const refreshToken = Store.get('refreshToken');
        if (!refreshToken) return false;
        try {
            const data = await fetch(`${API_BASE}/users/refresh`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refresh_token: refreshToken }),
            }).then(r => r.json());
            if (data.access_token) {
                Store.set('accessToken', data.access_token);
                return true;
            }
        } catch {}
        return false;
    }

    const get  = (path)       => _fetch(path, { method: 'GET' });
    const post = (path, body) => _fetch(path, { method: 'POST', body: JSON.stringify(body) });
    const patch= (path, body) => _fetch(path, { method: 'PATCH', body: JSON.stringify(body) });
    const del  = (path)       => _fetch(path, { method: 'DELETE' });

    // Auth
    const login = (email, password) => {
        const form = new URLSearchParams({ username: email, password });
        return fetch(`${API_BASE}/users/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: form,
        }).then(async res => {
            if (!res.ok) {
                const body = await res.json().catch(() => ({}));
                throw new Error(body.detail || `HTTP ${res.status}`);
            }
            return res.json();
        });
    };

    const register = (data) => post('/users/', data);
    const logout   = (rt)   => post('/users/logout', { refresh_token: rt });
    const getMe    = ()     => get('/users/me');

    // Accounts
    const createAccount   = (data) => post('/accounts/', data);
    const getUserAccounts = (uid)  => get(`/accounts/user/${uid}`);
    const getAccount      = (id)   => get(`/accounts/${id}`);
    const deleteAccount   = (id)   => del(`/accounts/${id}`);

    // Transfer
    const transfer = (data) => post('/accounts/transfer', data);

    // Transactions
    const getAccountTx = (accId, limit = 50, offset = 0) =>
        get(`/transactions/account/${accId}?limit=${limit}&offset=${offset}`);
    const getTx = (id) => get(`/transactions/${id}`);

    // Requests
    const createRequest   = (data) => post('/requests/', data);
    const getUserRequests = (uid)  => get(`/requests/user/${uid}`);

    return {
        login, register, logout, getMe,
        createAccount, getUserAccounts, getAccount, deleteAccount,
        transfer,
        getAccountTx, getTx,
        createRequest, getUserRequests,
    };
})();