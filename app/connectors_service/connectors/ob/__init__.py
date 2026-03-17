#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
"""
OceanBase 后端：用默认表结构（id + doc JSON）模拟 Elasticsearch。

参考 pyobvector 的 data 表设计，提供 OBManagementClient 与 schema 定义。
"""

from connectors.ob.schema import (
    OB_TABLE_CONNECTORS,
    OB_TABLE_SYNC_JOBS,
    OB_CONTENT_TABLE_PREFIX,
    index_name_to_table_name,
    es_index_to_ob_table,
    get_connectors_table_ddl,
    get_sync_jobs_table_ddl,
    get_content_table_ddl,
)
from connectors.ob.client import OBManagementClient

__all__ = [
    "OBManagementClient",
    "OB_TABLE_CONNECTORS",
    "OB_TABLE_SYNC_JOBS",
    "OB_CONTENT_TABLE_PREFIX",
    "index_name_to_table_name",
    "es_index_to_ob_table",
    "get_connectors_table_ddl",
    "get_sync_jobs_table_ddl",
    "get_content_table_ddl",
]
