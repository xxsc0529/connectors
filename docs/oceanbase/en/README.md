# OceanBase Backend Documentation Index

Documentation for using **OceanBase** as the Connectors backend (without Elasticsearch). Use this index to find topics or data sources quickly.

---

## Document List

| Document | Description |
|----------|-------------|
| [01-Quick start](./01-quickstart.md) | **Wheel install**, config, `connectors` / `sync-ob` command reference, verification |
| [02-Backend design](./02-backend-design.md) | Table layout, index-to-table naming, DDL |
| [03-FAQ and scripts](./03-faq-and-scripts.md) | FAQ, populating content tables, verify_ob_connector / sync-ob, code notes |
| [04-Data sources guide](./04-data-sources.md) | Configuration and usage for each connector (MySQL, GitHub, MongoDB, S3, etc.) |
| [05-Config examples](./05-config-examples.md) | **Example JSON per data source for `--from-file`** (copy and edit) |

---

## Quick lookup

### By topic

| Task | Document and section |
|------|------------------------|
| Run CLI for the first time (install wheel) | [01-Quick start](./01-quickstart.md) → Install, config, typical flow, command reference |
| Look up a CLI command (connectors / sync-ob) | [01-Quick start](./01-quickstart.md) → CLI command reference |
| Config `-c` error: No such file or directory | [03-FAQ and scripts](./03-faq-and-scripts.md) → Config file not found |
| Understand OB tables | [02-Backend design](./02-backend-design.md) → Table layout, naming |
| Content table empty / how to sync | [03-FAQ and scripts](./03-faq-and-scripts.md) → Populating content tables |
| Verify OB with script | [03-FAQ and scripts](./03-faq-and-scripts.md) → verify_ob_connector |
| Code optimizations / dev reference | [03-FAQ and scripts](./03-faq-and-scripts.md) → Code optimizations |
| Run a one-off sync (sync-ob) | [03-FAQ and scripts](./03-faq-and-scripts.md) → sync-ob |
| Configure MySQL and sync to OB | [04-Data sources](./04-data-sources.md) → MySQL |
| Configure GitHub and sync to OB | [04-Data sources](./04-data-sources.md) → GitHub |
| Configure other sources | [04-Data sources](./04-data-sources.md) → Data source list, generic flow |
| Copy example JSON for a source | [05-Config examples](./05-config-examples.md) → find by service_type |

### By data source (service_type)

| service_type | Description | Section |
|--------------|-------------|---------|
| mysql | MySQL database | [04-Data sources](./04-data-sources.md)#mysql |
| github | GitHub (issues, PRs, files) | [04-Data sources](./04-data-sources.md)#github |
| mongodb | MongoDB | [04-Data sources](./04-data-sources.md)#mongodb |
| postgresql | PostgreSQL | [04-Data sources](./04-data-sources.md)#postgresql |
| mssql | Microsoft SQL Server | [04-Data sources](./04-data-sources.md)#mssql |
| oracle | Oracle database | [04-Data sources](./04-data-sources.md)#oracle |
| s3 | Amazon S3 | [04-Data sources](./04-data-sources.md)#s3 |
| dir | Local directory | [04-Data sources](./04-data-sources.md)#dir |
| Others | See data source list and examples | [04-Data sources](./04-data-sources.md)#data-source-list, [05-Config examples](./05-config-examples.md) |

---

## See also

- [CLI.md](../../CLI.md) — Connectors CLI (including Elasticsearch)
- [CONFIG.md](../../CONFIG.md) — Configuration reference

**[中文文档](../zh/README.md)**
