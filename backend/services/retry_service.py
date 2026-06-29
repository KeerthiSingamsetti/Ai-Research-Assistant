import asyncio


async def retry_async(
    func,
    retries: int = 3,
    delay: int = 1
):
    """
    Retry async operations.
    """

    for attempt in range(retries):

        try:
            return await func()

        except Exception:

            if attempt == retries - 1:
                raise

            await asyncio.sleep(delay)