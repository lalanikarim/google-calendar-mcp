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
SLOT_MINIUTES = os.getenv("SLOT_MINUTES", 30)
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


def query_calendar(date: EventDateOnly) -> Response | Error:
    try:
        service = get_service()
        now = datetime.now(pytz.timezone(TIMEZONE)).isoformat()
        start = datetime.fromisoformat(
            f"{date.date}T{OPEN_FROM}{TZ}").isoformat()
        end = datetime.fromisoformat(
            f"{date.date}T{OPEN_TILL}{TZ}").isoformat()
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
        print(f"An error occurred: {error}, {error._get_reason()=}")
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
    """
    try:
        service = get_service()
        dt_start = datetime.fromisoformat(start.dateTime)
        dt_end = dt_start + timedelta(minutes=int(SLOT_MINIUTES))
        end = EventDateTime(dateTime=dt_end.isoformat(), timeZone=TIMEZONE)
        body = Event(
            summary=summary,
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
        print(f"An error occurred: {error}, {error._get_reason()=}")
        return Error(error=error)


def get_next_n_events(max: int = 10) -> Response | Error:
    try:
        service = get_service()
        # Call the Calendar API
        now = datetime.now(tz=timezone.utc).isoformat()
        print("Getting the upcoming 10 events")
        events_result = (
            service.events()
            .list(
                calendarId=CALENDAR_ID,
                timeMin=now,
                maxResults=max,
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
    if False:
        response = book_appointment(summary="New Event Summary",
                                    description="New Event Description", location=None,
                                    start=EventDateTime(
                                        dateTime="2025-04-24T13:00:00", timeZone="America/Chicago"),
                                    attendees=["jimmy00784@gmail.com"]
                                    )
        print(f"{response=}")
    response = get_next_n_events()
    print(f"{response=}")
    response = query_calendar(date=EventDateOnly(date="2025-04-24"))
    print(f"{response=}")
