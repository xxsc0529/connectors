# FAQ and scripts (OceanBase backend)

FAQ (config path, token scopes, etc.), two ways to populate content tables, and verify_ob_connector / sync-ob usage.

---

## 1. FAQ

1. **"Cannot create a connector-specific API key..."**  
   In OceanBase mode no ES API key is created; this message can be ignored.

2. **Config file not found / `-c`: No such file or directory**  
   The `-c` path is **relative to the current working directory**. If you run from the repo root and the config is in `app/connectors_service/`, use `connectors -c app/connectors_service/<filename> ...`, or `cd app/connectors_service` first then `-c <filename>`. An absolute path also works.

3. **aiomysql errors**  
   Install: `pip install aiomysql`, and confirm OceanBase is using the MySQL protocol port.

4. **Too many prompts on connector create**  
   Use `--from-file <JSON>` with all keys required by that service-type (see [04-Data sources](./04-data-sources.md)) for fully non-interactive create.

5. **Why is the content table empty?**  
   The CLI only creates connector/job records and content table schema in OceanBase. **Data is written by the Connector Service or the one-off sync script.** See “Populating content tables” below.

6. **job start doesn’t print “The job xxx has been started.”**  
   If the code fix for `if job_id` is in place, it should print; otherwise check that `job start` returns a valid job_id.

---

## 2. Populating content tables: two options

### Option A: One-off sync (recommended first)

After installing the wheel, from any directory, with a pending full job already created:

```bash
sync-ob -c config.yml -i <connector_id>
```

If there is no pending job, create one with the CLI:

```bash
connectors -c config.yml job start -i <connector_id> -t full
```

Then run `sync-ob`. It pulls data from the source and writes to the OceanBase table `ob_content_<index_name_sanitized>`.

**Optional:** `-j <job_id>` to run a specific job; otherwise the first pending full/incremental job for that connector is used.

### Option B: Long-running Connector Service

Config must include `backend: oceanbase`, `oceanbase`, and `connectors` (list of connector_id and service_type), plus the default `service`/`sources`. Then start:

```bash
elastic-ingest -c /path/to/config.yml
```

The service will poll OceanBase for pending jobs and run syncs, writing results to OceanBase content tables.

---

## 3. verify_ob_connector (verify OB state)

Connects to OceanBase and lists system/content tables and row counts. After installing the wheel, run as a module:

```bash
# With config file (recommended)
python -m scripts.verify_ob_connector -c config.yml

# With environment variables
OB_HOST=127.0.0.1 OB_PORT=2881 OB_USER=root@test OB_PASSWORD=xxx OB_DB=test \
  python -m scripts.verify_ob_connector
```

**Output:** Table list, row counts for `ob_connectors` / `ob_connectors_sync_jobs` and sample rows, and document counts for each `ob_content_*` table.

---

## 4. sync-ob (one-off sync)

Runs one pending full or incremental sync for a connector and writes results to OceanBase content tables. **Standalone command** (not a subcommand of `connectors`).

**Usage:**

```bash
sync-ob -c <config.yml> -i <connector_id> [-j <job_id>]
```

| Argument | Description |
|----------|-------------|
| `-c` / `--config` | Required. Path to YAML with `backend: oceanbase` and `oceanbase` |
| `-i` / `--connector-id` | Required. Connector ID |
| `-j` / `--job-id` | Optional. Job to run; default is first pending full/incremental for that connector |

**Requirements:** Config has `backend: oceanbase` and `oceanbase`; the connector exists in OceanBase and has a pending full or incremental job (e.g. create with `connectors -c config.yml job start -i <connector_id> -t full`).

---

## 5. Code optimizations (dev reference)

| Module | Change |
|--------|--------|
| **connectors_cli.py** | Fix job start success branch: `if job` → `if job_id` so “The job xxx has been started.” is printed |
| **ob/client.py** | **bulk_insert:** batch REPLACE/DELETE per table with `executemany`; **yield_existing_documents_metadata:** use `DictCursor` for row parsing |
| **ob/cli_backend.py** | **get_connector_by_index:** query by index name with `JSON_EXTRACT(doc, '$.index_name')`; **count:** return 0 for empty/invalid index |
| **verify_ob_connector.py** | Support `-c` for YAML or env vars `OB_HOST`, `OB_PORT`, `OB_USER`, `OB_PASSWORD`, `OB_DB` |

---

[← Backend design](./02-backend-design.md) | [Index](./README.md) | [Data sources →](./04-data-sources.md)
