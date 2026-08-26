import json
from datetime import datetime, timezone


def handler(event, context):
    name = event.get("name", "World")

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "message": f"Hello, {name}!",
                "receivedEvent": event,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ),
    }
