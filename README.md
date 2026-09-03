# taiga-kimai-sync

Taiga 與 Kimai 的整合工具，以非同步 Python Client 串接 Taiga API，提供後續工時同步所需的基礎能力。

## 功能

- 透過 `.env` 管理 Taiga、Kimai 與日誌設定
- 使用帳號密碼驗證 Taiga，並自動帶入 Bearer Token
- 取得可存取的 Taiga 專案，輸出 `id`、`name` 與 `slug`
- 支援非同步 Context Manager，自動完成登入與連線關閉
