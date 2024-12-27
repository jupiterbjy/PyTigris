"""
Unofficial Tigris API Client

:Author: jupiterbjy@gmail.com
"""

import base64
import json
import random
import urllib.parse
from datetime import datetime
from typing import List

import httpx
import pytz

from ._types import (
    CalendarEventData,
    CalendarEvent,
    TigrisCallError,
    TigrisUnexpectedError,
    TigrisLoginError,
)


# --- Globals ---

__all__ = ["TigrisClient"]

# Used to at least not expose string in plain text
_SALT = str(random.randint(0, 32767))


# --- Utilities ---


def _mangle(s: str) -> str:
    """Just bare minimum to mangle strings so it doesn't at least expose raw string"""
    return base64.b64encode((s + _SALT).encode("utf-8")).decode("utf-8")


def _unmangle(s: str) -> str:
    """unmangle mangled string"""
    return base64.b64decode(s.encode("utf-8")).decode("utf-8").removesuffix(_SALT)


# --- Classes ---


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

        self._email = _mangle(email)
        self._password = _mangle(password)

        self.tz = pytz.timezone(tz)

        # it really doesn't matter for race conditions so let's keep it simple

        # WARNING - DO NOT LEAK SITE ID
        # THAT IS ONLY THING SEEMINGLY HOLDING ENTIRE TIGRIS SECURITY
        self._site_id = ""

        # constant password - this does not change but will populate in runtime
        # for extra security
        self._const_pw = ""

        self.client = httpx.AsyncClient()
        # no safe closing needed, we're not sending them anything

    @property
    def _j_session_id(self) -> str:
        """Returns JSESSIONID cookie

        Returns:
            str: JSESSIONID cookie

        Raises:
            TigrisCallError: If JSESSIONID cookie not found
        """

        try:
            return self.client.cookies["JSESSIONID"]
        except KeyError as err:
            raise TigrisCallError(
                "JSESSIONID cookie not found - Is user logged in?"
            ) from err

    @property
    def _session_id(self) -> str:
        """Returns _tigris_sid cookie

        Returns:
            str: _tigris_sid cookie

        Raises:
            TigrisCallError: If _tigris_sid cookie not found
        """

        try:
            return self.client.cookies["_tigris_sid"]
        except KeyError as err:
            raise TigrisCallError(
                "_tigris_sid cookie not found - Is user logged in?"
            ) from err

    async def login(
        self, site_id_override="", email_override="", const_pw_override=""
    ) -> None:
        """Perform full login to Tigris

        Args:
            site_id_override (str, optional): Site ID. Set to override.
            email_override (str, optional): Email. Set to override.
            const_pw_override (str, optional): Constant Password for SSO. Set to override.

        Raises:
            TigrisLoginError: If login fails
            TigrisUnexpectedError: If login fails in unexpected way
        """

        await self._initial_login()
        await self._index()
        await self.cloud_sso_login(site_id_override, email_override, const_pw_override)

    async def _initial_login(self) -> None:
        """Logs in to Tigris

        Raises:
            TigrisLoginError: If login fails
            TigrisUnexpectedError: If login fails in unexpected way
        """

        resp = await self.client.post(
            "https://www.tigrison.com/login",
            data={
                "loginId": _unmangle(self._email),
                "passwd": _unmangle(self._password),
            },
        )

        try:
            resp.raise_for_status()
            data = resp.json()

            # check if it's returned json code is 200, cause it HTTP 200 on failure too
            if data["code"] != 0:
                raise TigrisLoginError(resp.json()["message"])

        except httpx.HTTPError as err:
            raise TigrisUnexpectedError(resp.reason_phrase) from err

        self._site_id = _mangle(data["data"]["siteId"])

    async def _index(self) -> None:
        """Perform index request to retrieve SSO password."""

        resp = await self.client.get(
            "https://www.tigrison.com/hr/index",
            cookies={"_tigris_sid": self._session_id},
        )

        try:
            resp.raise_for_status()

        except httpx.HTTPError as err:
            raise TigrisUnexpectedError(resp.reason_phrase) from err

        url = resp.json()["data"]

        # parse url and fetch loginPassword parameter
        parsed = urllib.parse.urlparse(url)
        self._const_pw = _mangle(
            urllib.parse.parse_qs(parsed.query)["loginPassword"][0]
        )

    async def cloud_sso_login(
        self, site_id_override="", email_override="", const_pw_override=""
    ) -> None:
        """Perform Cloud SSO login.

        Args:
            site_id_override (str, optional): Site ID. Set to override.
            email_override (str, optional): Email. Set to override.
            const_pw_override (str, optional): Constant Password for SSO. Set to override.

        Raises:
            TigrisLoginError: If login fails
            TigrisUnexpectedError: If login fails in unexpected way
        """

        # fail fast
        try:
            assert (
                self._const_pw or const_pw_override
            ), "Missing constant password - Either pass it or login first."
            assert (
                self._site_id or site_id_override
            ), "Missing site ID - Either pass it or login first."
            assert (
                self._email or email_override
            ), "Missing email - Either pass it or login first."
        except AssertionError as err:
            raise TigrisLoginError(err.args[0]) from err

        # fetch
        resp = await self.client.get(
            "https://api.tigris5240.com/cloudSsologinUser.do",
            params={
                "siteId": site_id_override or _unmangle(self._site_id),
                "userMailId": email_override or _unmangle(self._email),
                "loginUserId": email_override or _unmangle(self._email),
                "loginPassword": const_pw_override or _unmangle(self._const_pw),
            },
        )

        try:
            # it could be redirection to main page or redirection to error page.
            if resp.status_code == 302:
                assert (
                    "NoMatchingData.do" not in resp.next_request.url.path
                ), "Contains NoMatchingData.do in url"
            else:
                # otherwise not something we can handle
                resp.raise_for_status()

        except httpx.HTTPError as err:
            raise TigrisUnexpectedError(resp.reason_phrase) from err

        except AssertionError as err:
            raise TigrisLoginError("Invalid login info") from err

    async def _check_login(self) -> None:
        """Used to check if client is logged in before calendar request.

        Raises:
            TigrisLoginError: If login check fails
        """

        resp = await self.client.get(
            "https://api.tigris5240.com/chkLoginSession.do",
            cookies={
                "JSESSIONID": self._j_session_id,
            },
        )

        try:
            resp.raise_for_status()

            # data should have "Login!" string if valid
            data = resp.json()
            assert data["loginInfo"] == "Login!", "Return value was not `Login!`"

        except httpx.HTTPError as err:
            raise TigrisLoginError(resp.reason_phrase) from err

        except AssertionError as err:
            raise TigrisLoginError("Invalid login info - please login again") from err

    async def _set_location_prog_cd_for_log(self) -> None:
        """Set current menu location for unknown reason.
        This is ABSOLUTELY NEEDED to get full event from calendar.
        Otherwise, calendar will only return current logged-in user's teammates.

        Raises:
            TigrisCallError: If request fails due to invalid data or server error
            TigrisUnexpectedError: If request fails in unexpected way
        """

        resp = await self.client.post(
            "https://api.tigris5240.com/setLocationProgCdforLog.do",
            cookies={
                "JSESSIONID": self._j_session_id,
            },
            data={
                "location": "직원 Self Service > 직원(SelfService) > 인사정보 > <span>휴가자조회(달력)  [ TAA-0370 ]</span>",
                "progCd": "TAA-0370",
                "menuCd": "100-0124",
                "dataRwType": "R",
            },
        )

        try:
            resp.raise_for_status()

        except httpx.HTTPError as err:
            if resp.status_code == 500:
                raise TigrisCallError(
                    "Request is missing sufficient data or is an actual server error."
                )

            raise TigrisUnexpectedError(resp.reason_phrase) from err

    async def get_calendar(
        self,
        start_date: datetime,
        end_date: datetime,
        search_org_cd: str = "",
        org_search_type: str = "N",
        search_pos_cd: str = "",
        search_res_cd: str = "",
        teammate_only: bool = False,
    ) -> List[CalendarEvent]:
        """Get calendar data

        Args:
            start_date: Fetch start datetime
            end_date: Fetch end datetime
            search_org_cd: Search organization code
            org_search_type: Search organization type(speculation)
            search_pos_cd: Search position code
            search_res_cd: Search responsibility code
            teammate_only: Only fetch teammate's calendar if True

        Returns:
            List[CalendarEvent]: List of CalendarEvent

        Raises:
            TigrisCallError: If request fails due to invalid request
            TigrisUnexpectedError: If request fails in unexpected way
        """

        if not teammate_only:
            await self._check_login()
            await self._set_location_prog_cd_for_log()

        resp = await self.client.post(
            "https://api.tigris5240.com/TAADclzVcatnCldrMgr.do",
            params={"cmd": "getTAADclzVcatnCldrMgr"},
            data={
                "searchSYmd": start_date.isoformat(),
                "searchEYmd": end_date.isoformat(),
                "cmmSearchOrgCd": search_org_cd,
                "orgSearchType": org_search_type,
                "searchPosCd": search_pos_cd,
                "searchResCd": search_res_cd,
            },
            headers={
                "Referer": "https://api.tigris5240.com/Main.do?result=",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            },
            timeout=None,
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
            raise TigrisUnexpectedError(resp.reason_phrase) from err

        except AssertionError as err:
            raise TigrisCallError("Potentially invalid request cookies") from err

        d: CalendarEventData
        return [CalendarEvent(d, self.tz) for d in data["DATA"]]
