# taiga-kimai-sync

以非同步 Python Client 串接 Taiga API，讀取專案與 Epic 資料，為 Taiga 與 Kimai 的工時同步建立資料基礎。

## 功能

- 透過 `.env` 管理連線與日誌設定
- 使用帳號密碼驗證 Taiga，自動帶入 Bearer Token
- 取得可存取的專案資訊：`id`、`name`、`slug`
- 依專案取得 Epic 資訊：`id`、`ref`、`subject`、`project`
- 使用 Pydantic 驗證回應並統一處理 API 錯誤
- 支援非同步 Context Manager，自動登入與關閉連線
