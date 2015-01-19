from datetime import datetime, timedelta

from apiclient.discovery import build
import pandas as pd


def pull_events(api_key):
    # api_key = os.environ['GOOGLE_API_KEY']
    service = build('calendar', 'v3', developerKey=api_key)

    # API Reference:
    # https://developers.google.com/google-apps/calendar/v3/reference/events/list
    request = service.events().list(
        calendarId='s0bgkk5un6iq16k3521f76sckk@group.calendar.google.com',
        singleEvents=True,
        timeMin=u'{:s}T00:00:00-07:00'.format(str(datetime.today().date())),
        orderBy='startTime')

    events = []
    while request is not None:
        # Get the next page:
        response = request.execute()

        # Accessing the response like a dict object with an 'items' key
        # returns a list of item objects (events).
        for event in response.get('items', []):
            # The event object is a dict object with a 'summary' key.
            events.append(
                {'summary': repr(event.get('summary', 'NO SUMMARY'))[2:-1],
                 'description': repr(
                     event.get('description', 'NO DESCRIPTION'))[2:-1],
                 'start': event.get('start', 'NO DATE').values()[0],
                 'end': event.get('end', 'NO DATE').values()[0],
                 'location': repr(event.get('location', 'NO LOCATION'))[2:-1]})

        # Get the next request object by passing the previous request object to
        # the list_next method.
        request = service.events().list_next(request, response)

    return _events_to_df(events)


def _events_to_df(events):
    """Convert an iterable of events to a DataFrame"""

    df = pd.DataFrame(events)
    df['start'] = _localize_datetime(df['start'])
    df['end'] = _localize_datetime(df['end'])

    df['multiday'] = df['start'].apply(lambda x: x.date()) != \
                     df['end'].apply(lambda x: x.date())

    df.ix[df['multiday'], 'start'] = df.ix[df['multiday'], 'start'].apply(
        lambda x: x + pd.Timedelta(days=1))

    return df


def _localize_datetime(s):
    return pd.to_datetime(s).apply(
        lambda x: x.tz_localize('UTC').tz_convert('US/Pacific'))
