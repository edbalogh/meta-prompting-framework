"""Implementation of a langgraph checkpoint saver using Postgres."""
from typing import Any, AsyncIterator, Generator, Optional, Union
import time

import psycopg
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint import BaseCheckpointSaver
from langgraph.serde.jsonplus import JsonPlusSerializer
from langgraph.checkpoint.base import Checkpoint, CheckpointMetadata, CheckpointTuple
from psycopg_pool import AsyncConnectionPool, ConnectionPool

class PostgresSaver(BaseCheckpointSaver):
    def __init__(
        self,
        sync_connection: Optional[Union[psycopg.Connection, ConnectionPool]] = None,
        async_connection: Optional[Union[psycopg.AsyncConnection, AsyncConnectionPool]] = None,
    ):
        super().__init__(serde=JsonPlusSerializer())
        self.sync_connection = sync_connection
        self.async_connection = async_connection

    CREATE_TABLES_QUERY = """
    CREATE TABLE IF NOT EXISTS checkpoints (
        thread_id TEXT NOT NULL,
        thread_ts TEXT NOT NULL,
        parent_ts TEXT,
        checkpoint BYTEA NOT NULL,
        metadata BYTEA NOT NULL,
        PRIMARY KEY (thread_id, thread_ts)
    );
    """

    @staticmethod
    def create_tables(connection: Union[psycopg.Connection, ConnectionPool]) -> None:
        with connection.cursor() as cur:
            cur.execute(PostgresSaver.CREATE_TABLES_QUERY)

    @staticmethod
    async def acreate_tables(connection: Union[psycopg.AsyncConnection, AsyncConnectionPool]) -> None:
        async with connection.cursor() as cur:
            await cur.execute(PostgresSaver.CREATE_TABLES_QUERY)

    UPSERT_CHECKPOINT_QUERY = """
    INSERT INTO checkpoints (thread_id, thread_ts, parent_ts, checkpoint, metadata)
    VALUES (%s, %s, %s, %s, %s)
    ON CONFLICT (thread_id, thread_ts)
    DO UPDATE SET checkpoint = EXCLUDED.checkpoint, metadata = EXCLUDED.metadata;
    """

    def put(self, config: RunnableConfig, checkpoint: Checkpoint, metadata: CheckpointMetadata) -> RunnableConfig:
        thread_id = config["configurable"]["thread_id"]
        parent_ts = config["configurable"].get("thread_ts")
        with self.sync_connection.cursor() as cur:
            cur.execute(
                self.UPSERT_CHECKPOINT_QUERY,
                (
                    thread_id,
                    checkpoint["ts"],
                    parent_ts,
                    self.serde.dumps(checkpoint),
                    self.serde.dumps(metadata),
                ),
            )
        return {
            "configurable": {
                "thread_id": thread_id,
                "thread_ts": checkpoint["ts"],
            },
        }

    async def aput(self, config: RunnableConfig, checkpoint: Checkpoint, metadata: CheckpointMetadata) -> RunnableConfig:
        thread_id = config["configurable"]["thread_id"]
        parent_ts = config["configurable"].get("thread_ts")
        async with self.async_connection.cursor() as cur:
            await cur.execute(
                self.UPSERT_CHECKPOINT_QUERY,
                (
                    thread_id,
                    checkpoint["ts"],
                    parent_ts,
                    self.serde.dumps(checkpoint),
                    self.serde.dumps(metadata),
                ),
            )
        return {
            "configurable": {
                "thread_id": thread_id,
                "thread_ts": checkpoint["ts"],
            },
        }

    LIST_CHECKPOINTS_QUERY = """
    SELECT checkpoint, metadata, thread_ts, parent_ts
    FROM checkpoints
    WHERE thread_id = %s
    ORDER BY thread_ts DESC
    """

    def list(self, config: RunnableConfig, *, filter: Optional[dict[str, Any]] = None, before: Optional[RunnableConfig] = None, limit: Optional[int] = None) -> Generator[CheckpointTuple, None, None]:
        thread_id = config["configurable"]["thread_id"]
        with self.sync_connection.cursor() as cur:
            cur.execute(self.LIST_CHECKPOINTS_QUERY, (thread_id,))
            for checkpoint, metadata, thread_ts, parent_ts in cur:
                yield CheckpointTuple(
                    config={"configurable": {"thread_id": thread_id, "thread_ts": thread_ts}},
                    checkpoint=self.serde.loads(checkpoint),
                    metadata=self.serde.loads(metadata),
                    parent_config={"configurable": {"thread_id": thread_id, "thread_ts": parent_ts}} if parent_ts else None,
                )

    async def alist(self, config: RunnableConfig, *, filter: Optional[dict[str, Any]] = None, before: Optional[RunnableConfig] = None, limit: Optional[int] = None) -> AsyncIterator[CheckpointTuple]:
        thread_id = config["configurable"]["thread_id"]
        async with self.async_connection.cursor() as cur:
            await cur.execute(self.LIST_CHECKPOINTS_QUERY, (thread_id,))
            async for checkpoint, metadata, thread_ts, parent_ts in cur:
                yield CheckpointTuple(
                    config={"configurable": {"thread_id": thread_id, "thread_ts": thread_ts}},
                    checkpoint=self.serde.loads(checkpoint),
                    metadata=self.serde.loads(metadata),
                    parent_config={"configurable": {"thread_id": thread_id, "thread_ts": parent_ts}} if parent_ts else None,
                )

    GET_CHECKPOINT_QUERY = """
    SELECT checkpoint, metadata, thread_ts, parent_ts
    FROM checkpoints
    WHERE thread_id = %s AND thread_ts = %s
    """

    def get_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        thread_id = config["configurable"]["thread_id"]
        thread_ts = config["configurable"].get("thread_ts")
        with self.sync_connection.cursor() as cur:
            cur.execute(self.GET_CHECKPOINT_QUERY, (thread_id, thread_ts))
            result = cur.fetchone()
            if result:
                checkpoint, metadata, thread_ts, parent_ts = result
                return CheckpointTuple(
                    config=config,
                    checkpoint=self.serde.loads(checkpoint),
                    metadata=self.serde.loads(metadata),
                    parent_config={"configurable": {"thread_id": thread_id, "thread_ts": parent_ts}} if parent_ts else None,
                )
        return None

    async def aget_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        thread_id = config["configurable"]["thread_id"]
        thread_ts = config["configurable"].get("thread_ts")
        async with self.async_connection.cursor() as cur:
            await cur.execute(self.GET_CHECKPOINT_QUERY, (thread_id, thread_ts))
            result = await cur.fetchone()
            if result:
                checkpoint, metadata, thread_ts, parent_ts = result
                return CheckpointTuple(
                    config=config,
                    checkpoint=self.serde.loads(checkpoint),
                    metadata=self.serde.loads(metadata),
                    parent_config={"configurable": {"thread_id": thread_id, "thread_ts": parent_ts}} if parent_ts else None,
                )
        return None

    async def on_llm_start(self, run_id: str, **kwargs):
        # Implement logic for LLM start if needed
        pass

    async def on_llm_end(self, run_id: str, response: Any):
        # Implement logic for LLM end if needed
        pass

    async def on_llm_error(self, run_id: str, error: Union[Exception, KeyboardInterrupt]):
        # Implement logic for LLM error if needed
        pass

    async def complete_run(self, run_id: str, outputs: dict):
        # Implement logic for completing a run if needed
        pass
