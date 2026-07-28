import asyncio
import re

async def stream_answer(answer: str):

    sentences = re.split(r'(?<=[.!?])\s+', answer)

    for sentence in sentences:

        yield {
            "event": "message",
            "data": sentence
        }

        await asyncio.sleep(0.05)

    yield {
        "event": "end",
        "data": "[DONE]"
    }