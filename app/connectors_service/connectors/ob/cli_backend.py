#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0;
#
"""
OceanBase 作为 CLI 后端：实现 ConnectorIndex / SyncJobIndex 接口，供 connector/job/index 命令使用。
"""

import json
import logging
import uuid
from datetime import datetime, timezone, timedelta

from connectors_sdk.utils import iso_utc

from connectors.ob.client import OBManagementClient
from connectors.ob.schema import (
    OB_TABLE_CONNECTORS,
    OB_TABLE_SYNC_JOBS,
    es_index_to_ob_table,
    index_name_to_table_name,
)
from connectors.protocol import (
    CONCRETE_CONNECTORS_INDEX,
    CONCRETE_JOBS_INDEX,
    Connector,
    JobStatus,
    JobTriggerMethod,
    JobType,
    SyncJob,
)
from connectors.protocol.connectors import (
    INDEXED_DOCUMENT_COUNT,
    INDEXED_DOCUMENT_VOLUME,
    DELETED_DOCUMENT_COUNT,
    IDLE_JOBS_THRESHOLD,
)

logger = logging.getLogger(__name__)


def _doc_row_to_source(row: dict):
    """OB 行 (id, doc) -> ESDocument 期望的 doc_source { _id, _source }。"""
    doc_id = row.get("id")
    doc = row.get("doc")
    if isinstance(doc, str):
        doc = json.loads(doc) if doc else {}
    return {"_id": doc_id, "_source": doc}


class OBCLIClient(OBManagementClient):
    """CLI 用的 OceanBase 客户端，与 ESManagementClient 接口一致。"""

    async def clean_index(self, index_name: str):
        table = es_index_to_ob_table(index_name)
        await self._execute_write(f"DELETE FROM `{table}`")
        return {"deleted": 0}


class _OBConnectorIndexClient:
    """供 Connector.document_count() 使用的伪 client：提供 indices.refresh 与 count。"""

    def __init__(self, ob_client: OBManagementClient):
        self._client = ob_client

    @property
    def indices(self):
        class _Indices:
            def __init__(self, c):
                self._c = c
            async def refresh(self, index=None, ignore_unavailable=True):
                pass
        return _Indices(self._client)

    async def count(self, index=None, ignore_unavailable=True):
        from connectors.ob.schema import index_name_to_table_name, OB_CONTENT_TABLE_PREFIX
        index = index or ""
        if not index or not index.strip():
            return {"count": 0}
        table = index_name_to_table_name(index)
        if not table or not table.startswith(OB_CONTENT_TABLE_PREFIX):
            return {"count": 0}
        try:
            import aiomysql
        except ImportError:
            return {"count": 0}
        pool = await self._client._get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(f"SELECT COUNT(*) FROM `{table}`")
                row = await cur.fetchone()
        return {"count": row[0] if row else 0}


