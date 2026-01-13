# Strava Data Puller Setup Guide

This guide will help you set up the Strava Data Puller to connect to your Strava account and retrieve your running activity data.

## Prerequisites

1. A Strava account with activities
2. Python 3.7 or higher installed on your system

## Step 1: Create a Strava Application

1. Go to [Strava API Settings](https://www.strava.com/settings/api)
2. Click "Create App" or "My API Application"
3. Fill in the required information:
   - **Application Name**: Choose any name (e.g., "My Running Data Analyzer")
   - **Category**: Select "Data Analysis"
   - **Club**: Leave blank
   - **Website**: You can use `http://localhost` or your personal website
   - **Authorization Callback Domain**: Use `localhost` for local development
4. Click "Create"
5. Note down your **Client ID** and **Client Secret**

## Step 2: Get Your Access Token

### Method 1: Using the Authorization URL (Recommended)

1. Construct the authorization URL using your Client ID:
   ```
   https://www.strava.com/oauth/authorize?client_id=YOUR_CLIENT_ID&response_type=code&redirect_uri=http://localhost&scope=read,activity:read_all&state=test
   ```
   Replace `YOUR_CLIENT_ID` with your actual Client ID.

2. Open this URL in your browser and log in to Strava
3. You'll be redirected to a localhost URL with a `code` parameter
4. Copy the `code` value from the URL

5. Use the following Python script to exchange the code for tokens:

```python
import requests

client_id = "YOUR_CLIENT_ID"
client_secret = "YOUR_CLIENT_SECRET"
code = "THE_CODE_FROM_URL"

url = "https://www.strava.com/oauth/token"
data = {
    'client_id': client_id,
    'client_secret': client_secret,
    'code': code,
    'grant_type': 'authorization_code'
}

response = requests.post(url, data=data)
token_data = response.json()

print("Access Token:", token_data['access_token'])
print("Refresh Token:", token_data['refresh_token'])
```

### Method 2: Using Postman or curl

You can also use Postman or curl to make the token exchange request:

```bash
curl -X POST https://www.strava.com/oauth/token \
  -d client_id=YOUR_CLIENT_ID \
  -d client_secret=YOUR_CLIENT_SECRET \
  -d code=THE_CODE_FROM_URL \
  -d grant_type=authorization_code
```

## Step 3: Install Dependencies

1. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

## Step 4: Configure Your Credentials

### Option 1: Environment Variables (Recommended)

Create a `.env` file in the same directory as the script:

```env
STRAVA_CLIENT_ID=your_client_id_here
STRAVA_CLIENT_SECRET=your_client_secret_here
STRAVA_ACCESS_TOKEN=your_access_token_here
STRAVA_REFRESH_TOKEN=your_refresh_token_here
```

### Option 2: Direct Input

The script will prompt you for credentials if environment variables are not found.

## Step 5: Run the Script

```bash
python strava_data_puller.py
```

## What the Script Does

1. **Connects to Strava API**: Authenticates using your credentials
2. **Retrieves Activities**: Fetches all activities from the last 365 days
3. **Filters Running Data**: Identifies and filters running activities (Run, TrailRun, Treadmill)
4. **Processes Data**: Converts the data into a structured format
5. **Generates Summary**: Provides statistics about your running activities
6. **Exports Data**: Saves the data to a CSV file for further analysis

## Output

The script will:
- Display a summary of your running activities
- Save detailed data to a CSV file named `strava_running_data_YYYYMMDD_HHMMSS.csv`
- Show the first 5 activities in the console

## Data Fields Included

- Activity ID, name, and type
- Date and time
- Distance (in kilometers)
- Moving time and elapsed time
- Elevation gain
- Average and maximum speed
- Heart rate data (if available)
- Calories burned
- Social metrics (kudos, comments)
- Activity flags (trainer, commute, manual, etc.)

## Troubleshooting

### Common Issues

1. **"Token expired" error**: The script automatically refreshes tokens, but if it fails, you may need to re-authorize
2. **"No activities found"**: Check your date range or ensure you have activities in your Strava account
3. **Rate limiting**: The script includes delays to respect Strava's rate limits

### Rate Limits

Strava has rate limits:
- 100 requests per 15 minutes
- 1,000 requests per day

The script includes automatic delays to stay within these limits.

## Next Steps

Once you have your data, you can:
- Analyze trends in your running performance
- Create visualizations using matplotlib or seaborn
- Track progress over time
- Identify patterns in your training

## Security Notes

- Never commit your `.env` file to version control
- Keep your Client Secret private
- Access tokens expire after 6 hours, but refresh tokens are long-lived
- The script automatically handles token refresh

## Support

If you encounter issues:
1. Check the Strava API documentation: https://developers.strava.com/
2. Verify your app settings in Strava
3. Ensure your tokens are valid and have the correct permissions
