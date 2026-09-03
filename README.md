# taiga-kimai-sync

以非同步 Python Client 串接 Taiga API，沿著 Project、Epic、User Story 與 Task 的階層讀取工作項目，為 Taiga 與 Kimai 的工時同步建立資料基礎。

## 功能

- 透過 `.env` 管理連線與日誌設定
- 使用帳號密碼驗證 Taiga，自動帶入 Bearer Token
- 取得可存取的 Taiga Project
- 依 Project ID 取得 Epic
- 依 Epic ID 取得 User Story
- 依 User Story ID 取得 Task
- 使用 Pydantic 驗證回應並統一處理 API 錯誤
- 支援非同步 Context Manager，自動登入與關閉連線
