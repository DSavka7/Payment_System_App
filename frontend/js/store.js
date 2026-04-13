const Store = (() => {
  const _mem = {};

  const set = (key, value) => {
    _mem[key] = value;
    try { sessionStorage.setItem(`vault_${key}`, JSON.stringify(value)); } catch {}
  };

  const get = (key) => {
    if (_mem[key] !== undefined) return _mem[key];
    try {
      const raw = sessionStorage.getItem(`vault_${key}`);
      if (raw !== null) { _mem[key] = JSON.parse(raw); return _mem[key]; }
    } catch {}
    return null;
  };

  const clear = () => {
    Object.keys(_mem).forEach(k => delete _mem[k]);
    try { Object.keys(sessionStorage).filter(k => k.startsWith('vault_')).forEach(k => sessionStorage.removeItem(k)); } catch {}
  };

  // ── Typed helpers ─────────────────────────────────────────────────────────
  const setAuth = ({ access_token, refresh_token }) => {
    set('accessToken', access_token);
    set('refreshToken', refresh_token);
  };

  const setUser = (user) => set('user', user);
  const getUser = ()     => get('user');
  const isLoggedIn = ()  => !!get('accessToken');

  return { set, get, clear, setAuth, setUser, getUser, isLoggedIn };
})();