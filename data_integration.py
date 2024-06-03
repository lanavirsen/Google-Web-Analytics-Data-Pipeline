# For handling dates and times.
import datetime

# For accessing the names of months.
from calendar import month_name

# For handling authentication with Google services.
from google.oauth2 import service_account

# For accessing Google Analytics data.
from google.analytics.data_v1beta import BetaAnalyticsDataClient

# To configure and run reports on Google Analytics.
from google.analytics.data_v1beta.types import (
    RunReportRequest,
    DateRange,
    Dimension,
    Metric,
)

# To create service objects for Google APIs.
from googleapiclient.discovery import build

# For logging messages.
import logging

# Defining the scopes required for the Google API access:
# Sheets, Google Analytics, and Google Search Console.

SCOPES = [
    # Read/write access to user sheets.
    'https://www.googleapis.com/auth/spreadsheets',
    # Read-only access to Google Analytics data.
    'https://www.googleapis.com/auth/analytics.readonly',
    # Read-only access to Google Webmasters data.
    'https://www.googleapis.com/auth/webmasters.readonly',
]

# Path to the service account credentials JSON file
# used for authenticating with Google APIs.

SERVICE_ACCOUNT_FILE = 'E:\\Path\\Placeholder\\ServiceAccountFile.json'

# The ID of the Google Sheet where the data will be written.
SHEET_ID = '1ABc-dEFGhI-Jkl34--mNoPQ'

# Name of the specific worksheet within the Google Sheet where data will be stored.
SHEET_NAME = '2024'

# The Google Analytics 4 property ID from which the data will be fetched.
GA4_PROPERTY_ID = 'properties/123456789'

# Logging configuration.
logging.basicConfig(
    filename='E:\\Path\\Placeholder\\data_integration.log',
    level=logging.DEBUG,
    format='%(asctime)s:%(levelname)s:%(message)s'
)


# Function to fetch data from GA4.
def fetch_ga4_data(credentials, property_id, start_date, end_date):
    # Initializing the Google Analytics Data client with the loaded credentials.
    ga_client = BetaAnalyticsDataClient(credentials=credentials)
    
    # Constructing request for metrics.
    request = RunReportRequest(
        property=property_id,
        metrics=[
            Metric(name='activeUsers'),  # Total number of active users.
            Metric(name='newUsers'),  # Total number of new users.
            Metric(name='eventCount'),  # Total number of events.
            Metric(name='userEngagementDuration'),  # Total engagement time.
        ],
        # Date range for the data request.
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)]
    )

    # Executing the request using the GA client.
    response = ga_client.run_report(request)

    # Extracting metrics from the response, defaulting to fallback values
    # if no data is available.
    users = (
        int(response.rows[0].metric_values[0].value) if response.rows else 0
    )
    new_users = (
        int(response.rows[0].metric_values[1].value) if response.rows else 0
    )
    events = (
        int(response.rows[0].metric_values[2].value) if response.rows else 0
    )
    engagement_time = (
        int(response.rows[0].metric_values[3].value) if response.rows else 0
    )
    
    # Request to fetch the number of engaged sessions by different channels.
    request = RunReportRequest(
        property=property_id,
        dimensions=[Dimension(name='sessionDefaultChannelGroup')],
        metrics=[Metric(name='engagedSessions')],
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)]
    )

    # Executing the request using the GA client.
    response = ga_client.run_report(request)
    
    # Initialize channel data with zeros for specified channels.
    channels = ['Organic Social', 'Direct', 'Organic Search', 'Referral']
    channel_data = {channel: 0 for channel in channels} 
    
    # Processing the response rows to populate the channel data.
    for row in response.rows:
        channel = row.dimension_values[0].value
        if channel in channel_data:
            channel_data[channel] += int(row.metric_values[0].value)
    
    # Creating a list of engaged sessions per channel in the specified order.
    eng_session_per_channel = [channel_data[channel] for channel in channels]

    # Request to fetch the number of active users for custom events.
    request = RunReportRequest(
        property=property_id,
        dimensions=[Dimension(name='eventName')],
        metrics=[Metric(name='activeUsers')],
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        dimension_filter={
            'filter': {
                'field_name': 'eventName',
                'in_list_filter': {
                    'values': ['user_spent_2_minutes', 'bli_medlem_klick']
                }
            }
        }
    )
    
    # Executing the report.
    response = ga_client.run_report(request)

    # Variables to store counts.
    user_spent_2_minutes_user_count = 0
    bli_medlem_klick_user_count = 0

    # Updating variables based on the response.
    for row in response.rows:
        event_name = row.dimension_values[0].value
        user_count = int(row.metric_values[0].value)
    
        if event_name == 'user_spent_2_minutes':
            user_spent_2_minutes_user_count = int(user_count)
        elif event_name == 'bli_medlem_klick':
            bli_medlem_klick_user_count = int(user_count)
    
    # Returning all collected data.
    return (users, new_users, events, engagement_time, eng_session_per_channel,
            user_spent_2_minutes_user_count, bli_medlem_klick_user_count)


