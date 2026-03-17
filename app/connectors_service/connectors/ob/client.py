#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
"""
OceanBase 客户端：用默认表结构模拟 Elasticsearch，供 Connectors 写入/查询。

使用方式：配置中设置 backend: oceanbase 及 oceanbase.* 连接信息后，
由框架在合适处注入 OBManagementClient 替代 ESManagementClient。
"""

import json
import logging
import re

from connectors.es import TIMESTAMP_FIELD
from connectors.ob.schema import (
    ES_CONNECTORS_INDEX,
    ES_JOBS_INDEX,
    get_connectors_table_ddl,
    get_content_table_ddl,
    get_sync_jobs_table_ddl,
    es_index_to_ob_table,
)

logger = logging.getLogger(__name__)


def _sanitize_table_name(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_]", "_", name).strip("_") or "default"


class OBManagementClient:
    """
    使用 OceanBase 默认表结构（id + doc JSON）模拟 ES 的 index/document 行为。
    实现 ESManagementClient 的接口子集，供 Connectors 同步与元数据读写使用。
    """

    def __init__(self, config: dict):
        self.config = config
        self._host = config.get("host", "127.0.0.1")
        self._port = int(config.get("port", 2881))
        self._user = config.get("user", "root@test")
        self._password = config.get("password", "")
        self._database = config.get("database") or config.get("db_name", "connectors")
        self._pool = None

    async def wait(self):
        """兼容 PreflightCheck：建立连接并返回伪版本信息。"""
        await self._get_pool()
        return {"version": {"number": "1.0", "build_flavor": ""}}

    async def _get_pool(self):
        """Lazy 创建 aiomysql 连接池（OceanBase MySQL 模式）。"""
        if self._pool is not None:
            return self._pool
        try:
            import aiomysql
        except ImportError:
            raise RuntimeError(
                "OceanBase backend requires aiomysql. Install with: pip install aiomysql"
            )
        self._pool = await aiomysql.create_pool(
            host=self._host,
            port=self._port,
            user=self._user,
            password=self._password,
            db=self._database,
            minsize=1,
            maxsize=10,
        )
        return self._pool

    async def close(self):
        if self._pool:
            self._pool.close()
            await self._pool.wait_closed()
            self._pool = None

    async def _execute(self, sql: str, args=None, one: bool = False):
        try:
            import aiomysql
        except ImportError:
            raise RuntimeError("aiomysql required for OceanBase backend")
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(sql, args or ())
                if one:
                    return await cur.fetchone()
                return await cur.fetchall()

    async def _execute_many(self, sql: str, args_list: list):
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.executemany(sql, args_list)
            await conn.commit()

    async def _execute_write(self, sql: str, args=None):
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql, args or ())
            await conn.commit()

    async def ensure_exists(self, indices=None):
        """确保系统表及指定“索引”对应的表存在。"""
        if indices is None:
            indices = []
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                for idx in indices:
                    table = es_index_to_ob_table(idx)
                    if table in ("ob_connectors", "ob_connectors_sync_jobs"):
                        ddl = (
                            get_connectors_table_ddl()
                            if table == "ob_connectors"
                            else get_sync_jobs_table_ddl()
                        )
                    else:
                        ddl = get_content_table_ddl(table)
                    for stmt in ddl.strip().split(";"):
                        stmt = stmt.strip()
                        if stmt:
                            await cur.execute(stmt)
            await conn.commit()
        logger.debug("OB ensure_exists done for indices: %s", indices)

    async def index_exists(self, index_name: str) -> bool:
        """对应表是否存在。"""
        table = es_index_to_ob_table(index_name)
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT 1 FROM information_schema.tables "
                    "WHERE table_schema = %s AND table_name = %s",
                    (self._database, table),
                )
                row = await cur.fetchone()
        return row is not None

    async def get_index_or_alias(self, index_name: str, ignore_unavailable: bool = False):
        """兼容 SyncOrchestrator.prepare_content_index：存在则返回非 None。"""
        if await self.index_exists(index_name):
            return {index_name: {}}
        return None

    async def has_active_license_enabled(self, license_):
        """OceanBase 无 ES 许可证概念，始终视为已满足。"""
        from connectors.es.client import License
        return True, getattr(License, "PLATINUM", license_)

    async def create_content_index(self, search_index_name: str, language_code: str):
        """创建内容表（language_code 在 OB 默认表结构中未使用）。"""
        table = es_index_to_ob_table(search_index_name)
        ddl = get_content_table_ddl(table)
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                for stmt in ddl.strip().split(";"):
                    stmt = stmt.strip()
                    if stmt:
                        await cur.execute(stmt)
            await conn.commit()
        return None

    async def delete_indices(self, indices):
        """删除对应表（若存在）。"""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                for index_name in indices:
                    table = es_index_to_ob_table(index_name)
                    await cur.execute(f"DROP TABLE IF EXISTS `{table}`")
            await conn.commit()

    async def upsert(self, _id: str, index_name: str, doc: dict):
        """单条写入/更新（REPLACE INTO）。"""
        table = es_index_to_ob_table(index_name)
        doc_json = json.dumps(doc, default=str)
        sql = f"REPLACE INTO `{table}` (id, doc) VALUES (%s, %s)"
        await self._execute_write(sql, (_id, doc_json))

    async def bulk_insert(self, operations: list, pipeline: str = None):
        """
        解析 ES 风格 bulk 操作列表，转为 OB 的 REPLACE/DELETE。
        operations: [ { "index": { "_index", "_id" } }, doc, { "delete": { ... } }, ... ]
        """
        try:
            import aiomysql
        except ImportError:
            raise RuntimeError("aiomysql required for OceanBase backend")
        table_ops = {}  # table -> { "index": [(id, doc), ...], "delete": [id, ...] }
        i = 0
        while i < len(operations):
            op_item = operations[i]
            if isinstance(op_item, dict):
                if "index" in op_item:
                    meta = op_item["index"]
                    idx = meta.get("_index")
                    doc_id = meta.get("_id")
                    if i + 1 < len(operations):
                        doc = operations[i + 1]
                        if idx not in table_ops:
                            table_ops[idx] = {"index": [], "delete": []}
                        table_ops[idx]["index"].append((doc_id, doc))
                    i += 2
                    continue
                if "update" in op_item:
                    meta = op_item["update"]
                    idx = meta.get("_index")
                    doc_id = meta.get("_id")
                    if i + 1 < len(operations):
                        body = operations[i + 1]
                        doc = body.get("doc", {})
                        if body.get("doc_as_upsert"):
                            if idx not in table_ops:
                                table_ops[idx] = {"index": [], "delete": []}
                            table_ops[idx]["index"].append((doc_id, doc))
                    i += 2
                    continue
                if "delete" in op_item:
                    meta = op_item["delete"]
                    idx = meta.get("_index")
                    doc_id = meta.get("_id")
                    if idx not in table_ops:
                        table_ops[idx] = {"index": [], "delete": []}
                    table_ops[idx]["delete"].append(doc_id)
                    i += 1
                    continue
            i += 1

        items = []
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                for index_name, ops in table_ops.items():
                    table = es_index_to_ob_table(index_name)
                    with_ts = []
                    without_ts = []
                    for doc_id, doc in ops.get("index", []):
                        doc_json = json.dumps(doc, default=str)
                        ts = doc.get(TIMESTAMP_FIELD)
                        if ts is not None:
                            with_ts.append((doc_id, doc_json, ts))
                        else:
                            without_ts.append((doc_id, doc_json))
                    if with_ts:
                        await cur.executemany(
                            f"REPLACE INTO `{table}` (id, doc, _timestamp) VALUES (%s, %s, %s)",
                            with_ts,
                        )
                        for (doc_id, _, _) in with_ts:
                            items.append({"index": {"_id": doc_id, "_index": index_name, "result": "created"}})
                    if without_ts:
                        await cur.executemany(
                            f"REPLACE INTO `{table}` (id, doc) VALUES (%s, %s)",
                            without_ts,
                        )
                        for (doc_id, _) in without_ts:
                            items.append({"index": {"_id": doc_id, "_index": index_name, "result": "created"}})
                    deletes = ops.get("delete", [])
                    if deletes:
                        await cur.executemany(
                            f"DELETE FROM `{table}` WHERE id = %s",
                            [(doc_id,) for doc_id in deletes],
                        )
                        for doc_id in deletes:
                            items.append({"delete": {"_id": doc_id, "_index": index_name, "result": "deleted"}})
            await conn.commit()
        return {"errors": False, "items": items}

    async def yield_existing_documents_metadata(self, index_name: str):
        """迭代 (doc_id, _timestamp)。"""
        try:
            import aiomysql
        except ImportError:
            raise RuntimeError("aiomysql required for OceanBase backend")
        if not await self.index_exists(index_name):
            return
        table = es_index_to_ob_table(index_name)
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    f"SELECT id, JSON_UNQUOTE(JSON_EXTRACT(doc, %s)) AS ts FROM `{table}`",
                    (f"$.{TIMESTAMP_FIELD}",),
                )
                while True:
                    row = await cur.fetchone()
                    if not row:
                        break
                    yield row.get("id"), row.get("ts")

    async def list_indices(self, index_pattern: str = "*"):
        """列出内容表（模拟 ES indices），返回 { index_name: { "docs_count": N } }。"""
        pool = await self._get_pool()
        out = {}
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = %s AND table_name LIKE %s",
                    (self._database, "ob_content_%"),
                )
                rows = await cur.fetchall()
                for (tname,) in rows:
                    # 表名 -> 逻辑索引名：去掉 ob_content_ 前缀，_ 可还原为 -
                    logical = tname.replace("ob_content_", "", 1).replace("_", "-")
                    await cur.execute(
                        f"SELECT COUNT(*) FROM `{tname}`"
                    )
                    cnt = (await cur.fetchone())[0]
                    out[logical] = {"docs_count": cnt}
        return out
