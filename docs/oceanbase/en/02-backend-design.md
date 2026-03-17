# OceanBase backend design

When OceanBase is the Connectors backend, a set of tables in a MySQL-protocol database emulate Elasticsearch indices and documents so the CLI and Connector Service can read/write metadata and sync content. For usage and commands, see [01-Quick start](./01-quickstart.md).

---

## 1. Table types

| Type | Table | Description |
|------|-------|-------------|
| System | `ob_connectors` | Connector metadata (ES `.elastic-connectors-v1`) |
| System | `ob_connectors_sync_jobs` | Sync job metadata (ES `.elastic-connectors-sync-jobs-v1`) |
| Content | `ob_content_<sanitized_index_name>` | One table per logical index for document data |

---

## 2. Naming rules

- **Index name → content table name:** Non-alphanumeric characters in the index name become underscores, then the prefix `ob_content_` is added.
- Examples:
  - `github-idx` → `ob_content_github_idx`
  - `ob-mysql-idx` → `ob_content_ob_mysql_idx`
  - `my_index` → `ob_content_my_index`

---

## 3. Table DDL

### 3.1 System table `ob_connectors`

```sql
CREATE TABLE IF NOT EXISTS ob_connectors (
    id VARCHAR(512) NOT NULL PRIMARY KEY COMMENT 'connector id',
    doc JSON NOT NULL COMMENT 'connector document body'
);
```

- `id`: Connector ID (e.g. 20-char string from CLI).
- `doc`: Full connector document (JSON), including configuration, index_name, service_type, etc.

### 3.2 System table `ob_connectors_sync_jobs`

```sql
CREATE TABLE IF NOT EXISTS ob_connectors_sync_jobs (
    id VARCHAR(512) NOT NULL PRIMARY KEY COMMENT 'sync job id',
    doc JSON NOT NULL COMMENT 'sync job document body'
);
```

- `id`: Sync job ID.
- `doc`: Full job document (JSON), including status, job_type, connector, indexed_document_count, etc.

### 3.3 Content table `ob_content_<name>`

```sql
CREATE TABLE IF NOT EXISTS `ob_content_<name>` (
    id VARCHAR(512) NOT NULL PRIMARY KEY COMMENT 'document _id',
    doc JSON NOT NULL COMMENT 'document _source',
    _timestamp TIMESTAMP NULL DEFAULT NULL COMMENT 'for incremental sync'
);
```

- `id`: Document `_id`.
- `doc`: Document body (`_source`) as JSON.
- `_timestamp`: Used for incremental sync (may be NULL).

---

## 4. Mapping to Elasticsearch

| Elasticsearch | OceanBase |
|---------------|-----------|
| System index `.elastic-connectors-v1` | Table `ob_connectors` |
| System index `.elastic-connectors-sync-jobs-v1` | Table `ob_connectors_sync_jobs` |
| Regular index (e.g. `my-index`) | Table `ob_content_my_index` |
| Document `_id` | Column `id` |
| Document `_source` | Column `doc` (JSON) |

---

[← Quick start](./01-quickstart.md) | [Index](./README.md) | [FAQ and scripts →](./03-faq-and-scripts.md)
