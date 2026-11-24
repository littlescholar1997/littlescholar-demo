# 管理員登入設定與驗收

日期：2026-11-24

## 目前狀態

登入入口、已登入工作台、登出及伺服器 JWT 驗證已實作。正式服務尚未部署到 Cloudflare 帳號，Google OAuth 尚未配置，尚未完成真實帳號登入驗收。因此公開入口 auth.json 保持 enabled:false，不顯示可用的登入按鈕。

選用 Google → Cloudflare Access → CMS Worker。Google 負責確認帳號身分，Cloudflare Access 負責登入流程、Cookie、工作階段與撤銷，Worker 再驗證簽章、issuer、audience、到期時間與管理員 Email 名單。沒有自行保存 Google 密碼或把 ID Token 放進 localStorage。現有 localStorage 只用於試用草稿。

Google 登入不等於取得 GitHub 寫入權限。此階段登入後的內容編輯仍是本機草稿，正式發布尚未串接，也未加入公開註冊功能。

## 架構與部署邊界

- GitHub Pages：保留官網與 `/admin/` 登入入口，以及明確標示的 `/admin/demo.html` 介面試用。
- 獨立 Cloudflare 管理員主機：部署 auth-server Worker 與 CMS 靜態資產，整個主機由 Access 保護，不與公開官網共用 Access 規則。
- Worker 的 `run_worker_first:true` 確保資產也先驗證；任何 alternate host、未設定環境或未帶有效 Access 憑證的請求一律拒絕。
- Worker 只開放 CMS 必要資產與讀取用 session API；production 不提供 demo、Decap 試用或未知 API。不要以 GitHub Pages 的前端隱藏作為權限保護。
- 公開 Repo 和已發布文章本來就是公開資料。不要提交管理員名單、未發布敏感內容或憑證。

## Google 與 Cloudflare 設定順序

1. 準備 Cloudflare 帳號與用於後台的獨立主機。可以先使用測試子網域，不用先更動 Wix 官網或主網域。
2. 在 Cloudflare Zero Trust 設定 team name，取得 `https://TEAM.cloudflareaccess.com`。
3. 在 Google Cloud 建立或沿用學校管理的專案。在 Google Auth Platform 設定品牌名稱、支援信箱及 Audience；一般 Gmail 選 External。
4. 建立 Web application 類型的 OAuth client。Authorized JavaScript origins 填 team domain，Authorized redirect URI 填 `https://TEAM.cloudflareaccess.com/cdn-cgi/access/callback`。callback 是 Access team domain，不是 GitHub Pages 網址，也不是 Worker 的 /admin/。
5. 將 Client ID 與 Client Secret 直接填入 Cloudflare Zero Trust → Integrations → Identity providers → Google；啟用 PKCE。不要貼進聊天、Repo 或前端設定。
6. 建立 Access Self-hosted application，保護完整管理員主機所有路徑。Login methods 只選 Google。Allow policy 使用指定管理員的完整 Email，不可 Everyone 或整個 gmail.com；建議 session duration 1 小時。Cookie 設定啟用 HttpOnly 與 Secure，並確認 SameSite 與登入回跳正常。
7. 取得 Access application 的 AUD tag。修改 auth-server/wrangler.jsonc：ACCESS_TEAM_DOMAIN、ACCESS_AUD、ADMIN_ORIGIN，並加入自己管理的 custom domain route。ADMIN_ORIGIN 必須是精確 https origin，無路徑或結尾斜線。
8. 在本機已授權的 Cloudflare 環境，以 `npx wrangler secret put ADMIN_EMAILS` 安全輸入管理員 Email；多位管理員以逗號分隔。本專案程式會讀取此設定，不需要將真實名單提交到 Git。
9. 從 Repo 根目錄建置：`python3 scripts/build_site.py --output dist`。在 auth-server 執行 `npm ci`、`npm test`、`npm run build`，最後 `npm run deploy`。
10. 先驗收下方情境，通過後才將公開 admin/auth.json 設為 enabled:true、serviceUrl 設為確定可用的後台 origin。Google provider 保持啟用。不能只改 enabled 就視為完成登入。

若 Google 專案仍處測試模式，請確認測試帳號設定；正式使用前按 Google 的要求完成 publishing status 與品牌資訊。不要要求 Gmail、Drive、Calendar 等非登入所需權限。

## 正式驗收

- 無痕未登入進入管理主機：先到 Access／Google 身分驗證，不能直接讀到 workspace、JS、content 或 API。
- 指定管理員：Google 登入後看到自己的 Email，列表、編輯、圖片與預覽正常。
- 非名單帳號：Access 與 Worker 均拒絕，不可只靠前端導回。
- 手工偽造 email header、Cookie 或 JWT；錯誤 issuer/audience、過期 token、變更簽章、空名單：伺服器拒絕。
- 登出：完成 Access 登出，重新請求不能取得 session。切換回舊分頁或工作階段到期時，工作台鎖定並要求重新登入。
- 撤權：同時移除 Access policy 與 Worker ADMIN_EMAILS，並在 Access 撤銷現有工作階段。
- 不授權 GitHub 寫入，不宣稱已啟用正式發布或跨裝置草稿同步。

## 程式檢查

`cd auth-server && npm test && npm run build`

測試以本機產生的 RSA 金鑰和真正簽署 JWT 驗證正常與攻擊案例，不使用真實 Google 密鑰、不傳送 Email、不進行假登入。正式 Google／Access 帳號整合必須另行驗收。

官方文件：

- https://developers.cloudflare.com/cloudflare-one/integrations/identity-providers/google/
- https://developers.cloudflare.com/cloudflare-one/access-controls/applications/http-apps/authorization-cookie/validating-json/
- https://developers.cloudflare.com/cloudflare-one/access-controls/access-settings/session-management/
- https://developers.cloudflare.com/workers/static-assets/binding/
