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
        kind: The type of event (e.g. "holiday", "meeting", etc.)
        title: The title of the event
        leavNm: The name of the person or organization associated with the event
        leavCd: The code or ID of the person or organization associated with the event
        personInfo: Additional information about the person or organization associated with the event
        orgCd: The code or ID of the organization associated with the event
        orgNm: The name of the organization associated with the event
        posCd: The code or ID of the position or role associated with the event
        posNm: The name of the position or role associated with the event
        resCd: The code or ID of the resource associated with the event
        resNm: The name of the resource associated with the event
        wktypeCd: The type of work or activity associated with the event
        wktypeNm: The name of the work or activity associated with the event
        staYmd: The start date of the event in YYYY-MM-DD format
        endYmd: The end date of the event in YYYY-MM-DD format
        endYmdAdd: Immediate day after endYmd in YYYY-MM-DD format. Not sure what this is for.
        agentName: The name of the agent or person responsible for the event
        allDay: Whether the event is an all-day event
        staHm: The start time of the event
        endHm: The end time of the event
        reqStatusCd: The status of the event request
        reason: The reason for the event
        note: Additional notes or comments about the event
    """

    def __init__(self, data: CalendarEventData):
        self._src_data = data
        self.kind = data["kind"]
        self.title = data["title"]
        self.leavNm = data["leavNm"]
        self.leavCd = data["leavCd"]
        self.personInfo = data["personInfo"]
        self.orgCd = data["orgCd"]
        self.orgNm = data["orgNm"]
        self.posCd = data["posCd"]
        self.posNm = data["posNm"]
        self.resCd = data["resCd"]
        self.resNm = data["resNm"]
        self.wktypeCd = data["wktypeCd"]
        self.wktypeNm = data["wktypeNm"]
        self.staYmd = data["staYmd"]
        self.endYmd = data["endYmd"]
        self.endYmdAdd = data["endYmdAdd"]
        self.agentName = data["agentName"]
        self.allDay = data["allDay"]
        self.staHm = data["staHm"]
        self.endHm = data["endHm"]
        self.reqStatusCd = data["reqStatusCd"]
        self.reason = data["reason"]
        self.note = data["note"]

    @cached_property
    def is_global(self) -> bool:
        """Returns true if event is global (i.e. holiday)"""

        # global events has YYYYMMDD while non-global events has YYYY-MM-DD
        return len(self.staYmd) == 8

    @cached_property
    def start_datetime(self) -> datetime:
        """Return event's start time as datetime."""

        ymd_format = "%Y%m%d" if self.is_global else "%Y-%m-%d"

        if self.staHm:
            return datetime.strptime(
                f"{self.staYmd} {self.staHm}", ymd_format + " T%H:%M:%S"
            )

        return datetime.strptime(self.staYmd, ymd_format)

    @cached_property
    def end_datetime(self) -> datetime:
        """Return event's end time as datetime."""

        ymd_format = "%Y%m%d" if self.is_global else "%Y-%m-%d"

        if self.endHm:
            return datetime.strptime(
                f"{self.endYmd} {self.endHm}", ymd_format + " T%H:%M:%S"
            )

        return datetime.strptime(self.endYmd, ymd_format)

    def __str__(self):
        """
        Return a string representation of the CalendarEvent object.
        """
        return f"CalendarEvent(title='{self.title}', start='{self.staYmd}', end='{self.endYmd}')"

    def to_dict(self) -> CalendarEventData:
        """
        Convert the CalendarEvent object to a CalendarEventData dictionary.

        :return: A CalendarEventData dictionary containing event data.
        """
        return self._src_data
