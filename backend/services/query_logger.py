from datetime import datetime
import json
import os

LOG_FILE = "logs/chat_history.json"


def log_query(
    query: str,
    answer: str,
    confidence: float
):
    """
    Save user queries and responses.
    """

    os.makedirs(
        "logs",
        exist_ok=True
    )

    record = {
        "timestamp": datetime.utcnow().isoformat(),
        "query": query,
        "answer": answer,
        "confidence": confidence
    }

    data = []

    if os.path.exists(LOG_FILE):

        try:

            with open(
                LOG_FILE,
                "r",
                encoding="utf-8"
            ) as f:

                data = json.load(f)

        except Exception:
            data = []

    data.append(record)

    with open(
        LOG_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            indent=4
        )