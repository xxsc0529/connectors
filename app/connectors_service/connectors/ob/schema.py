#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
"""
OceanBase 默认表结构，用于模拟 Elasticsearch 的 index/document 模型。

参考 pyobvector 的 data_json_t 设计：每张表用 id + doc(JSON) 存储文档。
"""

# 系统表名（对应 ES 系统索引）
OB_TABLE_CONNECTORS = "ob_connectors"
OB_TABLE_SYNC_JOBS = "ob_connectors_sync_jobs"

# 内容表前缀（ES 索引名会映射为 ob_content_<sanitized_name>）
OB_CONTENT_TABLE_PREFIX = "ob_content_"

# 索引名 -> OB 表名：仅保留 [a-zA-Z0-9_]，其余替换为 _
def index_name_to_table_name(index_name: str) -> str:
    sanitized = "".join(c if c.isalnum() or c == "_" else "_" for c in index_name)
    return f"{OB_CONTENT_TABLE_PREFIX}{sanitized}".strip("_")


def get_connectors_table_ddl() -> str:
    """Connector 元数据表 DDL（模拟 .elastic-connectors-v1）。"""
    return f"""
CREATE TABLE IF NOT EXISTS {OB_TABLE_CONNECTORS} (
    id VARCHAR(512) NOT NULL PRIMARY KEY COMMENT 'connector id',
    doc JSON NOT NULL COMMENT 'connector document body'
);
"""


def get_sync_jobs_table_ddl() -> str:
    """同步任务元数据表 DDL（模拟 .elastic-connectors-sync-jobs-v1）。"""
    return f"""
CREATE TABLE IF NOT EXISTS {OB_TABLE_SYNC_JOBS} (
    id VARCHAR(512) NOT NULL PRIMARY KEY COMMENT 'sync job id',
    doc JSON NOT NULL COMMENT 'sync job document body'
);
"""


def get_content_table_ddl(table_name: str) -> str:
    """内容表 DDL（模拟 ES 普通索引，如 mysql-demo）。"""
    return f"""
CREATE TABLE IF NOT EXISTS `{table_name}` (
    id VARCHAR(512) NOT NULL PRIMARY KEY COMMENT 'document _id',
    doc JSON NOT NULL COMMENT 'document _source',
    _timestamp TIMESTAMP NULL DEFAULT NULL COMMENT 'for incremental sync'
);
"""


# ES 索引名到 OB 系统表名映射（框架使用的具体索引名）
ES_CONNECTORS_INDEX = ".elastic-connectors-v1"
ES_JOBS_INDEX = ".elastic-connectors-sync-jobs-v1"


def es_index_to_ob_table(index_name: str) -> str:
    """将 ES 索引名映射为 OceanBase 表名。"""
    if index_name == ES_CONNECTORS_INDEX or index_name == ".elastic-connectors":
        return OB_TABLE_CONNECTORS
    if index_name == ES_JOBS_INDEX or index_name == ".elastic-connectors-sync-jobs":
        return OB_TABLE_SYNC_JOBS
    return index_name_to_table_name(index_name)
