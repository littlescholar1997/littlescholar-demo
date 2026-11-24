# 小學者內容管理：第一階段交接

2026-11-24

## 現在可以使用

- `/admin/`：管理員登入入口，驗證服務尚待啟用；`/admin/demo.html`：自訂中文內容工作台試用。包含消息與老師文章列表、搜尋、狀態篩選、新增、編輯、Markdown 內文、圖片上傳壓縮、沙盒預覽、本機儲存、JSON 匯入匯出、未儲存提醒。
- 學生見證：姓名、學歷、經歷、原文、照片、排序、狀態。
- 彈出公告：標題、文字、圖片、按鈕、台灣時間起訖、每天／每次瀏覽／每次進入的頻率。第一階段編輯僅儲存在本機，前台已有消費正式設定的程式，但範例預設關閉。
- 網站基本資料：電話、地址、營業時間。
- `/news/`、`/teacher/`：文章列表與搜尋，每篇有自己的 `.html` 網址。
- `/voices/`：完整校友見證列表。
- `/admin/preview.html`：手機／平板介面預覽。
- `/admin/decap.html`：Decap 配置與待辦說明，提供官方 test-repo 編輯器試用。test-repo 內容重新整理即消失。

## 明確的完成邊界

目前的自訂工作台是可操作的第一階段原型，並非完成登入與正式發布的多人 CMS。

本機儲存只寫入目前來源網域的 localStorage，不會傳送內容至 GitHub，也不會同步至其他裝置。請用 JSON 匯出備份。上傳圖片先在瀏覽器轉成 WebP，隨草稿及備份保存；正式版應使用 Repo uploads 或獨立圖片服務。

Decap 的 GitHub backend 設定已放在 `admin/config.yml`，但 OAuth 尚未配置，也未建立自動發布工作流。`admin/auth.json` 為停用狀態的公開入口設定，不是登入保護。新增的 auth-server Worker 會在伺服器驗證 Cloudflare Access JWT 與管理員名單；尚待部署與 Google OAuth 設定，步驟見 ADMIN-LOGIN.md。未在任何公開檔案放置密碼、Token 或 client secret。

正式環境仍需：

1. 決定登入服務，配置 GitHub OAuth 驗證服務與 callback、允許的來源網域；將秘密儲存在伺服器環境變數。
2. 確認管理員帳號與 Repo 權限，測試未授權帳號不能寫入。
3. 將內容修改接到驗證、建置、預覽與部署工作流，失敗時保留上一個成功版本。
4. 已從 Wix 公開 sitemap 匯入 8 篇全文、發布日期及 10 張圖片；正式切換前請由編輯再審閱內容與圖片使用權。來源比對見 migration/report.json。
5. 將公開 Repo 中的草稿視為公開資訊。若需要未發布內容保密，使用私有內容 Repo 或受權限控管的 CMS 儲存，不能靠前台隱藏。
6. 在正式發布驗收完成後，再調整 Wix 網域及舊文章轉址。

未變更 Wix、DNS、付費服務或帳號權限。

## 資料與建置

唯一內容來源：`content/site.json`。結構版本為 `schemaVersion: 1`。

文章欄位：id、section、title、slug、category、date、status、featured、cover、coverAlt、summary、body、sourceUrl、migration。

- section：news／teacher
- status：draft／published／archived
- migration：excerpt（只有摘要）／complete（全文完成）
- 日期空白代表尚未確認，不會杜撰發布日期。
- date 是顯示日期，並非排程發布。公告起訖時間則由前台以 UTC+8 判斷。

本機建置，不需要安裝 Python 套件：

```bash
node tests/core.test.cjs
python3 tests/build.test.py
python3 scripts/build_site.py --content content/site.json --output _site
```

把 `_site` 部署為網站輸出。建置只公開 published 的文章及見證，封存或草稿頁不輸出；重新建置也會移除舊的生成文章頁。來源 Repo 如為公開，來源 JSON 與版本歷史仍可被讀取。

已測試：資料結構、重複網址、路徑穿越、危險網址、Markdown HTML 跳脫、公告時間、圖片說明、草稿排除與封存頁移除。瀏覽器另驗證新增儲存後刷新、搜尋、內文預覽與公告預覽。

## 設計

沿用品牌紅 #BC000B，搭配白、淡綠 #EEF3ED、深綠文字 #29342E。用左側功能列、內容列表與右側文章設定降低編輯負擔。沒有假流量或營收統計；數量來自實際內容。主要操作至少 44px，手機把功能列改為橫向選單。
