from pydantic import BaseModel, Field
from typing import List, TypedDict, Optional, Any, Dict


class FreeBusyCalendar(BaseModel):
    id: str = Field(..., description="Google Calendar ID")


class FreeBusyRequest(BaseModel):
    timeMin: str = Field(...,
                         description="Start time in iso format to check freebusy calendar")
    timeMax: str = Field(...,
                         description="End time in iso format to check freebusy calendar")
    timeZone: str = Field(...,
                          description="Timezone for response. e.g. `America/Chicago`")
    items: List[FreeBusyCalendar] = Field(
        [], description="List of Google calendars to query")


class BusyBlock(BaseModel):
    start: str = Field(..., description="Start of busy block")
    end: str = Field(..., description="End of busy block")


class CalendarBusy(BaseModel):
    busy: List[BusyBlock] = Field(
        [], description="List of busy blocks on the calendar.")


class FreeBusyResponse(BaseModel):
    calendars: Dict[str, CalendarBusy]