# Function to fetch data from Google Search Console.
def fetch_search_console_data(credentials, site_url, start_date, end_date):
    # Initializing the Google Search Console service.
    search_console_service = build(
        'searchconsole', 'v1', credentials=credentials
    )

    # Defining the request parameters for the Search Console API query.
    request = {
        'startDate': start_date,
        'endDate': end_date,
        # No dimensions to collect aggregate data.
        'dimensions': [],
        # Letting the API determine the best aggregation method.
        'aggregationType': 'auto',
        # Limiting the number of rows returned by the API to 1000.
        'rowLimit': 1000
    }
    
    # Executing the API query.
    response = search_console_service.searchanalytics().query(
        siteUrl=site_url,
        body=request
    ).execute()

    if 'rows' in response:
        # Extracting the first (and only) row of data.
        totals = response['rows'][0]
        # Returning the relevant metrics from the response.
        return (
            totals['clicks'],
            totals['impressions'],
            totals['ctr'],
            totals['position']
        )
    else:
        # Returning zeros for all metrics if no data is available.
        return 0, 0, 0, 0


# Function to write data to Google Sheets and format CTR.
def write_and_format_data(credentials, sheet_id, sheet_name, data):
    # Initializing the Google Sheets API.
    sheet_service = build('sheets', 'v4', credentials=credentials)

    # Determining the next empty row to write the data to.
    result = sheet_service.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range=sheet_name
    ).execute()
    next_row = len(result.get('values', [])) + 1

    # Defining the cell range to update in A1 notation.
    range_name = f"{sheet_name}!A{next_row}"

    # Constructing the request body to update the sheet with new data.
    body = {
        'values': [data],
        'majorDimension': 'ROWS'
    }

    # Updating the values in the specified range of the spreadsheet.
    result = sheet_service.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range=range_name,
        valueInputOption='USER_ENTERED',
        body=body
    ).execute()

    # The "sheetId" used in Google Sheets API is a unique identifier
    # assigned to each sheet within a spreadsheet. It is an integer that
    # remains consistent for a sheet even if the order of sheets is changed
    # within the spreadsheet.

    # Retrieve the sheet ID for the given sheet name
    spreadsheet = sheet_service.spreadsheets().get(
        spreadsheetId=sheet_id
    ).execute()
    sheets = spreadsheet.get('sheets', [])
    sheet_id_num = next(
        sheet.get('properties', {}).get('sheetId') 
        for sheet in sheets 
        if sheet.get('properties', {}).get('title') == sheet_name
    )

    # Defining a request to format the CTR (Click Through Rate) as a percentage.
    requests = [{
        'repeatCell': {
            'range': {
                'sheetId': sheet_id_num,  # ID of the sheet.
                'startRowIndex': next_row - 1,  # Starting at the current row.
                'endRowIndex': next_row,  # Ending at the next row.
                'startColumnIndex': 13,  # Starting at column N.
                'endColumnIndex': 14  # Ending at column O.
            },
            'cell': {
                'userEnteredFormat': {
                    'numberFormat': {
                        # Setting number format type to percent.
                        'type': 'PERCENT',
                        # Defining the percent format to one decimal place.
                        'pattern': '#0.0%'
                    }
                }
            },
            'fields': 'userEnteredFormat.numberFormat'
        }
    }]

    # Executing the formatting request to update the cell format.
    body = {'requests': requests}
    sheet_service.spreadsheets().batchUpdate(
        spreadsheetId=sheet_id, body=body
    ).execute()


