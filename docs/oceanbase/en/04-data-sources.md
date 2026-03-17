# Data sources guide (OceanBase backend)

Configuration and usage for each connector with the OceanBase backend. Use the listed `--service-type` values; for non-interactive create, pass JSON via `--from-file` with keys matching each source’s config.

**Full example JSON per source → [05-Config examples](./05-config-examples.md)** (copy and edit).

---

## Data source list

| service_type | Description | Section |
|--------------|-------------|---------|
| mysql | MySQL database | [MySQL](#mysql) |
| github | GitHub (issues, PRs, files) | [GitHub](#github) |
| mongodb | MongoDB | [MongoDB](#mongodb) |
| postgresql | PostgreSQL | [PostgreSQL](#postgresql) |
| mssql | Microsoft SQL Server | [MSSQL](#mssql) |
| oracle | Oracle database | [Oracle](#oracle) |
| s3 | Amazon S3 | [S3](#s3) |
| dir | Local directory | [Dir](#dir) |
| azure_blob_storage | Azure Blob Storage | [Others](#other-data-sources) |
| box | Box | [Others](#other-data-sources) |
| confluence | Confluence | [Others](#other-data-sources) |
| dropbox | Dropbox | [Others](#other-data-sources) |
| gmail | Gmail | [Others](#other-data-sources) |
| gitlab | GitLab | [Others](#other-data-sources) |
| google_cloud_storage | Google Cloud Storage | [Others](#other-data-sources) |
| google_drive | Google Drive | [Others](#other-data-sources) |
| graphql | GraphQL | [Others](#other-data-sources) |
| jira | Jira | [Others](#other-data-sources) |
| microsoft_teams | Microsoft Teams | [Others](#other-data-sources) |
| network_drive | Network drive / NAS | [Others](#other-data-sources) |
| notion | Notion | [Others](#other-data-sources) |
| onedrive | OneDrive | [Others](#other-data-sources) |
| outlook | Outlook | [Others](#other-data-sources) |
| redis | Redis | [Others](#other-data-sources) |
| salesforce | Salesforce | [Others](#other-data-sources) |
| sandfly | Sandfly | [Others](#other-data-sources) |
| servicenow | ServiceNow | [Others](#other-data-sources) |
| sharepoint_online | SharePoint Online | [Others](#other-data-sources) |
| sharepoint_server | SharePoint Server | [Others](#other-data-sources) |
| slack | Slack | [Others](#other-data-sources) |
| zoom | Zoom | [Others](#other-data-sources) |

---

## MySQL

- **service_type:** `mysql`
- **Purpose:** Sync from MySQL tables to OceanBase content tables.

### Config keys (--from-file JSON)

| Key | Description |
|-----|-------------|
| host | Host |
| port | Port (number) |
| user | Username |
| password | Password |
| database | Database name |
| tables | Table list, e.g. `"*"` or `["t1","t2"]` |
| ssl_enabled | Enable SSL (bool) |
| fetch_size | Rows per batch (optional) |
| retry_count | Retries (optional) |

### JSON example

See [05-Config examples](./05-config-examples.md#mysql). Minimal:

```json
{
  "host": "127.0.0.1",
  "port": 3306,
  "user": "root",
  "password": "changeme",
  "database": "test",
  "tables": "*",
  "ssl_enabled": false,
  "fetch_size": 50,
  "retry_count": 3
}
```

### Command example

```bash
connectors -c config.yml connector create \
  --name ob-mysql-test \
  --index-name ob-mysql-idx \
  --service-type mysql \
  --index-language en \
  --from-file mysql-connector-config.json
```

---

## GitHub

- **service_type:** `github`
- **Purpose:** Sync GitHub repos (issues, PRs, files) to OceanBase content tables.
- **Auth:** Prefer **Classic PAT** (`ghp_`), with scopes `repo`, `user`, `read:org`. Fine-grained PATs (`github_pat_`) are not supported by the current scope check and will fail.

### Config keys (--from-file JSON)

| Key | Description |
|-----|-------------|
| data_source | `github_cloud` or `github_server` |
| auth_method | `personal_access_token` or `github_app` |
| token | PAT or App credentials |
| repo_type | `organization` or `other` |
| repositories | Repo list, e.g. `["owner/repo"]` or `["*"]` |
| ssl_enabled | bool |
| retry_count | Number (required, e.g. 3) |
| use_text_extraction_service | bool (required, e.g. false) |
| use_document_level_security | bool (required, e.g. false) |
| host | Only when data_source=github_server |

### JSON example

See [05-Config examples](./05-config-examples.md#github). Example file: `app/connectors_service/github-connector-config.example.json` — copy and set `token` and `repositories`.

### Flow

1. Create connector: `connector create --service-type github --from-file github-connector-config.json ...`
2. Create job: `job start -i <connector_id> -t full`
3. Run sync: `sync-ob -c <config> -i <connector_id>`

---

## MongoDB

- **service_type:** `mongodb`
- **Purpose:** Sync from MongoDB collections to OceanBase content tables.

### Config keys (--from-file JSON)

| Key | Description |
|-----|-------------|
| host | Host |
| user | Username (optional) |
| password | Password (optional) |
| database | Database name |
| collection | Collection name |
| direct_connection | bool (optional) |
| ssl_enabled | bool (optional) |
| ssl_ca | Certificate (optional when ssl_enabled) |
| tls_insecure | bool (optional) |

### JSON example

See [05-Config examples](./05-config-examples.md#mongodb).

### Command template

```bash
connectors -c config.yml connector create \
  --name ob-mongo \
  --index-name mongo-idx \
  --service-type mongodb \
  --index-language en \
  --from-file mongo-connector-config.json
```

---

## PostgreSQL

- **service_type:** `postgresql`
- **Purpose:** Sync from PostgreSQL tables to OceanBase.

Provide host, port, username, password, database, schema, tables, etc. **Example:** [05-Config examples](./05-config-examples.md#postgresql).

### Command template

```bash
connectors -c <config> connector create \
  --name pg-conn \
  --index-name pg-idx \
  --service-type postgresql \
  --index-language en \
  --from-file postgresql-connector-config.json
```

---

## MSSQL

- **service_type:** `mssql`
- **Purpose:** Sync from Microsoft SQL Server.

**Example:** [05-Config examples](./05-config-examples.md#mssql). Use `--service-type mssql` and `--from-file` pointing to the JSON.

---

## Oracle

- **service_type:** `oracle`
- **Purpose:** Sync from Oracle database.

**Example:** [05-Config examples](./05-config-examples.md#oracle). Use `--service-type oracle`.

---

## S3

- **service_type:** `s3`
- **Purpose:** Sync from Amazon S3 buckets.

**Example:** [05-Config examples](./05-config-examples.md#s3). Sync rules: [sync-rules/s3.md](../../sync-rules/s3.md).

---

## Dir

- **service_type:** `dir`
- **Purpose:** Sync from a local directory.

**Example:** [05-Config examples](./05-config-examples.md#dir).

---

## Other data sources

For all other types in the table (e.g. azure_blob_storage, box, confluence, dropbox, gmail, gitlab, graphql, jira, notion, redis, salesforce, sandfly, servicenow, slack, zoom):

1. **Config:** Prepare a JSON file. **Example JSON for each source is in [05-Config examples](./05-config-examples.md)** (redis, graphql, slack, gitlab, notion, jira, confluence, zoom, salesforce, servicenow, azure_blob_storage, box, dropbox, network_drive, sandfly, etc.). Keys must match the source’s `get_default_configuration()`; include all required and dependency keys for non-interactive create.
2. **Create connector:** Same CLI pattern with the appropriate `--service-type` and `--from-file`.
3. **Create job:** `job start -i <connector_id> -t full` (or incremental / access_control as supported).
4. **Run sync:** `sync-ob -c <config> -i <connector_id>`, or use the long-running Service.

Some sources have sync rule docs, e.g. [sync-rules/SALESFORCE.md](../../sync-rules/SALESFORCE.md), [sync-rules/NOTION.md](../../sync-rules/NOTION.md).

---

[← FAQ and scripts](./03-faq-and-scripts.md) | [Index](./README.md) | [Config examples →](./05-config-examples.md)
