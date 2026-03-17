#!/usr/bin/env python3
"""
一次性将指定 connector 的 pending full/incremental 同步任务执行到 OceanBase 内容表。

用法（任选其一，无需在源码目录）:
  # 源码或可编辑安装时（在 app/connectors_service 下）:
  .venv/bin/python scripts/sync_ob.py -c config.yml -i <connector_id>
  # 安装为 whl 后，任意目录均可:
  python -m scripts.sync_ob -c config.yml -i <connector_id>
  sync-ob -c config.yml -i <connector_id>

依赖：配置文件中需包含 backend: oceanbase、oceanbase: {...}、sources（或使用默认），且 connector 已在 OceanBase 中存在并有 pending job。
"""
import argparse
import asyncio
import os
import sys

# 源码下运行时保证可导入 connectors；whl 安装后可省略
_src_parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _src_parent not in sys.path:
    sys.path.insert(0, _src_parent)


async def main():
    parser = argparse.ArgumentParser(description="Run one sync job to OceanBase content table")
    parser.add_argument("-c", "--config", required=True, help="Path to config YAML (backend: oceanbase)")
    parser.add_argument("-i", "--connector-id", required=True, dest="connector_id", help="Connector ID")
    parser.add_argument("-j", "--job-id", default=None, dest="job_id", help="Specific job ID (default: first pending)")
    args = parser.parse_args()

    from connectors.config import load_config
    from connectors.utils import get_source_klass
    from connectors.sync_job_runner import SyncJobRunner
    from connectors.protocol import JobType
    from connectors.es.index import DocumentNotFoundError

    try:
        from connectors.ob.cli_backend import OBConnectorIndex, OBSyncJobIndex
    except ImportError:
        print("OB backend not available (aiomysql?). pip install aiomysql")
        sys.exit(1)

    config = load_config(args.config)
    if config.get("backend") != "oceanbase" or not config.get("oceanbase"):
        print("Config must contain backend: oceanbase and oceanbase: {...}")
        sys.exit(1)

    ob_config = dict(config["oceanbase"])
    ob_config["backend"] = "oceanbase"
    service_config = config.get("service", {})
    sources = config.get("sources", {})

    connector_index = OBConnectorIndex(ob_config)
    sync_job_index = OBSyncJobIndex(ob_config)
    try:
        connector = await connector_index.fetch_by_id(args.connector_id)
    except DocumentNotFoundError:
        print(f"Connector not found: {args.connector_id}")
        sys.exit(1)
    finally:
        await connector_index.close()

    service_type = getattr(connector, "service_type", None)
    if not service_type or service_type not in sources:
        print(f"Connector service_type={service_type} not in config sources")
        sys.exit(1)
    source_klass = get_source_klass(sources[service_type])

    if args.job_id:
        try:
            sync_job = await sync_job_index.fetch_by_id(args.job_id)
        except DocumentNotFoundError:
            print(f"Job not found: {args.job_id}")
            sys.exit(1)
        src = getattr(sync_job, "_source", sync_job.__dict__.get("_source") or {})
        if src.get("connector", {}).get("id") != args.connector_id:
            print(f"Job {args.job_id} does not belong to connector {args.connector_id}")
            sys.exit(1)
    else:
        sync_job = None
        async for job in sync_job_index.pending_jobs(
            connector_ids=[args.connector_id],
            job_types=[JobType.FULL.value, JobType.INCREMENTAL.value],
        ):
            sync_job = job
            break
        if sync_job is None:
            print(f"No pending full/incremental job for connector {args.connector_id}. Create one with: connectors job start -i {args.connector_id} -t full")
            sys.exit(1)

    await sync_job_index.close()

    runner = SyncJobRunner(
        source_klass=source_klass,
        sync_job=sync_job,
        connector=connector,
        es_config=ob_config,
        service_config=service_config,
    )
    print(f"Running sync job {sync_job.id} (connector {args.connector_id}, type {sync_job.job_type}) -> OceanBase ...")
    try:
        await runner.execute()
        print("Sync finished.")
    except Exception as e:
        print(f"Sync failed: {e}")
        sys.exit(1)


def _run():
    asyncio.run(main())


if __name__ == "__main__":
    _run()
