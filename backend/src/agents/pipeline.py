import uuid
from loguru import logger
from src.queue.config import enqueue_job


class AgentOrchestrator:
    async def trigger_analysis_pipeline(
        self, 
        document_id: uuid.UUID, 
        version_id: uuid.UUID, 
        storage_path: str, 
        user_id: uuid.UUID
    ) -> str:
        job_id = await enqueue_job(
            "execute_pipeline_lifecycle",
            document_id=document_id,
            version_id=version_id,
            storage_path=storage_path,
            user_id=user_id
        )
        logger.info(f"Successfully enqueued pipeline job {job_id} for document: {document_id}")
        return job_id


agent_orchestrator = AgentOrchestrator()
