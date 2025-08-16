from typing import Any

from app.models import ContextSnapshot


async def compile_inputs(ctx: ContextSnapshot, text: str, sliders: dict[str, Any]):
    # Will run NLP, precheck, analytics via asyncio.gather in PR2
    raise NotImplementedError("Implemented in PR2")
