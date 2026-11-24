'use strict';
(async () => {
  const status = document.querySelector('#login-status'), button = document.querySelector('#sign-in');
  try {
    const response = await fetch('auth.json', { cache: 'no-store' });
    if (!response.ok) throw Error('config');
    const config = await response.json();
    if (!config.enabled || !config.serviceUrl) {
      status.textContent = '管理員登入尚待啟用。驗證服務設定完成後，即可從這裡進入後台。';
      button.textContent = '管理員登入尚未啟用'; return;
    }
    const url = new URL(config.serviceUrl);
    if (url.protocol !== 'https:' || url.username || url.password || url.search || url.hash || url.pathname !== '/') throw Error('config');
    button.href = url.origin + '/admin/';
    button.removeAttribute('aria-disabled'); button.textContent = '使用 Google 帳號登入';
    status.textContent = '使用指定的管理員帳號登入。將前往 Google 登入頁完成身分驗證。';
  } catch {
    status.textContent = '暫時無法載入登入設定，請重新整理或聯絡網站管理員。';
    button.textContent = '登入暫時無法使用';
  }
})();
