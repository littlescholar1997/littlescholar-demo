# Chrome DevTools MCP

已安裝並驗證 npm 套件 `chrome-devtools-mcp@1.13.0` 可啟動 MCP server、完成 initialize 並列出 33 個工具。

在支援自訂 MCP server 的本機用戶端，可載入 Repo 根目錄 `.mcp.json`。安裝後還需要可執行的 Google Chrome／Chrome for Testing。ChatGPT Work 的工具清單不會因為新增 `.mcp.json` 而自動擴充。

## 本次環境限制

呼叫 list_pages 失敗，Chromium 在建立 socket 時被執行環境拒絕：`socket() failed: Operation not permitted`。因此本次無法透過這個 MCP 蒐集 console、network 或效能追蹤，也沒有宣稱完成 Lighthouse 評分。

未停用作業系統或 Chrome 的 sandbox，也未變更網路權限。網站改以既有雲端瀏覽器進行實際畫面與互動驗證，並以 Python／Node 執行結構、內容完整性與連結檢查。

官方來源：https://github.com/ChromeDevTools/chrome-devtools-mcp
