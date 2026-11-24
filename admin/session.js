'use strict';
(async () => {
  let expiresAt = 0, checking = false, signedOut = false;
  const headers = { 'X-Requested-With': 'XMLHttpRequest' };
  function lock(message) {
    if (signedOut) return;
    signedOut = true;
    const main = document.createElement('main');
    main.style.cssText = 'max-width:640px;margin:12vh auto;padding:30px';
    const heading = document.createElement('h1'); heading.textContent = '請重新登入';
    const text = document.createElement('p'); text.textContent = message;
    const link = document.createElement('a'); link.href = './'; link.textContent = '返回管理員登入';
    main.append(heading, text, link); document.body.replaceChildren(main); document.body.hidden = false;
  }
  async function check() {
    if (checking || signedOut) return false;
    checking = true;
    try {
      const response = await fetch('/api/admin/session', { headers, credentials: 'same-origin', cache: 'no-store', redirect: 'error' });
      if (!response.ok) throw Error('session');
      const session = await response.json();
      if (session.authenticated !== true || session.user?.role !== 'admin' || !session.user.email || !(session.user.expiresAt > Date.now())) throw Error('session');
      expiresAt = session.user.expiresAt;
      document.querySelector('#signed-in-email').textContent = session.user.email;
      return true;
    } catch {
      lock('登入已到期、未獲授權，或暫時無法驗證身分。請重新登入後繼續。');
      return false;
    } finally { checking = false; }
  }
  if (!await check()) return;
  document.body.hidden = false;
  const script = document.createElement('script'); script.src = 'admin.js';
  script.onerror = () => lock('工作台載入失敗，請重新登入後再試。');
  document.body.append(script);
  document.querySelector('#sign-out').addEventListener('click', async event => {
    event.currentTarget.disabled = true;
    try {
      const response = await fetch('/api/admin/logout', { method: 'POST', headers, credentials: 'same-origin', redirect: 'error' });
      if (!response.ok) throw Error('logout');
      const result = await response.json();
      const url = new URL(result.logoutUrl);
      if (url.origin !== location.origin || url.pathname !== '/cdn-cgi/access/logout' || url.search || url.hash) throw Error('logout');
      location.assign(url.href);
    } catch {
      event.currentTarget.disabled = false;
      document.querySelector('#toast').textContent = '登出未完成，請確認連線後重試。';
      document.querySelector('#toast').classList.add('toast-visible');
    }
  });
  setInterval(() => { if (Date.now() >= expiresAt) lock('登入已到期，請重新登入。'); else check(); }, 60000);
  document.addEventListener('visibilitychange', () => { if (!document.hidden) check(); });
  window.addEventListener('pageshow', event => { if (event.persisted) check(); });
})();
