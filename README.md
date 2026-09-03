# taiga-kimai-sync

以非同步 Python Client 串接 Taiga 與 Kimai API，讀取 Taiga 工作項目並管理 Kimai Customer 與 Project，建立工時同步所需的兩端 API 基礎。

## 功能

- 透過 `.env` 管理連線與日誌設定
- 使用帳號密碼驗證 Taiga，自動帶入 Bearer Token
- 依序讀取 Taiga 的 Project、Epic、User Story 與 Task
- 使用 API Token 驗證 Kimai 並檢查連線狀態
- 查詢、建立及更新 Kimai Customer
- 查詢、建立及更新 Kimai Project，並可依 Customer 篩選
- 使用 Pydantic 驗證回應並統一處理 API 錯誤
- 支援非同步 Context Manager，自動驗證服務與關閉連線
