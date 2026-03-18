# OceanBase modifications (compliance notice)

This repository is based on the upstream project: https://github.com/elastic/connectors

## What we changed

We modified the upstream Connectors codebase to add an **OceanBase backend** (MySQL-protocol) so that:

1. The CLI can manage connectors/jobs against OceanBase (instead of Elasticsearch).
2. Connector metadata and sync job metadata are stored in OceanBase system tables.
3. Connector content (documents) are written into OceanBase content tables.
4. A one-off sync CLI command/script (`sync-ob`) is provided to run pending full/incremental jobs and populate OceanBase content tables.
5. Documentation under `docs/oceanbase/` is added/updated to describe configuration, commands, scripts, and examples for the OceanBase backend.

## Files and components added/updated

Key OceanBase-related code and entry points:

- `app/connectors_service/connectors/ob/` (OceanBase backend implementation)
  - OceanBase client / schema / CLI backend integration
- `app/connectors_service/scripts/sync_ob.py` (one-off sync runner)
- `app/connectors_service/pyproject.toml` (CLI entry point: `sync-ob`)

Key OceanBase documentation:

- `docs/oceanbase/` (Chinese/English quick start, backend design, FAQ/scripts, data sources, config examples)

## License / notices

This repository is distributed under **Elastic License 2.0** (see `LICENSE` in the repository root).

If you copy or distribute any portion of this modified work, you must ensure that recipients also receive:

- The applicable license terms (see `LICENSE`)
- Any relevant upstream notices included with the repository
- Prominent notices that you have modified the software (this file)

## Notes

This notice is intended to satisfy “prominent notices” requirements for derivative works.

