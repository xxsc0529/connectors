# Config examples by data source

Example JSON for each `service_type` when creating connectors **non-interactively** with `--from-file <JSON>`. Replace placeholders with real values and add/remove keys as needed. Required keys and dependencies follow each source’s `get_default_configuration()` (see `connectors/sources/<name>/datasource.py`).

---

## mysql

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

---

## github

```json
{
  "data_source": "github_cloud",
  "auth_method": "personal_access_token",
  "token": "ghp_yourPAT",
  "repo_type": "other",
  "repositories": ["owner/repo"],
  "ssl_enabled": false,
  "retry_count": 3,
  "use_text_extraction_service": false,
  "use_document_level_security": false
}
```

For GitHub Server use `"data_source": "github_server"` and `"host": "https://your-ghe-host"`. PAT must have `repo`, `user`, `read:org`; Classic PAT (`ghp_`) is recommended.

---

## mongodb

```json
{
  "host": "localhost",
  "user": "",
  "password": "",
  "database": "mydb",
  "collection": "mycoll",
  "direct_connection": false,
  "ssl_enabled": false
}
```

---

## postgresql

```json
{
  "host": "127.0.0.1",
  "port": 5432,
  "username": "postgres",
  "password": "changeme",
  "database": "mydb",
  "schema": "public",
  "tables": "*",
  "fetch_size": 50,
  "retry_count": 3,
  "ssl_enabled": false
}
```

---

## mssql

```json
{
  "host": "127.0.0.1",
  "port": 1433,
  "username": "sa",
  "password": "changeme",
  "database": "mydb",
  "tables": "*",
  "schema": "dbo",
  "fetch_size": 50,
  "retry_count": 3,
  "ssl_enabled": false
}
```

---

## oracle

```json
{
  "host": "127.0.0.1",
  "port": 1521,
  "username": "user",
  "password": "changeme",
  "connection_source": "sid",
  "sid": "ORCL",
  "tables": "*",
  "fetch_size": 50,
  "retry_count": 3
}
```

For Service Name use `"connection_source": "service_name"` and `"service_name": "your_service"` (omit `sid`).

---

## s3

```json
{
  "buckets": ["my-bucket"],
  "aws_access_key_id": "AKIAIOSFODNN7EXAMPLE",
  "aws_secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
  "read_timeout": 90,
  "connect_timeout": 90,
  "max_attempts": 5,
  "page_size": 100,
  "use_text_extraction_service": false
}
```

---

## dir

```json
{
  "directory": "/path/to/local/dir",
  "pattern": "**/*.*"
}
```

---

## redis

```json
{
  "host": "127.0.0.1",
  "port": 6379,
  "username": "",
  "password": "",
  "database": ["*"],
  "ssl_enabled": false
}
```

---

## graphql

```json
{
  "http_endpoint": "https://api.example.com/graphql",
  "http_method": "POST",
  "authentication_method": "none"
}
```

For Basic Auth use `"authentication_method": "basic"` plus `"username"` and `"password"`. For Bearer use `"authentication_method": "bearer"` and `"token"`.

---

## slack

```json
{
  "token": "xoxb-xxx",
  "fetch_last_n_days": 30,
  "auto_join_channels": false,
  "sync_users": true
}
```

---

## gitlab

```json
{
  "token": "glpat-xxx",
  "projects": ["group/project"]
}
```

To sync all accessible projects use `"projects": ["*"]`.

---

## notion

```json
{
  "notion_secret_key": "secret_xxx",
  "databases": ["database_id_1"],
  "pages": ["page_id_1"],
  "index_comments": false,
  "concurrent_downloads": 30
}
```

---

## jira

Jira Cloud example:

```json
{
  "data_source": "jira_cloud",
  "account_email": "user@example.com",
  "api_token": "xxx",
  "jira_url": "https://your-domain.atlassian.net",
  "projects": ["PROJ"],
  "ssl_enabled": true
}
```

For Jira Server use `"data_source": "jira_server"` with `"username"`, `"password"`, and `"jira_url"`.

---

## confluence

Confluence Cloud example:

```json
{
  "data_source": "confluence_cloud",
  "account_email": "user@example.com",
  "api_token": "xxx",
  "confluence_url": "https://your-domain.atlassian.net/wiki",
  "spaces": ["SPACE"]
}
```

