import datetime
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from pydantic import BaseModel, Field
from typing import List, Dict, TypedDict, Any, Optional
from mcp.server.fastmcp import FastMCP

from dotenv import load_dotenv
import os

load_dotenv()

# If modifying these scopes, delete the file token.json.
SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/calendar.freebusy",
]


class EventTime(BaseModel):
    dateTime: str = Field(
        ..., description="Date and optional time of the event in format `YYYY-DD-MMTHH:mm:ss-TZ`")
    timeZone: str = Field(
        ..., description="Timzeone of the event date time. Default: 'America/Chicago'")


class EventAttendee(BaseModel):
    email: str = Field(..., description="Email address of the attendee")


class Event(BaseModel):
    summary: str = Field(..., description="Summary of the event")
    location: Optional[str] = Field(
        None, description="Location of the meeting. Either an address or an online meeting link")
    start: EventTime = Field(...,
                             description="Start date and time of the event")
    end: EventTime = Field(..., description="End date and time of the event")
    attendees: List[EventAttendee] = Field([],
                                           description="List of attendees")


mcp = FastMCP("Calendar")


def main():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("calendar", "v3", credentials=creds)

        # Call the Calendar API
        now = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
        print("Getting the upcoming 10 events")
        events_result = (
            service.events()
            .list(
                calendarId=os.getenv("CALENDAR_ID", "primary"),
                timeMin=now,
                maxResults=10,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])

        if not events:
            print("No upcoming events found.")
            return

        # Prints the start and name of the next 10 events
        for event in events:
            # event["start"].get("dateTime", event["start"].get("date"))
            event = Event(**event)
            print(event.start, event.summary)

    except HttpError as error:
        print(f"An error occurred: {error}")


if __name__ == "__main__":
    main()
