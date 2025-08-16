from typing import Dict, Any
from app.models import ContextSnapshot
import asyncio
async def compile_inputs(ctx: ContextSnapshot, text: str, sliders: Dict[str, Any]):
    # Will run NLP, precheck, analytics via asyncio.gather in PR2
    raise NotImplementedError("Implemented in PR2")
