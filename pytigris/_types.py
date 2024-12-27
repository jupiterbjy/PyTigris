"""
Data Type definitions for type hinting.
This naming follows the original API's naming, thus it's not PEP8 compliant

:Author: jupiterbjy@gmail.com
"""

from datetime import datetime
from functools import cached_property
from typing import TypedDict, Optional


__all__ = [
    "TigrisLoginError",
    "TigrisUnexpectedError",
    "TigrisCallError",
    "CalendarEventData",
    "CalendarEvent",
]

import pytz


class TigrisLoginError(Exception):
    """Tigris login error"""

    pass


class TigrisUnexpectedError(Exception):
    """Tigris Cloud SSO login error"""

    pass


class TigrisCallError(Exception):
    """Tigris call error"""

    pass


class CalendarEventData(TypedDict):
    """Typed dictionary class representing calendar event data.

    Note:
        See parameters at https://github.com/jupiterbjy/PyTigris5240/blob/main/API_MEMO.md#success-2
    """

    kind: Optional[str]
    title: Optional[str]
    leavNm: Optional[str]
    leavCd: Optional[int]
    personInfo: Optional[str]
    orgCd: Optional[str]
    orgNm: Optional[str]
    posCd: Optional[str]
    posNm: Optional[str]
    resCd: Optional[str]
    resNm: Optional[str]
    wktypeCd: Optional[str]
    wktypeNm: Optional[str]
    staYmd: Optional[str]
    endYmd: Optional[str]
    endYmdAdd: Optional[str]
    agentName: Optional[str]
    allDay: Optional[bool]
    staHm: Optional[str]
    endHm: Optional[str]
    reqStatusCd: Optional[str]
    reason: Optional[str]
    note: Optional[str]


class CalendarEvent:
    """Class representing a calendar event

    Attributes:
        tz: pytz.BaseTzInfo, The timezone of the event provided by TigrisClient
        kind: str, The type of event. `vacation` usually
        title: str, Title of the event. Has (△) sign if it's not approved yet
        leave_name: str, Name of the vacation in Korean
        leave_code: int, Unique identifier for the vacation type
        person_info: str, Information about the person responsible in `{orgNm}/{resNm}/{posNm}/{wktypeNm}` format. set to `///` if it's global vacation
        organization_code: Optional[str], Organizational code
        organization_name: Optional[str], Organizational name
        position_code: Optional[str], Position code
        position_name: Optional[str], Position name
        responsibility_code: Optional[str], Responsibility code
        responsibility_name: Optional[str], Responsibility name (i.e. team leader)
        work_type_code: Optional[str], Work type code
        work_type_name: Optional[str], Work type name
        start_year_month_day: str, Start date of the vacation in YYYY-MM-DD format, else YYYYMMDD format
        end_year_month_day: str, End date of the vacation in YYYY-MM-DD format if personal, else YYYYMMDD format
        end_ymd_add: Optional[str], Immediate day after `endYmd` in YYYY-MM-DD format
        agent_name: Optional[str], Agent name
        is_full_day: bool, Whether the vacation is a full-day or half-day
        start_hour_minute: Optional[str], Start hour of the vacation in THHMMSS format
        end_hour_minute: Optional[str], End hour of the vacation in THHMMSS format
        request_status_code: Optional[str], Status code indicating whether the request was approved or rejected
        reason: Optional[str], Reason for taking the vacation
        note: Optional[str], Additional information written by requesters
    """

    def __init__(self, data: CalendarEventData, tz: pytz.BaseTzInfo):
        self.tz = tz
        self._src_data = data
        self.kind = data["kind"]
        self.title = data["title"]
        self.leave_name = data["leavNm"]
        self.leave_code = data["leavCd"]
        self.person_info = data["personInfo"]
        self.organization_code: Optional[str] = data["orgCd"]
        self.organization_name: Optional[str] = data["orgNm"]
        self.position_code: Optional[str] = data["posCd"]
        self.position_name: Optional[str] = data["posNm"]
        self.responsibility_code: Optional[str] = data["resCd"]
        self.responsibility_name: Optional[str] = data["resNm"]
        self.work_type_code: Optional[str] = data["wktypeCd"]
        self.work_type_name: Optional[str] = data["wktypeNm"]
        self.start_year_month_day: str = data["staYmd"]
        self.end_year_month_day: str = data["endYmd"]
        self.end_ymd_add: Optional[str] = data["endYmdAdd"]
        self.agent_name: Optional[str] = data["agentName"]
        self.is_full_day: bool = data["allDay"] == "true"
        self.start_hour_minute: Optional[str] = data["staHm"]
        self.end_hour_minute: Optional[str] = data["endHm"]
        self.request_status_code: Optional[str] = data["reqStatusCd"]
        self.reason: Optional[str] = data["reason"]
        self.note: Optional[str] = data["note"]

    @cached_property
    def name(self) -> str:
        """Returns the name section of the event"""

        if self.is_global:
            return self.title.strip()

        return self.title.split("-")[0]

    @cached_property
    def is_global(self) -> bool:
        """Returns true if event is global (i.e. holiday)"""

        # global events has YYYYMMDD while non-global events has YYYY-MM-DD
        return len(self.start_year_month_day) == 8

    @cached_property
    def start_datetime(self) -> datetime:
        """Return event's start time as datetime."""

        ymd_format = "%Y%m%d" if self.is_global else "%Y-%m-%d"
        dt = (
            datetime.strptime(
                f"{self.start_year_month_day} {self.start_hour_minute}",
                ymd_format + " T%H:%M:%S",
            )
            if self.start_hour_minute
            else datetime.strptime(self.start_year_month_day, ymd_format)
        )
        return self.tz.localize(dt)

    @cached_property
    def end_datetime(self) -> datetime:
        """Return event's end time as datetime."""

        ymd_format = "%Y%m%d" if self.is_global else "%Y-%m-%d"
        dt = (
            datetime.strptime(
                f"{self.end_year_month_day} {self.end_hour_minute}",
                ymd_format + " T%H:%M:%S",
            )
            if self.end_hour_minute
            else datetime.strptime(self.end_year_month_day, ymd_format)
        )

        return self.tz.localize(dt)

    def __contains__(self, item: datetime) -> bool:
        """Checks if the CalendarEvent object contains the given datetime.

        Args:
            item: date to check

        Returns:
            True if the CalendarEvent object contains the given datetime, False otherwise
        """

        return self.start_datetime <= item <= self.end_datetime

    def __str__(self):
        """
        Return a string representation of the CalendarEvent object.
        """
        return f"CalendarEvent(title='{self.title}', start='{self.start_year_month_day}', end='{self.end_year_month_day}')"

    def to_dict(self) -> CalendarEventData:
        """
        Convert the CalendarEvent object to a CalendarEventData dictionary.

        Returns:
             A CalendarEventData dictionary containing event data.
        """
        return self._src_data
