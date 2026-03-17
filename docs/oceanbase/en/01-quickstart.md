# Quick start (OceanBase backend)

This page describes using OceanBase as the Connectors backend: **install via the wheel package**, then use the `connectors` and `sync-ob` commands for configuration, creating connectors, starting jobs, and one-off sync.

---

## 1. Prerequisites

1. **OceanBase instance** (MySQL protocol, e.g. 4.x/5.x)
   - Target database already created (e.g. `test`). The CLI will create system and content tables in it.
2. **Install the Connectors package** via the wheel or from source (see §2). The OceanBase backend depends on `aiomysql`, which is installed with the package.

---

## 2. Install (wheel package)

The dependency `elasticsearch-connectors-sdk` is not on PyPI; it lives in this repo under `libs/connectors_sdk`. **Install the SDK first, then the wheel.**

From the **repository root** (the directory that contains `app` and `libs`):

```bash
# 1. Install the local SDK (once)
pip install ./libs/connectors_sdk

# 2. Install the wheel, or install from source
pip install ./app/connectors_service/dist/elasticsearch_connectors-*.whl
```

If you have not built the wheel yet:

```bash
pip install ./libs/connectors_sdk
pip install ./app/connectors_service
```

After install, you can use `connectors` and `sync-ob` from any directory.

### 2.1 Build the wheel (optional)

To build the wheel yourself, from `app/connectors_service`:

```bash
pip install build
python -m build --wheel
```

The wheel is written to `dist/`, e.g. `dist/elasticsearch_connectors-9.4.0-py3-none-any.whl`.

---

## 3. Configuration

### 3.1 Config structure

The CLI uses `backend: oceanbase` and an `oceanbase` section:

```yaml
backend: oceanbase
oceanbase:
  host: "127.0.0.1"
  port: 2881
  user: "root@test"
  password: "your_password"
  db_name: "test"
```

| Field | Description |
|-------|-------------|
| host / port | OceanBase host and port (MySQL protocol) |
| user / password | Login (tenant allowed, e.g. `root@test`) |
| db_name or database | Database name for system and content tables |

### 3.2 Config file path (`-c`)

Use a separate YAML for OceanBase and pass it with `-c`. **The path is relative to the current working directory.** After installing the wheel you can run from any directory; prefer an absolute path or a clear relative path to avoid "No such file or directory".

- From the **directory that contains the config**: `connectors -c test-ob-config.yml ...`
- From the **repo root** with config in `app/connectors_service/`: `connectors -c app/connectors_service/test-ob-config.yml ...`
- Or run `cd app/connectors_service` first, then use `-c test-ob-config.yml`.

```bash
connectors -c /path/to/config-oceanbase.yml <subcommand> ...
sync-ob -c /path/to/config-oceanbase.yml -i <connector_id>
```

---

## 4. CLI command reference

All commands below use `-c <OceanBase config>` with the installed `connectors` command.

| Action | Example |
|--------|---------|
| Help | `connectors --help` / `connectors -c config.yml --help` |
| List connectors | `connectors -c config.yml connector list` |
| Create connector | `connectors -c config.yml connector create --index-name <name> --service-type <type> --name <name> --index-language en --from-file <JSON>` |
| List indices | `connectors -c config.yml index list` |
| Clean index | `connectors -c config.yml index clean <index_name>` |
| Delete index | `connectors -c config.yml index delete <index_name>` |
| List jobs for a connector | `connectors -c config.yml job list <connector_id>` |
| Start job | `connectors -c config.yml job start -i <connector_id> -t full` (or `incremental` / `access_control`) |
| View job | `connectors -c config.yml job view <job_id>` |
| Cancel job | `connectors -c config.yml job cancel <job_id>` |
| One-off sync to OceanBase | `sync-ob -c config.yml -i <connector_id>` (standalone command, not a subcommand of `connectors`) |

**About connector_id:** It is generated when you create a connector and printed in the output (e.g. `Connector ... ID: 50064af25b174ed9abec ... has been created!`). Commands like `job list`, `job start`, and `sync-ob` must target a specific connector, so **connector_id cannot be omitted**. To see existing IDs, run `connectors -c config.yml connector list`.

**Note:** `login` is for Elasticsearch; not needed when using only OceanBase.

---

## 5. Typical flow (data into OceanBase)

1. **Install:** SDK then wheel (see §2).  
2. **Prepare config:** OceanBase YAML and data source JSON (see [04-Data sources](./04-data-sources.md), [05-Config examples](./05-config-examples.md)).  
3. **Create connector:** `connectors -c config.yml connector create ... --from-file <source.json>`, note the **Connector ID**.  
4. **Start job:** `connectors -c config.yml job start -i <connector_id> -t full`.  
5. **Run sync:** `sync-ob -c config.yml -i <connector_id>` to write data into OceanBase content tables.

---

## 6. Minimal verification

From any directory (replace `config.yml` with your config path; remember `-c` is relative to cwd, see 3.2):

```bash
# 1. CLI and connectivity
connectors --help
connectors -c config.yml connector list
connectors -c config.yml index list

# 2. If you have a connector, test job
connectors -c config.yml job list <connector_id>
connectors -c config.yml job start -i <connector_id> -t full
# Expected: "The job <job_id> has been started."

# 3. One-off sync to OceanBase
sync-ob -c config.yml -i <connector_id>

# 4. Verify OB tables and row counts (if script is installed)
python -m scripts.verify_ob_connector -c config.yml
```

---

## 7. Generic connector create template

Non-interactive create uses `--from-file` with a JSON whose keys match the data source config (see [04-Data sources](./04-data-sources.md)):

```bash
connectors -c config.yml connector create \
  --name <display_name> \
  --index-name <index_name> \
  --service-type <mysql|github|mongodb|...> \
  --index-language en \
  --from-file <path-to-config.json>
```

On success you get a **Connector ID**. The message "Cannot create a connector-specific API key..." can be ignored when using OceanBase.

---

[← Index](./README.md) | [Backend design →](./02-backend-design.md)
