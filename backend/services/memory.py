import json
import os
from datetime import datetime

CHAT_FILE = "logs/chat_history.json"

MAX_HISTORY = 5


def get_recent_history():
    """
    Load recent chat messages.
    """

    if not os.path.exists(CHAT_FILE):
        return []

    try:

        with open(
            CHAT_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        return data[-MAX_HISTORY:]

    except Exception:
        return []


def save_chat(
    query: str,
    answer: str,
    confidence: float
):
    """
    Save chat interaction.
    """

    os.makedirs(
        "logs",
        exist_ok=True
    )

    history = []

    if os.path.exists(CHAT_FILE):

        try:

            with open(
                CHAT_FILE,
                "r",
                encoding="utf-8"
            ) as f:

                history = json.load(f)

        except Exception:

            history = []

    history.append(
        {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "answer": answer,
            "confidence": confidence
        }
    )

    with open(
        CHAT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            history,
            f,
            indent=2
        )


def build_memory_context() -> str:
    """
    Convert chat history into prompt context.
    """

    history = get_recent_history()

    if not history:
        return ""

    memory_parts = []

    for item in history:

        memory_parts.append(
            f"User: {item['query']}"
        )

        memory_parts.append(
            f"Assistant: {item['answer']}"
        )

    return "\n".join(
        memory_parts
    )

