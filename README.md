# PyTigris5240

Very rough unofficial client for www.tigrison.com without much(actually just calendar) feature.

Refer reverse-engineering memo in [API_MEMO.md](https://github.com/jupiterbjy/pytigris/blob/master/API_MEMO.md) for internal details.


## Usage

```python
import getpass
from datetime import datetime, timedelta

import pytz
import trio
# also support asyncio as httpx supports it

from pytigris import TigrisClient


async def _fetch_calendar():
    client = TigrisClient(
        input("Email: "),
        getpass.getpass("Password: "),
    )
    await client.login()
    
    end_date = datetime.now(pytz.timezone("Asia/Seoul"))
    start_date = end_date - timedelta(weeks=4)

    for event in await client.get_calendar(
        start_date=start_date,
        end_date=end_date,
    ):
        print(f"{event.title} - {event.start_datetime} - {event.end_datetime}")


trio.run(_fetch_calendar)
```
