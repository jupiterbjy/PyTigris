"""
Tigris API Client module

:Author: jupiterbjy@gmail.com
"""

from ._client import *
from ._types import *


__version__ = "0.2a"


def _standalone_demo():
    """Standalone demo. Used for module testing."""

    import getpass
    from datetime import datetime
    import asyncio

    _id, _pw = input("Email: "), getpass.getpass("Password: ")

    # noinspection PyProtectedMember
    async def _main():

        client = TigrisClient(_id, _pw)

        await client.login()

        print(client._site_id)
        print(client._session_id)
        print(client._const_pw)

        start = datetime.fromisoformat("2024-11-01T00:00:00+09:00")
        end = datetime.fromisoformat("2025-01-12T00:00:00+09:00")

        print(start.isoformat())
        print(end.isoformat())

        events = await client.get_calendar(start, end, teammate_only=False)

        for event in events:
            print(f"{event.title} - {event.start_datetime} - {event.end_datetime}")

    asyncio.run(_main())


if __name__ == "__main__":
    _standalone_demo()