def main():
    # Loading service account credentials from JSON file with specified scopes.
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=SCOPES
    )   

    # Getting the current date from the system clock.
    today = datetime.date.today()

    # URL for analytics data.
    site_url = 'https://www.ideellmarknadsforing.se/'

    # Computing the first and last day of the previous month.
    first_day_last_month = (today.replace(day=1)
                            - datetime.timedelta(days=1)).replace(day=1)
    last_day_last_month = today.replace(day=1) - datetime.timedelta(days=1)

    # Formatting the month and year (e.g., "May 2024").
    month_and_year = (
        f"{month_name[first_day_last_month.month]} {first_day_last_month.year}"
    )

    # Logging the beginning of the data fetching process for Google Analytics.
    logging.info("Fetching Google Analytics data")

    # Initializing variables with default values to handle cases where
    # data might not be fetched.

    users = new_users = events = engagement_time = 0
    eng_session_per_channel = []
    formatted_avg_engagement_time = 0
    user_spent_2_minutes_user_count = bli_medlem_klick_user_count = 0
    clicks = impressions = ctr = position = 0 

    try:
        # Attempting to fetch Google Analytics data.
        (users, new_users, events, engagement_time,
         eng_session_per_channel, user_spent_2_minutes_user_count,
         bli_medlem_klick_user_count) = fetch_ga4_data(
             # Authentication credentials.
             credentials,
             # Google Analytics property ID.
             GA4_PROPERTY_ID,
             # Start date formatted as string.
             first_day_last_month.strftime('%Y-%m-%d'),
             # End date formatted as string.
             last_day_last_month.strftime('%Y-%m-%d')
        )
        
        # Logging success if data fetching was completed without any exceptions.
        logging.info("Operation was successful")
        logging.info(f"GA4 data fetched: users={users}, "
                     f"new_users={new_users}, "
                     f"events={events}, "
                     f"eng_session_per_channel={eng_session_per_channel}")
        logging.info(f"user_spent_2_minutes={user_spent_2_minutes_user_count}, "
                     f"bli_medlem_klick={bli_medlem_klick_user_count}")

    except Exception as e:
        # Logging any exceptions that occur during the fetching process.
        logging.error("Failed to complete operation", exc_info=True)

    # Logging the beginning of the data fetching process for Google Search Console.
    logging.info("Fetching Search Console data")

    try:
        # Attempting to fetch Search Console data.
        clicks, impressions, ctr, position = fetch_search_console_data(
            # Authentication credentials.
            credentials,
            # URL of the website for which to fetch Search Console data.
            site_url,
            # Start date formatted as string.
            first_day_last_month.strftime('%Y-%m-%d'),
            # End date formatted as string.
            last_day_last_month.strftime('%Y-%m-%d')
        )
        
        # Logging success if data fetching was completed without any exceptions.
        logging.info("Operation was successful")
        logging.info(f"GSC data fetched: clicks={clicks}, "
                     f"impressions={impressions}, "
                     f"ctr={ctr}, "
                     f"position={position}")

    except Exception as e:
        # Logging any exceptions that occur during the fetching process.
        logging.error("Failed to complete operation", exc_info=True)  

    # Preparing data to be written.

    # Logging the beginning of the average engagement time calculation.
    logging.info("Calculating average engagement time in minutes:seconds")

    try:
        # Calculating the average engagement time in seconds.

        # Dividing total engagement time by the number of users to get average.
        avg_engagement_time_seconds = engagement_time / users if users else 0

        # Converting average engagement time from seconds to minutes and seconds.
        minutes = int(avg_engagement_time_seconds // 60)
        seconds = int(avg_engagement_time_seconds % 60)

        # Formatting the average engagement time as "minutes:seconds".
        formatted_avg_engagement_time = f"{minutes}:{seconds:02}"
            
        # Logging success message with the calculated average engagement time.
        logging.info("Operation was successful")
        logging.info(
            "Average engagement time: "
            f"formatted_avg_engagement_time={formatted_avg_engagement_time}"
        )

    except Exception as e:
        # Logging an error if there is an exception during the calculation process.
        logging.error("Failed to complete operation", exc_info=True)

    # Preparing the list of data to be written.
    data_to_write = (
        [
            month_and_year,  # The reporting month and year.
            users,  # Total number of users.
            new_users,  # Total number of new users.
            events,  # Total number of events.
            formatted_avg_engagement_time,  # Formatted average engagement time.
        ]
        + eng_session_per_channel  # Appending engagement sessions per channel data.
        + [
            # Number of users who spent at least 2 minutes on the site.
            user_spent_2_minutes_user_count,
            # Number of users who clicked the button "Bli medlem".
            bli_medlem_klick_user_count,
            # Total number of clicks from Search Console.
            clicks,
            # Total number of impressions from Search Console.
            impressions,
            # Click-through rate from Search Console.
            ctr,
            # Rounded average position from Search Console.
            round(position, 1),
        ]
    )

    # Logging the initiation of the data writing process to Google Sheets.
    logging.info("Writing to Google Sheets")

    try:
        # Attempting to write and format the data in Google Sheets.
        write_and_format_data(credentials, SHEET_ID, SHEET_NAME, data_to_write)

        # Logging a success message if data writing and formatting
        # complete successfully.
        logging.info("Operation was successful")

    except Exception as e:
        # Logging an error message if an exception occurs during
        # the write operation, including traceback information.
        logging.error("Failed to complete operation", exc_info=True)

# If the script is executed as the main program, calling the main function.
if __name__ == '__main__':
    main()