class OBConnectorIndex:
    """用 ob_connectors 表实现 ConnectorIndex 的 CLI 所需接口。"""

    def __init__(self, config: dict):
        self._client = OBManagementClient(config)
        self.index_name = ".elastic-connectors"
        self.feature_use_connectors_api = False
        self.serverless = False
        self.client = _OBConnectorIndexClient(self._client)

    async def close(self):
        await self._client.close()

    def stop_waiting(self):
        pass

    def _create_object(self, doc_source: dict) -> Connector:
        return Connector(self, doc_source)

    async def all_connectors(self):
        try:
            import aiomysql
        except ImportError:
            raise RuntimeError("aiomysql required for OceanBase backend")
        pool = await self._client._get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    f"SELECT id, doc FROM `{OB_TABLE_CONNECTORS}`"
                )
                while True:
                    row = await cur.fetchone()
                    if not row:
                        break
                    doc = row.get("doc")
                    if isinstance(doc, str):
                        doc = json.loads(doc) if doc else {}
                    doc_source = {"_id": row["id"], "_source": doc}
                    yield self._create_object(doc_source)

    async def fetch_by_id(self, doc_id: str) -> Connector:
        try:
            import aiomysql
        except ImportError:
            raise RuntimeError("aiomysql required for OceanBase backend")
        pool = await self._client._get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    f"SELECT id, doc FROM `{OB_TABLE_CONNECTORS}` WHERE id = %s",
                    (doc_id,),
                )
                row = await cur.fetchone()
        if not row:
            from connectors.es.index import DocumentNotFoundError
            raise DocumentNotFoundError(
                f"Couldn't find document in {OB_TABLE_CONNECTORS} by id {doc_id}"
            )
        doc_source = _doc_row_to_source(row)
        return self._create_object(doc_source)

    async def fetch_response_by_id(self, doc_id: str) -> dict:
        """供 ESDocument.reload() 使用，返回 { _id, _source }。"""
        try:
            import aiomysql
        except ImportError:
            raise RuntimeError("aiomysql required for OceanBase backend")
        pool = await self._client._get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    f"SELECT id, doc FROM `{OB_TABLE_CONNECTORS}` WHERE id = %s",
                    (doc_id,),
                )
                row = await cur.fetchone()
        if not row:
            from connectors.es.index import DocumentNotFoundError
            raise DocumentNotFoundError(
                f"Couldn't find document in {OB_TABLE_CONNECTORS} by id {doc_id}"
            )
        return _doc_row_to_source(row)

    async def get_connector_by_index(self, index_name: str):
        try:
            import aiomysql
        except ImportError:
            raise RuntimeError("aiomysql required for OceanBase backend")
        pool = await self._client._get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    "SELECT id, doc FROM `{}` WHERE JSON_UNQUOTE(JSON_EXTRACT(doc, %s)) = %s LIMIT 1".format(
                        OB_TABLE_CONNECTORS
                    ),
                    ("$.index_name", index_name),
                )
                row = await cur.fetchone()
        if not row:
            return None
        doc = row.get("doc")
        if isinstance(doc, str):
            doc = json.loads(doc) if doc else {}
        return self._create_object({"_id": row["id"], "_source": doc})

    async def index(self, doc: dict) -> dict:
        doc_id = str(uuid.uuid4()).replace("-", "")[:20]
        await self._client.upsert(doc_id, CONCRETE_CONNECTORS_INDEX, doc)
        return {"_id": doc_id}

    async def update(self, doc_id: str, doc: dict, if_seq_no=None, if_primary_term=None):
        """部分更新：先读后合并再写入，供 Connector.sync_starts / sync_done 等使用。"""
        try:
            import aiomysql
        except ImportError:
            raise RuntimeError("aiomysql required for OceanBase backend")
        pool = await self._client._get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    f"SELECT id, doc FROM `{OB_TABLE_CONNECTORS}` WHERE id = %s",
                    (doc_id,),
                )
                row = await cur.fetchone()
        if not row:
            return
        current = row.get("doc")
        if isinstance(current, str):
            current = json.loads(current) if current else {}
        current.update(doc)
        await self._client.upsert(doc_id, CONCRETE_CONNECTORS_INDEX, current)

    async def has_active_license_enabled(self, license_):
        """OceanBase 无 ES 许可证概念，始终视为已满足。"""
        from connectors.es.client import License
        return True, License.PLATINUM

    async def supported_connectors(self, native_service_types=None, connector_ids=None):
        """Yield connectors matching native_service_types or connector_ids (used by job_scheduling)."""
        if native_service_types is None:
            native_service_types = []
        if connector_ids is None:
            connector_ids = []
        if not native_service_types and not connector_ids:
            return
        async for connector in self.all_connectors():
            if getattr(connector, "deleted", False):
                continue
            if connector_ids and connector.id in connector_ids:
                yield connector
                continue
            if native_service_types and getattr(connector, "is_native", False) and getattr(connector, "service_type", None) in native_service_types:
                yield connector


