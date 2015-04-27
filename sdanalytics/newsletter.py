import calendar
from cgi import escape
from datetime import datetime
import os
import re

from lxml import etree
import jinja2
import pandas as pd

CUR_DIR = os.path.dirname(__file__)


def ordinal(n):
    """
    A compact function for generating ordinal suffixes (1st, 2nd, etc.)

    :param n:
    :return:

    >>> ordinal(1)
    '1st'
    >>> ordinal(2)
    '2nd'
    """
    return "%d%s" % (n, "tsnrhtdd"[(n / 10 % 10 != 1) *
                                   (n % 10 < 4) * n % 10::4])


def create_long_date(start, end):
    """
    Convert a start and end date into a formatted string.

    >>> create_long_date(datetime(2014,1,1,10), datetime(2014,1,1,11))
    'Wed, January 1st 10:00am - 11:00am'
    >>> create_long_date(datetime(2014,1,1,10), datetime(2014,1,2,11))
    'Wed, January 1st - 2nd'
    """
    if start.day == end.day:
        return '{}, {} {} {} - {}' \
            .format(calendar.day_abbr[start.weekday()],
                    calendar.month_name[start.month],
                    ordinal(start.day),
                    start.strftime('%l:%M%p').strip().lower(),
                    end.strftime('%l:%M%p').strip().lower())
    else:
        return '{}, {} {} - {}' \
            .format(calendar.day_abbr[start.weekday()],
                    calendar.month_name[start.month],
                    ordinal(start.day),
                    ordinal(end.day))


def events_to_html(events):
    """Render all the events into an html table for the newsletter"""

    # Make sure events is a pandas DataFrame:
    events = pd.DataFrame(events)

    # Create root XML that we will use to build our table:
    root = etree.Element('table')
    troot = etree.SubElement(root, 'tbody')

    for _, row in events.iterrows():

        long_date = create_long_date(row['start'], row['end'])

        # calendar_link = escape(
        #     'https://www.google.com/calendar/embed'
        #     '?src=s0bgkk5un6iq16k3521f76sckk%40'
        #     'group.calendar.google.com&ctz=America/Los_Angeles')

        # Format the large badge text based on single/multi-day:
        if row.multiday:
            icon_large_text = "{}-{}".format(row['start'].day, row['end'].day)
        else:
            icon_large_text = row['start'].day

        # Try to extract link from text. If none found, default to homepage:
        url_regex = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        html_link_match = re.search(url_regex, row['description'])
        if html_link_match:
            event_link = html_link_match.group()
        else:
            event_link = r'http://www.sdanalytics.org/'

        # Render the html for this event:
        html_string = event_template_to_html(
            icon_small_text=calendar.day_abbr[row['start'].weekday()],
            icon_large_text=icon_large_text,
            summary_title=escape(row['summary']),
            summary_link=event_link,
            summary_subtitle=long_date,
            description_text=escape(row['description'])
            .replace('\\n', '<br/>'),
            description_subtext=escape(row['location']),
            calendar_link=r'http://www.sdanalytics.org/#events')

        # Return h:
        if False:
            troot.append(etree.fromstring(html_string))
        else:
            for child in etree.fromstring(html_string).getchildren():
                troot.append(child)

        # Remove comments from html:
        comments = troot.xpath('//comment()')
        for comment in comments:
            comment.getparent().remove(comment)

    # Return pretty html string:
    return etree.tostring(root, pretty_print=True)


def event_template_to_html(**event_args):
    """Render the event template with the provided event arguments"""

    loader = jinja2.FileSystemLoader(searchpath=CUR_DIR)
    template_env = jinja2.Environment(loader=loader)
    template = template_env.get_template("newsletter_event_row.html")

    return template.render(**event_args)

    # # Finally, process the template to produce our final text.
    # output_html = template.render(
    #     **{'icon_small_text': 'Apr',
    #        'icon_large_text': 16,
    #        'summary_title': 'My Awesome Talk',
    #        'summary_link': r'http://www.sdanalytics.org/',
    #        'summary_subtitle': ' Wed, April 9th, 6:00pm - 8:00pm',
    #        'description_text': ' '.join(['Description text'] * 20),
    #        'description_subtext': 'My house',
    #        'calendar_link': r'http://www.sdanalytics.org/#events'})
    #
    # return output_html