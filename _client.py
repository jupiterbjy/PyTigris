"""
Unofficial Tigris API Client

:Author: jupiterbjy@gmail.com
:version: 0
"""


import urllib.parse

import httpx


class TigrisLoginError(Exception):
    pass


class TigrisClient:
    def __init__(self, email: str, password: str):
        self._email = email
        self._password = password

        # WARNING - DO NOT LEAK SITE ID
        # THAT IS ONLY THING SEEMINGLY HOLDING ENTIRE TIGRIS SECURITY
        self._site_id = ""

        # honestly not sure if this is even used
        self._session_id = ""

        # constant password - this does not change but will populate in runtime
        # for extra security
        self._password_constant = ""

        self.client = httpx.AsyncClient()

    async def login(self) -> None:
        """Logs in to Tigris

        Raises:
            TigrisLoginError: If login fails
        """

        resp = await self.client.post(
            "https://www.tigrison.com/login",
            data={
                "siteId": "",
                "timeZoneId": "Asia/Seoul",
                "recaptchaToken": "",
                "loginId": self._email,
                "passwd": self._password
            },
            headers={
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            }
        )

        try:
            resp.raise_for_status()
            data = resp.json()

            # check if it's returned json code is 200, cause it HTTP 200 on failure too
            if data["code"] != 200:
                raise TigrisLoginError(resp.json()["message"])

        except httpx.HTTPError as err:
            raise TigrisLoginError(resp.reason_phrase) from err

        self._site_id = data["siteId"]

        # saved in cookie but to reuse without login
        self._session_id = data["sessionId"]

    async def index(self) -> None:
        """Perform index request to retrieve SSO password."""

        resp = await self.client.get(
            "https://www.tigrison.com/hr/index",
            cookies={
                "_tigris_sid": self._session_id
            }
        )

        url = resp.json()["data"]

        # parse url and fetch loginPassword parameter
        parsed = urllib.parse.urlparse(url)
        self._password_constant = urllib.parse.parse_qs(parsed.query)["loginPassword"][0]

    async def cloud_sso_login(self) -> None:
        """Perform Cloud SSO login"""

        resp = await self.client.get(
            "https://www.tigrison.com/cloudSsologinUser.do",
            params={
                "siteId": self._site_id,
                "userMailId": self._email,
                "loginUserId": self._email,
                "loginPassword": self._password_constant,
                "multiLangCd": "ko"
            }
        )