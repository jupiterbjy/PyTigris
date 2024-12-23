"""
Tigris API Client module

:Author: jupiterbjy@gmail.com
"""

from ._client import *
from ._types import *


if __name__ == "__main__":
    # Test code
    import getpass
    from datetime import datetime
    import trio

    async def _main():
        client = TigrisClient(input("Email: "), getpass.getpass("Password: "))

        await client.login()
        await client.index()
        await client.cloud_sso_login()

        start = datetime.fromisoformat("2024-01-01T00:00:00+09:00")
        end = datetime.fromisoformat("2025-01-12T00:00:00+09:00")

        print(start.isoformat())
        print(end.isoformat())
        print(client._site_id)
        print(client._session_id)
        print(client._password_constant)

        events = await client.get_calendar(start, end)

        for event in events:
            print(f"{event.title} - {event.start_datetime} - {event.end_datetime}")

    trio.run(_main)
