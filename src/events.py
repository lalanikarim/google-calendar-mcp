from pydantic import BaseModel, Field
from typing import Optional, List


class EventDateOnly(BaseModel):
    date: str = Field(...,
                      description="Date of the event in format `YYYY-MM-DD`")


class EventDateTime(BaseModel):
    dateTime: str = Field(
        ...,
        description="Date and optional time of the event in format `YYYY-MM-DDTHH:mm:ss`",
    )
    timeZone: Optional[str] = Field(
        None, description="Timzeone of the event date time. Default: 'America/Chicago'"
    )


class EventAttendee(BaseModel):
    email: str = Field(..., description="Email address of the attendee")


class Event(BaseModel):
    id: Optional[str] = Field(None, description="Event Id")
    summary: str = Field(..., description="Summary of the event")
    description: Optional[str] = Field(..., description="Description of the event")
    location: Optional[str] = Field(
        None,
        description="Location of the meeting. Either an address or an online meeting link",
    )
    start: EventDateTime | EventDateOnly = Field(
        description="Start date and time of the event"
    )
    end: EventDateTime | EventDateOnly = Field(
        description="End date and time of the event"
    )
    attendees: List[EventAttendee] = Field([], description="List of attendees")
    htmlLink: Optional[str] = Field(None, description="Event Link")
