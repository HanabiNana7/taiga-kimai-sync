# taiga-kimai-sync

以非同步 Python Client 串接 Taiga 與 Kimai，讀取 Taiga 工作項目、管理 Kimai 資源，並保存兩端資料的同步映射。

## API 整合

- 透過 `.env` 管理連線與日誌設定
- 驗證並讀取 Taiga 的 Project、Epic、User Story 與 Task
- 驗證並管理 Kimai 的 Customer、Project 與 Activity
- 使用 Pydantic 驗證回應、統一處理 API 錯誤，並以非同步 Context Manager 管理連線

## 同步映射

使用 SQLite 與 SQLAlchemy 建立 `Taiga Project → Kimai Customer`、`Taiga Epic → Kimai Project`、`Taiga Task → Kimai Activity` 的一對一映射，並透過非同步 Session 與 Alembic migration 管理資料庫。
