# :arrows_counterclockwise: Google API Data Pipeline Project

## Introduction

### Objective
The aim of this project was to automate the monthly collection, transformation, and presentation of web analytics data from Google Analytics 4 and Google Search Console into a Google Sheet for the non-profit organization Ideell marknadsföring i Sverige, where I volunteer as a Data Analyst and Data Team Coordinator. This automation streamlines the process of monitoring and reporting key performance metrics, facilitating easier analysis and access to data for our data team.

### Tools and technologies used
- **Python**: For scripting the data collection and transformation processes.
- **Google Analytics Data API and Google Search Console API**: For accessing and retrieving web analytics data.
- **Google Sheets API**: For loading and visualizing data in a user-friendly format.
- **OAuth2.0**: For secure API authentication.
- **Jupyter Notebook and Visual Code Studio**: For developing, testing, and documenting the code.

### Project outcomes
- Enabled automated, timely, and error-free reporting of key web metrics, significantly reducing manual effort and enhancing the decision-making process.
- Developed reusable code modules for fetching and processing API data, which can be adapted for other similar projects or expanded to include additional data sources.

### Skills demonstrated
- Utilizing cloud-based APIs for data integration
- Data cleaning, transformation, and preparation
- Automating and scheduling Python scripts

## Steps done
### Table of contents
1. [Google Analytics 4 - Google Sheets pipeline](#google-analytics-4---google-sheets-pipeline)
    1. [Setting up a Google Cloud Project](#setting-up-a-google-cloud-project)
    2. [Enabling the required APIs for GA4 and Google Sheets](#enabling-the-required-apis-for-ga4-and-google-sheets)
    3. [Creating credentials](#creating-credentials)

### 1. Google Analytics 4 - Google Sheets pipeline

#### 1.1. Setting up a Google Cloud Project

I accessed the Google Cloud Console and initiated the creation of a new project.

(Image 1)

#### 1.2. Enabling the required APIs for GA4 and Google Sheets

I navigated to the "APIs & Services > Library" section in the Google Cloud Console, searched for the Google Analytics Data API and Google Sheets API, and enabled them.

(Image 2)

(Image 3)

#### 1.3. Creating credentials

First, I navigated to "IAM & Admin > Service Accounts" to create a service account in the Google Cloud project.

(Image 4)

Next, I generated and downloaded a JSON key file for my service account. This key is used to authenticate my script with Google APIs.

(Image 5)

Initially, the attempt to create the keys raised an error due to insufficient permissions.

Upon further investigation, I discovered that a policy was enforced to disable Service Account Key Creation (as service account keys can pose a security risk if not managed carefully). After editing the policy, I successfully created and downloaded the keys.

#### 1.4. Setting permissions

I added the service account email as a user in Google Analytics, granting it the necessary permissions to read the data.

I also shared the Google Sheet, which will be used to write the data, with the email address associated with the service account, ensuring it had the required permissions to read and write.

#### 1.5. Installing client libraries

To write a Python script to automate data fetching from GA4 and writing to Google Sheets, I first needed to install the required libraries.

```
pip install google-auth google-analytics-data gspread
```

(Image 6)

#### 1.6. Writing code to access GA4 data and write it to Google Sheet

**Loading the required libraries**

```python
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

# To interact with Google Sheets.
import gspread
```

**Defining the constants**

```python
# Defining the scopes required for the Google API access:
# Google Sheets and Google Analytics.

SCOPES = [
    # Read/write access to user sheets and their properties.
    'https://www.googleapis.com/auth/spreadsheets',
    # Read-only access to Google Analytics data.
    'https://www.googleapis.com/auth/analytics.readonly',
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
```

**Authenticating and constructing service clients**

```python
# Loading service account credentials from JSON file with specified scopes.
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=SCOPES
)  

# Initializing the Google Analytics Data client with the loaded credentials.
ga_client = BetaAnalyticsDataClient(credentials=credentials)

# Authorizing and creating a client to interact with Google Sheets
# using the same credentials.

sheet_client = gspread.authorize(credentials)
```

**Calculating data range for previous month**

```python
# Getting the current date from the system clock.
today = datetime.date.today()

# Computing the first and last day of the previous month.
first_day_last_month = (today.replace(day=1)
						- datetime.timedelta(days=1)).replace(day=1)
last_day_last_month = today.replace(day=1) - datetime.timedelta(days=1)

# Formatting the month and year (e.g., "May 2024").
month_and_year = (
	f"{month_name[first_day_last_month.month]} {first_day_last_month.year}"
)
```

#### Defining the functions to fetch and write data

I started with just a few GA4 metrics to test the pipeline:

- Total number of active users.
- Total number of new users.
- Total number of events.

```python
# Function to fetch data from GA4.
def fetch_ga4_data(property_id, start_date, end_date):
    # Constructing request for metrics.
    request = RunReportRequest(
        property=property_id,
        metrics=[
            Metric(name='activeUsers'),  # Total number of active users.
            Metric(name='newUsers'),  # Total number of new users.
            Metric(name='eventCount'),  # Total number of events.
        ],
        # Date range for the data request.
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)]
    )
    
    # Executing the request using the GA client.
    response = ga_client.run_report(request)
    
    # Extracting metrics from the response, defaulting to fallback values
    # if no data is available.
    users = (
        int(response.rows[0].metric_values[0].value) if response.rows else 0
    )
    new_users = (
        int(response.rows[0].metric_values[1].value) if response.rows else 0
    )
    events = (
        int(response.rows[0].metric_values[2].value) if response.rows else 0
    )
    
    # Returning all collected data.
    return users, new_users, events, engagement_time


# Function to write data to Google Sheets.
def write_to_sheet(sheet_id, sheet_name, data):
    # Preparing data.
    values = [data]  # Data should be a list of values.
    
    # Accessing the specific sheet and worksheet.
    sheet = sheet_client.open_by_key(sheet_id)
    worksheet = sheet.worksheet(sheet_name)
    
    # Finding the next empty row to determine where to start writing data.
    next_row = len(worksheet.get_all_values()) + 1
    
    # Writing data to the determined range in the sheet.
    
    # Specifying the start row and column A.
    range_name = f"!A{next_row}"
    # Updating the worksheet with the provided values.
    worksheet.update(range_name, values)
```

**Fetching data from GA4**

```python
users, new_users, events = fetch_ga4_data(
    # Google Analytics property ID.
    GA4_PROPERTY_ID,
    # Start date formatted as string.
    first_day_last_month.strftime('%Y-%m-%d'),
    # End date formatted as string.
    last_day_last_month.strftime('%Y-%m-%d')
)
```

**Preparing data**

```python
data_to_write = [
    month_and_year,  # The reporting month and year.
    users,  # Total number of users.
    new_users,  # Total number of new users.
    events,  # Total number of events.
]
```

**Writing data to Google Sheets**

```python
write_to_sheet(SHEET_ID, SHEET_NAME, data_to_write)
```

**Adding more metrics**

After ensuring the code worked, I added more metrics, including:

- Average engagement time per user.
- Total number of engaged sessions per channel ("Organic Social", "Direct", "Organic Search", "Referral").
- Custom event: total number of users who spent 2+ minutes on our website.
- Custom event: total number of users who clicked the button "Bli medlem" ("Become a member" in English).

Since there was no direct metric for average engagement time per user, I fetched the total engagement time (saved as `engagement_time`) and transformed and formatted it as follows:

```python
# Dividing total engagement time by the number of users to get average.
avg_engagement_time_seconds = engagement_time / users if users else 0

# Converting average engagement time from seconds to minutes and seconds.
minutes = int(avg_engagement_time_seconds // 60)
seconds = int(avg_engagement_time_seconds % 60)

# Formatting the average engagement time as "minutes:seconds".
formatted_avg_engagement_time = f"{minutes}:{seconds:02}"
```

### 2. Adding Google Search Console to the existing pipeline

#### 2.1. Enabling Google Search Console API

In the Google Cloud Console, I selected my project and enabled the Google Search Console API in the  "APIs & Services > Library" section.

(Image 7)

#### 2.2. Setting permissions

I added the service account email to my Google Search Console property with the appropriate permission level (read access).

#### 2.3. Installing the client library

I installed the necessary library:

```
pip install google-api-python-client
```

(Image 8)

#### 2.4. Adjusting code to add Google Search Console data to the pipeline

**Loading additional libraries**

One more library was added:

```python
# To create service objects for Google APIs.
from googleapiclient.discovery import build
```

**Setting up access to Google Search Console**

```python
# Initializing the Google Search Console service.
search_console_service = build('webmasters', 'v1', credentials=credentials)

# URL for analytics data.
site_url = 'https://www.ideellmarknadsforing.se/' 
```

**Defining the function to fetch data from Google Search Console**

I was interested in the following metrics from Google Search Console:

- Total number of clicks.
- Total number of impressions.
- Average CTR (Click Through Rate).
- Average position of our website.

```python
def fetch_search_console_data(site_url, start_date, end_date):
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
```

**Fetching Search Console data**

```python
clicks, impressions, ctr, position = fetch_search_console_data(
    # URL of the website for which to fetch Search Console data.
    site_url,
    # Start date formatted as string.
    first_day_last_month.strftime('%Y-%m-%d'),
    # End date formatted as string.
    last_day_last_month.strftime('%Y-%m-%d')
)
```

Then I added Search Console data to the list of data to be written.

**Formatting**

To display CTR as a rounded percentage in the Google Sheet, I needed to adjust the function for writing data to include formatting. As the `gspread` library has more limited functionality, I switched to using `google-api-python-client` for Google Sheets instead.

Initializing the Google Sheets API:

```python
sheet_service = build('sheets', 'v4', credentials=credentials)
```

The updated function to write to the sheet:

```python
def write_and_format_data(sheet_id, sheet_name, data):
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

    # Defining a request to format the CTR (Click Through Rate) as a percentage.
    requests = [{
        'repeatCell': {
            'range': {
                'sheetId': 0,  # ID of the sheet within the spreadsheet.
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
    response = service.spreadsheets().batchUpdate(
        spreadsheetId=sheet_id, body=body
    ).execute()
```

### 3. Saving the code as a .py script

So far, I had been working with my code in Jupyter Notebook. 

While modifying the code in Visual Studio Code to create a .py script, I rearranged it for a better structure and encapsulated the execution logic within a `main` function for modularity.

The script ends with a check to call `main` if the script is executed directly:

```python
if __name__ == '__main__':
    main()
```

### 4. Logging

For a script that's being run automatically, adding logging is a practical way to track its execution and troubleshoot any issues that might arise. For that, I used Python's built-in `logging` library.

**Importing the logging library**

```python
import logging
```

**Setting up the logging configuration**

I set up the logging configuration at the global level, outside the `main` function:

```python
logging.basicConfig(
    filename='E:\\Path\\Placeholder\\data_integration.log',
    level=logging.DEBUG,
    format='%(asctime)s:%(levelname)s:%(message)s'
)
```

**Using logging in the `main` function**

Inside the `main` function, I used logging calls to log specific events, errors, or information relevant to the execution flow of the script.

**Fetching data from Google Analytics**

```python
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
```

**Fetching data from Google Search Console**

```python
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
```

**Preparing data to be written**

```python
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
    logging.info("Average engagement time: "
                 f"formatted_avg_engagement_time={formatted_avg_engagement_time}")

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
        # Number of users who clicked the button 'Bli medlem'.
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
```

**Writing data to Google Sheets**

```python
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
```

### 5. Scheduling

I use a Windows system, so I utilized the built-in Task Scheduler to automate the execution of my Python script on the 3rd day of each month.

#### 5.1. Creating a new task in Task Scheduler

I opened Task Scheduler and initiated the creation of a new task.

(Image 9)

#### 5.2. Configuring the task
**General tab**

I named the task "Monthly IMIS Data Fetching" and adjusted the security options as needed.

(Image 10)

**Triggers tab**

I clicked on "New…" to set a new trigger.

For "Begin the task", I selected "On a schedule", and for "Settings", I chose "Monthly". For "Months", I selected all months, and for "Days", I selected "3" to set the task to run on the 3rd day of each month.

(Image 11)

(Image 12)

**Actions tab**

I clicked on "New…" to define the action the task should perform. 

For "Action", I chose "Start a program" and provided the paths for the three required fields: the path to the Python executable, the path to my script, and the path to the folder containing the script.

(Image 13)

**Conditions tab**

I then adjusted the settings in the Conditions tab as required.

(Image 14)

**Settings tab**

Finally, I adjusted the setting in the Setting tab.

(Image 15)

**Saving and testing**

Initially, I encountered an issue with the task failing to run the script.

After researching the error code online, I discovered that the problem was due to the use of quotation marks in the "Start in (optional)" field in the Action tab. While the "Program/script" and "Add arguments (optional)" fields accept quotation marks, the "Start in (optional)" field does not.

After correcting this issue, the task executed as intended.