class OBSyncJobIndex:
    """用 ob_connectors_sync_jobs 表实现 SyncJobIndex 的 CLI 所需接口。"""

    def __init__(self, config: dict):
        self._client = OBManagementClient(config)
        self.index_name = ".elastic-connectors-sync-jobs"
        self.feature_use_connectors_api = False

    async def close(self):
        await self._client.close()

    def stop_waiting(self):
        pass

    def _create_object(self, doc_source: dict) -> SyncJob:
        return SyncJob(self, doc_source)

    async def fetch_by_id(self, doc_id: str) -> SyncJob:
        try:
            import aiomysql
        except ImportError:
            raise RuntimeError("aiomysql required for OceanBase backend")
        pool = await self._client._get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    f"SELECT id, doc FROM `{OB_TABLE_SYNC_JOBS}` WHERE id = %s",
                    (doc_id,),
                )
                row = await cur.fetchone()
        if not row:
            from connectors.es.index import DocumentNotFoundError
            raise DocumentNotFoundError(
                f"Couldn't find job in {OB_TABLE_SYNC_JOBS} by id {doc_id}"
            )
        doc_source = _doc_row_to_source(row)
        return self._create_object(doc_source)

    async def fetch_response_by_id(self, doc_id: str) -> dict:
        """供 ESDocument.reload() 使用，返回 { _id, _source }。"""
        try:
            import aiomysql
        except ImportError:
            raise RuntimeError("aiomysql required for OceanBase backend")
        pool = await self._client._get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    f"SELECT id, doc FROM `{OB_TABLE_SYNC_JOBS}` WHERE id = %s",
                    (doc_id,),
                )
                row = await cur.fetchone()
        if not row:
            from connectors.es.index import DocumentNotFoundError
            raise DocumentNotFoundError(
                f"Couldn't find job in {OB_TABLE_SYNC_JOBS} by id {doc_id}"
            )
        return _doc_row_to_source(row)

    async def create(self, connector, trigger_method, job_type):
        job_id = str(uuid.uuid4()).replace("-", "")[:20]
        filtering = connector.filtering.get_active_filter().transform_filtering()
        index_name = connector.index_name
        if job_type == JobType.ACCESS_CONTROL:
            from connectors.protocol import CONNECTORS_ACCESS_CONTROL_INDEX_PREFIX
            index_name = f"{CONNECTORS_ACCESS_CONTROL_INDEX_PREFIX}{index_name}"
        job_def = {
            "connector": {
                "id": connector.id,
                "filtering": filtering,
                "index_name": index_name,
                "language": connector.language,
                "pipeline": connector.pipeline.data,
                "service_type": connector.service_type,
                "configuration": connector.configuration.to_dict(),
            },
            "trigger_method": trigger_method.value,
            "job_type": job_type.value,
            "status": JobStatus.PENDING.value,
            INDEXED_DOCUMENT_COUNT: 0,
            INDEXED_DOCUMENT_VOLUME: 0,
            DELETED_DOCUMENT_COUNT: 0,
            "created_at": iso_utc(),
            "last_seen": iso_utc(),
        }
        await self._client.upsert(job_id, CONCRETE_JOBS_INDEX, job_def)
        return job_id

    async def get_all_docs(self, query=None, sort=None, page_size=100):
        try:
            import aiomysql
        except ImportError:
            raise RuntimeError("aiomysql required for OceanBase backend")
        pool = await self._client._get_pool()
        rows = []
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    f"SELECT id, doc FROM `{OB_TABLE_SYNC_JOBS}`"
                )
                while True:
                    row = await cur.fetchone()
                    if not row:
                        break
                    doc = row.get("doc")
                    if isinstance(doc, str):
                        doc = json.loads(doc) if doc else {}
                    rows.append({"_id": row["id"], "_source": doc})

        # 内存过滤 query（简化：只支持 term connector.id / term _id）
        if query and isinstance(query.get("bool"), dict):
            must = query["bool"].get("must") or []
            for clause in must:
                if isinstance(clause, dict) and "term" in clause:
                    term = clause["term"]
                    if "connector.id" in term:
                        cid = term["connector.id"]
                        rows = [r for r in rows if r["_source"].get("connector", {}).get("id") == cid]
                    elif "_id" in term:
                        jid = term["_id"]
                        rows = [r for r in rows if r["_id"] == jid]
                    break
            filter_clause = query["bool"].get("filter") or []
            for clause in filter_clause:
                if isinstance(clause, dict) and "term" in clause:
                    term = clause["term"]
                    if "connector.index_name" in term:
                        iname = term["connector.index_name"]
                        rows = [r for r in rows if r["_source"].get("connector", {}).get("index_name") == iname]
                    break

        if sort:
            for s in (sort or [])[::-1]:
                if isinstance(s, dict) and "created_at" in s:
                    order = s.get("created_at", "asc")
                    rows.sort(key=lambda r: r["_source"].get("created_at") or "", reverse=(order == "desc"))
                    break

        for r in rows:
            yield self._create_object(r)

    async def update(self, doc_id, doc, if_seq_no=None, if_primary_term=None):
        try:
            import aiomysql
        except ImportError:
            raise RuntimeError("aiomysql required for OceanBase backend")
        pool = await self._client._get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    f"SELECT id, doc FROM `{OB_TABLE_SYNC_JOBS}` WHERE id = %s",
                    (doc_id,),
                )
                row = await cur.fetchone()
        if not row:
            return
        current = row.get("doc")
        if isinstance(current, str):
            current = json.loads(current) if current else {}
        current.update(doc)
        await self._client.upsert(doc_id, CONCRETE_JOBS_INDEX, current)

    async def pending_jobs(self, connector_ids, job_types):
        """Yield pending/suspended jobs for given connector_ids and job_types (Service 拉取待执行任务用)."""
        if not job_types:
            return
        if not isinstance(job_types, list):
            job_types = [str(job_types)]
        cid_set = set(connector_ids or [])
        type_set = set(job_types)
        pending_statuses = (JobStatus.PENDING.value, JobStatus.SUSPENDED.value)
        # 拉取全部 job 后在内存过滤、排序
        try:
            import aiomysql
        except ImportError:
            raise RuntimeError("aiomysql required for OceanBase backend")
        pool = await self._client._get_pool()
        rows = []
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(f"SELECT id, doc FROM `{OB_TABLE_SYNC_JOBS}`")
                while True:
                    row = await cur.fetchone()
                    if not row:
                        break
                    doc = row.get("doc")
                    if isinstance(doc, str):
                        doc = json.loads(doc) if doc else {}
                    cid = (doc.get("connector") or {}).get("id")
                    if cid not in cid_set:
                        continue
                    if doc.get("status") not in pending_statuses:
                        continue
                    if doc.get("job_type") not in type_set:
                        continue
                    rows.append({"_id": row["id"], "_source": doc})
        rows.sort(key=lambda r: r["_source"].get("created_at") or "")
        for r in rows:
            yield self._create_object(r)

    async def orphaned_idle_jobs(self, connector_ids):
        """Jobs in progress/canceling whose connector.id not in connector_ids."""
        connector_ids_set = set(connector_ids or [])
        async for job in self.get_all_docs(query=None):
            cid = job.connector.id if hasattr(job, "connector") else (job.__dict__.get("_source") or {}).get("connector", {}).get("id")
            if cid in connector_ids_set:
                continue
            status = getattr(job, "status", None) or (job.__dict__.get("_source") or {}).get("status")
            if status in (JobStatus.IN_PROGRESS.value, JobStatus.CANCELING.value):
                yield job

    async def idle_jobs(self, connector_ids):
        """Jobs in progress/canceling for given connector_ids with last_seen too old."""
        connector_ids_set = set(connector_ids or [])
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=IDLE_JOBS_THRESHOLD)
        async for job in self.get_all_docs(query=None):
            cid = job.connector.id if hasattr(job, "connector") else (job.__dict__.get("_source") or {}).get("connector", {}).get("id")
            if cid not in connector_ids_set:
                continue
            src = job.__dict__.get("_source") or {}
            if src.get("status") not in (JobStatus.IN_PROGRESS.value, JobStatus.CANCELING.value):
                continue
            last_seen = src.get("last_seen")
            if not last_seen:
                continue
            try:
                if isinstance(last_seen, str):
                    dt = datetime.fromisoformat(last_seen.replace("Z", "+00:00"))
                else:
                    dt = last_seen
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                if dt > cutoff:
                    continue
            except Exception:
                continue
            yield job
