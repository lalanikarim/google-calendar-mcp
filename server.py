import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from mcp.server.fastmcp import FastMCP
from datetime import datetime, timedelta, timezone
from src import (Event, EventDateTime, EventDateOnly, EventAttendee,
                 FreeBusyRequest, FreeBusyCalendar, FreeBusyResponse)
from typing import Optional, List, TypedDict, Any
import pytz

from dotenv import load_dotenv
import os

load_dotenv()
CALENDAR_ID = os.getenv("CALENDAR_ID", "primary")
EMAIL = os.getenv("EMAIL")
TIMEZONE = os.getenv("TIMEZONE", "America/Chicago")
OPEN_FROM = os.getenv("OPEN_FROM", "10:00:00")
OPEN_TILL = os.getenv("OPEN_TILL", "18:00:00")
TZ = os.getenv("TZ", "-05:00")
SLOT_MINUTES = os.getenv("SLOT_MINUTES", 30)
# If modifying these scopes, delete the file token.json.
SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/calendar.freebusy",
]


mcp = FastMCP("Calendar")


def authenticate():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    if creds:
        return creds
    raise Exception("Unable to authenticate")


def get_service():
    creds = authenticate()
    service = build("calendar", "v3", credentials=creds)
    return service


class Response(TypedDict):
    response: Any


class Error(TypedDict):
    error: Any


@mcp.tool()
def get_calendar_busy_slots(when: EventDateOnly | str) -> Response | Error:
    """
    Check the calendar for busy slots for a given date

    args:
        when: Date to check for busy slots in ISO format
    """
    try:
        service = get_service()
        now = datetime.now(pytz.timezone(TIMEZONE)).isoformat()
        if isinstance(when, str):
            when = EventDateOnly(date=when)
        start = datetime.fromisoformat(
            f"{when.date}T{OPEN_FROM}{TZ}").isoformat()
        end = datetime.fromisoformat(
            f"{when.date}T{OPEN_TILL}{TZ}").isoformat()
        print(f"{now=},{start=},{end=}")
        query = FreeBusyRequest(
            timeMin=start if start >= now else now,
            timeMax=end,
            timeZone=TIMEZONE,
            items=[
                FreeBusyCalendar(id=CALENDAR_ID)
            ]
        )
        print(f"{query=}")
        result = service.freebusy().query(body=query.model_dump()).execute()
        result = FreeBusyResponse(**result)
        return Response(response=result)
    except HttpError as error:
        print(f"An error occurred: {error}, {error.reason=}")
        return Error(error=error)


@mcp.tool()
def book_appointment(
    summary: str,
    description: Optional[str],
    location: Optional[str],
    start: EventDateTime,
    attendees: List[str],
) -> Response | Error:
    """
    Book an appointment on the calendar

    args:
        summary: Summary of the appointment
        description: Optional - Description of the appointment
        location: Optional - Location of the appointment
        start: Start of the appointment in ISO format
        attendees: List of attendee email addresses
    """
    try:
        service = get_service()
        dt_start = datetime.fromisoformat(start.dateTime)
        if dt_start.time() < datetime.strptime(OPEN_FROM,"%H:%M:%S").time():
            return Error(error=f"Cannot book an appointment before {OPEN_FROM}")
        dt_end = dt_start + timedelta(minutes=int(SLOT_MINUTES))
        if dt_end.time() > datetime.strptime(OPEN_TILL,"%H:%M:%S").time():
            return Error(error=f"Cannot book an appointment after {OPEN_TILL}")
        end = EventDateTime(dateTime=dt_end.isoformat(), timeZone=TIMEZONE)
        body = Event(
            summary=summary,
            description=description,
            location=location,
            start=start,
            end=end,
            attendees=[EventAttendee(email=attendee)
                       for attendee in set(attendees + [EMAIL])])
        if not body.start.timeZone:
            body.start.timeZone = TIMEZONE
        if not body.end.timeZone:
            body.end.timeZone = TIMEZONE
        print(f"{body.model_dump(exclude_none=True)=}")
        event = service.events().insert(calendarId=CALENDAR_ID,
                                        body=body.model_dump(exclude_none=True)).execute()
        event = Event(**event)
        return Response(response=event.htmlLink)
    except HttpError as error:
        print(f"An error occurred: {error}, {error.reason=}")
        return Error(error=error)


@mcp.tool()
def get_upcoming_events(starting_from: Optional[EventDateTime] = None, max_events: int = 10) -> Response | Error:
    """
    Get upcoming events from the calendar

    args:
        starting_from: Optional - Date and time to check for busy slots in ISO format - defaults to current time
        max_events: Optional - Maximum number of events to return - defaults to 10
    """
    try:
        service = get_service()
        # Call the Calendar API
        now = datetime.now(tz=timezone.utc).isoformat()
        if starting_from:
            starting_from.dateTime = datetime.fromisoformat(starting_from.dateTime).isoformat()
            if len(starting_from.dateTime) == 19:
                starting_from.dateTime = starting_from.dateTime + TZ
            print(f"{starting_from.dateTime=},{len(starting_from.dateTime)=}")
        print("Getting the upcoming 10 events")
        events_result = (
            service.events()
            .list(
                calendarId=CALENDAR_ID,
                timeMin=starting_from.dateTime if starting_from else now,
                maxResults=max_events,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])

        return Response(response=[Event(**event) for event in events])

    except HttpError as error:
        print(f"An error occurred: {error}")
        return Error(error=error)


if __name__ == "__main__":
    import uvicorn
    if get_service():
        uvicorn.run(mcp.sse_app())