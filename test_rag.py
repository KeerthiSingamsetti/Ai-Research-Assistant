import asyncio

from backend.services.rag_pipeline import (
    generate_answer
)


async def main():

    result = await generate_answer(
        "What is Artificial Intelligence?"
    )

    print(result)


if __name__ == "__main__":
    asyncio.run(main())