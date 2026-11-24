# CMS 首版與 Wix 內容移轉驗證

2026-11-24

- 從公開 sitemap 的 8 個文章網址匯入全文，涵蓋 140 個來源文字區塊；以原頁發布日期建立日期欄位。
- 6 篇最新消息、2 篇老師文章；保留 Student Works 與三張作品圖。
- 10 張圖片轉成 WebP，存於 uploads/wix，不依賴 Wix 圖片 CDN。
- migration/report.json 記錄各文章來源及圖片對照；不提交原頁 HTML 與套件目錄。
- 首頁摘要、列表、文章、返回連結與 CMS 使用同一份 content/site.json。
- 舊 summer-course-2026.html 保留導引頁，避免既有示範連結失效。

## 已執行

- Node 資料與 Markdown 安全檢查。
- Python 建置、草稿排除、封存移除、完整移轉比對與本機圖片存在檢查。
- 靜態 HTML 的本機連結、圖片替代文字、重複 ID 掃描，結果見 migration/static-audit.json。
- 雲端瀏覽器檢查首頁、文章列表、長文、學生作品、見證、CMS；375 px 外框（360 px 內容視口）未出現橫向溢出。
- 瀏覽器操作已確認新增、儲存、刷新後保留草稿；本機草稿優先於網站更新資料，匯出後再匯入網站資料可進行人工合併。

## 限制

此階段為本機儲存的可操作 CMS 原型。正式登入、多人權限、寫入 GitHub 與自動發布尚未串接；詳細交接見 CMS-HANDOFF.md。

Chrome DevTools MCP 1.13.0 已安裝，stdio 初始化與 33 個工具列舉通過；本機 Chromium 啟動遭環境 socket 權限拒絕，未能執行 MCP 瀏覽器、Lighthouse 或效能追蹤。本次瀏覽器結果來自雲端瀏覽器，不宣稱已完成上述效能檢查。可重現設定見 tools/devtools/README.md。

尚未切換 Wix、DNS 或正式網域。
