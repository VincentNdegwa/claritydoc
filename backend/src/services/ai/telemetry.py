import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.models import AIInferenceLog
from src.config import settings


async def log_inference_metrics(
    db: AsyncSession, 
    user_id: uuid.UUID, 
    document_id: uuid.UUID, 
    agent_name: str, 
    meta: dict
) -> None:
    """
    Writes token usage and calculated financial expenditures to the system ledger.
    """
    input_rate = settings.AI_PRICING_INPUT / 1000000
    output_rate = settings.AI_PRICING_OUTPUT / 1000000
    
    cost = (meta["prompt_tokens"] * input_rate) + (meta["completion_tokens"] * output_rate)
    
    log_entry = AIInferenceLog(
        id=uuid.uuid4(),
        user_id=user_id,
        document_id=document_id,
        agent_name=agent_name,
        provider=meta["provider"],
        model_name=meta["model_name"],
        prompt_tokens=meta["prompt_tokens"],
        completion_tokens=meta["completion_tokens"],
        cached_tokens=meta["cached_tokens"],
        estimated_cost_usd=cost,
        latency_ms=meta["latency_ms"],
        status_code=meta["status_code"]
    )
    db.add(log_entry)
    await db.commit()
