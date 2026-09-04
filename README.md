# taiga-kimai-sync

以非同步 Python Client 串接 Taiga 與 Kimai，讀取 Taiga 工作項目、管理 Kimai 資源，並保存兩端資料的同步映射。

## API 整合

- 透過 `.env` 管理連線與日誌設定
- 驗證並讀取 Taiga 的 Project、Epic、User Story 與 Task
- Kimai Client 以 API Token 驗證，並以共用非同步 Transport 串接 `customers`、`projects`、`activities` Resource，支援列表、單筆查詢、建立與更新
- 使用 Pydantic 驗證回應、統一處理 API 錯誤，並以非同步 Context Manager 管理連線

## 同步映射

使用 SQLite 與 SQLAlchemy 建立 `Taiga Project → Kimai Customer`、`Taiga Epic → Kimai Project`、`Taiga Task → Kimai Activity` 的一對一映射，並透過非同步 Session 與 Alembic migration 管理資料庫。

## 同步流程

- `Taiga Project → Kimai Customer`：首次同步會建立 Customer 與映射；後續沿用既有 Kimai ID，同步名稱與顯示狀態，資料一致時不重複寫入
- `Taiga Epic → Kimai Project`：需先有父層映射，缺少時中止；首次同步會建立 Project 與映射，後續沿用既有 Kimai ID，同步名稱、Customer 與顯示狀態，資料一致時不重複寫入
- `Taiga Task → Kimai Activity`：驗證 Task、User Story 與 Epic 關係並要求 Epic 映射；首次同步以 `[User Story] Task` 建立 Activity 與映射，後續沿用既有 Kimai ID，同步名稱、所屬 Project 與顯示狀態，資料一致時不重複寫入

## 全量同步

`reconcile` 依 Project → Epic → User Story → Task 完整走訪 Taiga 並執行各層同步。走訪成功後，未再出現但仍有映射的 Kimai 資源會依 Activity → Project → Customer 順序設為隱藏；若途中失敗則不執行清理，避免誤判資料已刪除。