For Server or Data Center use `username`/`password` or `data_center_username`/`data_center_password` and the matching `data_source`.

---

## zoom

```json
{
  "account_id": "xxx",
  "client_id": "xxx",
  "client_secret": "xxx",
  "fetch_past_meeting_details": false,
  "recording_age": 12,
  "use_text_extraction_service": false
}
```

---

## salesforce

```json
{
  "domain": "your-domain",
  "client_id": "xxx",
  "client_secret": "xxx",
  "standard_objects_to_sync": ["Account", "Contact", "Lead"],
  "sync_custom_objects": false,
  "use_text_extraction_service": false,
  "use_document_level_security": false
}
```

---

## servicenow

```json
{
  "url": "https://instance.service-now.com",
  "username": "admin",
  "password": "xxx",
  "services": ["*"],
  "retry_count": 3,
  "concurrent_downloads": 10,
  "use_text_extraction_service": false,
  "use_document_level_security": false
}
```

---

## azure_blob_storage

```json
{
  "account_name": "myaccount",
  "account_key": "xxx",
  "blob_endpoint": "https://myaccount.blob.core.windows.net",
  "containers": ["container1"],
  "retry_count": 3,
  "concurrent_downloads": 10,
  "use_text_extraction_service": false
}
```

---

## box

Box Free example:

```json
{
  "is_enterprise": "box_free",
  "client_id": "xxx",
  "client_secret": "xxx",
  "refresh_token": "xxx",
  "concurrent_downloads": 10
}
```

For Box Enterprise use `"is_enterprise": "box_enterprise"` and `"enterprise_id": 12345` (no `refresh_token`).

---

## dropbox

```json
{
  "path": "",
  "app_key": "xxx",
  "app_secret": "xxx",
  "refresh_token": "xxx",
  "retry_count": 3,
  "concurrent_downloads": 10,
  "use_text_extraction_service": false
}
```

---

## network_drive

```json
{
  "username": "user",
  "password": "xxx",
  "server_ip": "192.168.1.1",
  "server_port": 445,
  "drive_path": "\\\\share\\path",
  "use_document_level_security": false
}
```

---

## sandfly

```json
{
  "server_url": "https://server-name/v4",
  "username": "admin",
  "password": "xxx",
  "enable_pass": false,
  "verify_ssl": true,
  "fetch_days": 30
}
```

---

## gmail

Requires OAuth2 or Service Account keys (e.g. `client_id`, `client_secret`, `refresh_token`). See `get_default_configuration()` in `connectors/sources/gmail/datasource.py`.

---

## google_drive

Typically `client_id`, `client_secret`, `refresh_token`, or Service Account config. See `connectors/sources/google_drive/datasource.py`.

---

## google_cloud_storage

Typically `project_id`, `bucket`, and auth (e.g. JSON key or service account). See `connectors/sources/google_cloud_storage/datasource.py`.

---

## onedrive

Typically Microsoft 365 app credentials and `refresh_token`. See `connectors/sources/onedrive/datasource.py`.

---

## outlook

Typically Microsoft 365 app credentials and refresh token. See `connectors/sources/outlook/datasource.py`.

---

## sharepoint_online

Typically `tenant_id`, `client_id`, `client_secret`, `site_collection_path`, etc. See `connectors/sources/sharepoint/sharepoint_online/datasource.py`.

---

## sharepoint_server

Typically `host`, `username`, `password`, `site_collection_path`, etc. See `connectors/sources/sharepoint/sharepoint_server/datasource.py`.

---

## microsoft_teams

Typically Azure AD app and permission-related config. See `connectors/sources/microsoft_teams/datasource.py`.

---

## How to use

1. Save any JSON above to a file (e.g. `mysql-config.json`).
2. Create the connector with that file and the matching `service_type`:
   ```bash
   connectors -c config.yml connector create \
     --name my-conn \
     --index-name my-idx \
     --service-type <type_from_table> \
     --index-language en \
     --from-file mysql-config.json
   ```
3. If the CLI reports a missing key, add it to the JSON (check `get_default_configuration()` in the source’s `datasource.py`).

---

[← Data sources guide](./04-data-sources.md) | [Index](./README.md)
