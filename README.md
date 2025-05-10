# Google Calendar MCP Server for Booking Appointments

A proof-of-concept implementation of a Model Context Protocol (MCP) server that integrates with Google Calendar to enable appointment booking functionality.

## Features

- Connect to Google Calendar API using OAuth2
- Get calendar busy slots for a specific date
- Book appointments with customizable details
- Retrieve upcoming events from your calendar
- Timezone support

## Requirements

- Python 3.10+
- Google Cloud project with Calendar API enabled
- OAuth2 credentials for Google Calendar API

## Environment Variables

Configure the following environment variables:

- `CALENDAR_ID`: The Google Calendar ID to use (defaults to "primary")
- `EMAIL`: Your Google account email
- `TIMEZONE`: Your timezone (defaults to "America/Chicago")
- `OPEN_FROM`: Business hours start time (defaults to "10:00:00")
- `OPEN_TILL`: Business hours end time (defaults to "18:00:00")
- `TZ`: Timezone offset (defaults to "-05:00")
- `SLOT_MINUTES`: Duration of appointment slots in minutes (defaults to 30)

## Usage

This server exposes several MCP tools:

- `get_calendar_busy_slots`: Find busy time slots for a specific date
- `book_appointment`: Schedule a new appointment with attendees
- `get_upcoming_events`: Retrieve upcoming calendar events

## Note

This is a proof-of-concept implementation. For production use, additional security measures and error handling should be implemented.

## Built With

- [FastMCP](https://github.com/jlowin/fastmcp) - The fast, Pythonic way to build MCP servers and clients
- [Google Calendar API](https://developers.google.com/calendar) - For calendar integration
