"""
Unofficial Tigris API Client

:Author: jupiterbjy@gmail.com
"""

import json
import urllib.parse
from datetime import datetime, timedelta
from typing import List

import httpx

from ._types import CalendarEventData, CalendarEvent


class TigrisLoginError(Exception):
    """Tigris login error"""

    pass


class TigrisCloudSSOError(Exception):
    """Tigris Cloud SSO login error"""

    pass


class TigrisCallError(Exception):
    """Tigris call error"""

    pass


class TigrisClient:
    """
    Tigris unofficial API Client
    """

    def __init__(self, email: str, password: str, tz: str = "Asia/Seoul"):
        """Initialize Tigris Client

        Args:
            email (str): Tigris email
            password (str): Tigris password
            tz (str, optional): Timezone. Defaults to "Asia/Seoul".
        """

        self._email = email
        self._password = password

        self.tz = tz

        # WARNING - DO NOT LEAK SITE ID
        # THAT IS ONLY THING SEEMINGLY HOLDING ENTIRE TIGRIS SECURITY
        self._site_id = ""

        # constant password - this does not change but will populate in runtime
        # for extra security
        self._password_constant = ""

        self.client = httpx.AsyncClient()
        # no safe closing needed, we're not sending them anything

    @property
    def _j_session_id(self) -> str:
        try:
            return self.client.cookies["JSESSIONID"]
        except KeyError:
            return ""

    @property
    def _session_id(self) -> str:
        try:
            return self.client.cookies["_tigris_sid"]
        except KeyError:
            return ""

    async def login(self) -> None:
        """Logs in to Tigris

        Raises:
            TigrisLoginError: If login fails
        """

        resp = await self.client.post(
            "https://www.tigrison.com/login",
            data={
                "siteId": "",
                "timeZoneId": self.tz,
                "recaptchaToken": "",
                "loginId": self._email,
                "passwd": self._password,
            },
            headers={
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            },
        )

        try:
            resp.raise_for_status()
            data = resp.json()

            # check if it's returned json code is 200, cause it HTTP 200 on failure too
            if data["code"] != 0:
                raise TigrisLoginError(resp.json()["message"])

        except httpx.HTTPError as err:
            raise TigrisLoginError(resp.reason_phrase) from err

        self._site_id = data["data"]["siteId"]

    async def index(self) -> None:
        """Perform index request to retrieve SSO password."""

        resp = await self.client.get(
            "https://www.tigrison.com/hr/index",
            cookies={"_tigris_sid": self._session_id},
        )

        url = resp.json()["data"]

        # parse url and fetch loginPassword parameter
        parsed = urllib.parse.urlparse(url)
        self._password_constant = urllib.parse.parse_qs(parsed.query)["loginPassword"][
            0
        ]

    async def cloud_sso_login(self, site_id="", email="", password="") -> None:
        """Perform Cloud SSO login.

        Args:
            site_id (str, optional): Site ID. Set to override.
            email (str, optional): Email. Set to override.
            password (str, optional): Password. Set to override.
        """

        resp = await self.client.get(
            "https://api.tigris5240.com/cloudSsologinUser.do",
            params={
                "siteId": self._site_id if site_id == "" else site_id,
                "userMailId": self._email if email == "" else email,
                "loginUserId": self._email if email == "" else email,
                "loginPassword": (
                    self._password_constant if password == "" else password
                ),
                "multiLangCd": "ko",
            },
            headers={
                "Connection": "keep-alive",
            },
        )

        try:
            # check 302 first
            if resp.status_code == 302:
                assert (
                    "NoMatchingData.do" not in resp.next_request.url.path
                ), "Contains NoMatchingData.do in url"
            else:
                resp.raise_for_status()

        except httpx.HTTPError as err:
            raise TigrisCloudSSOError(resp.reason_phrase) from err

        except AssertionError as err:
            raise TigrisCloudSSOError("Invalid login info") from err

    async def check_login(self) -> None:
        resp = await self.client.get(
            "https://api.tigris5240.com/chkLoginSession.do",
            cookies={
                "JSESSIONID": self._j_session_id,
            },
        )

        try:
            resp.raise_for_status()

            data = resp.json()
            assert data["loginInfo"] == "Login!", "Return value was not `Login!`"

        except httpx.HTTPError as err:
            raise TigrisCloudSSOError(resp.reason_phrase) from err

        except AssertionError as err:
            raise TigrisCloudSSOError("Invalid login info") from err

    async def get_calendar(
        self, start_date: datetime, end_date: datetime
    ) -> List[CalendarEvent]:
        """Get calendar data

        Args:
            start_date: Fetch start datetime
            end_date: Fetch end datetime

        Returns:
            List[CalendarEvent]: List of CalendarEvent
        """

        # await self.check_login()

        resp = await self.client.post(
            "https://api.tigris5240.com/TAADclzVcatnCldrMgr.do",
            cookies={
                # "JSESSIONID": self._j_session_id,
                "colShowYn": "N",
                "kiwiboxSaveChk": "true",
                "menuShow": "Y",
            },
            params={"cmd": "getTAADclzVcatnCldrMgr"},
            data={
                "searchSYmd": start_date.isoformat(),
                "searchEYmd": end_date.isoformat(),
                "cmmSearchOrgCd": "",
                "orgSearchType": "N",
                "searchPosCd": "",
                "searchResCd": "",
            },
            headers={
                "Host": "api.tigris5240.com",
                "Origin": "https://api.tigris5240.com",
                "Sec-Ch-Ua": '"Microsoft Edge";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"Windows"',
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
                "Referer": "https://api.tigris5240.com/TAADclzVcatnCldrMgr.do?cmd=viewTAADclzVcatnCldrMgr",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.142.86 Safari/537.36",
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Accept-Language": "ko,en;q=0.9,en-US;q=0.8",
                "Dnt": "1",
                "x-requested-with": "XMLHttpRequest",
                "Connection": "keep-alive",
                "Pragma": "no-cache",
                "Cache-Control": "no-cache",
            },
        )

        try:
            # check 302 first
            if resp.status_code == 302:
                raise TigrisCallError("Possibly invalid request header")
            else:
                resp.raise_for_status()

            data = await resp.aread()
            data = json.loads(data.decode("utf-8"))

            assert len(data["DATA"]), "DATA is empty"

        except httpx.HTTPError as err:
            # TODO: Change message for 302
            raise TigrisCallError(resp.reason_phrase) from err

        except AssertionError as err:
            raise TigrisCallError("Potentially invalid request cookies") from err

        return [CalendarEvent(d) for d in data["DATA"]]
