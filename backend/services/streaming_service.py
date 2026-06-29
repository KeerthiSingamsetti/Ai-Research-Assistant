import asyncio

async def stream_answer(answer: str):

    words = answer.split()

    for word in words:

        yield {
            "event": "message",
            "data": word + " "
        }

        await asyncio.sleep(0.05)

    yield {
        "event": "end",
        "data": "[DONE]"
    }