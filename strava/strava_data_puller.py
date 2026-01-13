"""
Strava Data Puller
A Python script to connect to Strava API and retrieve activity data.
"""

import requests
import json
import time
from datetime import datetime, timedelta
import pandas as pd
from typing import List, Dict, Optional
import os
import re
from dataclasses import dataclass
from .strava_data_processing import StravaDataProcessor


@dataclass
class StravaConfig:
    """Configuration class for Strava API credentials."""
    client_id: str
    client_secret: str
    access_token: str
    refresh_token: str


class StravaAPI:
    """Class to handle all Strava API interactions and data retrieval."""
    
    def __init__(self, config: StravaConfig):
        self.config = config
        self.base_url = "https://www.strava.com/api/v3"
        self.headers = {
            'Authorization': f'Bearer {config.access_token}',
            'Content-Type': 'application/json'
        }
    
    def refresh_access_token(self) -> bool:
        """Refresh the access token using the refresh token."""
        url = "https://www.strava.com/oauth/token"
        data = {
            'client_id': self.config.client_id,
            'client_secret': self.config.client_secret,
            'refresh_token': self.config.refresh_token,
            'grant_type': 'refresh_token'
        }
        
        try:
            response = requests.post(url, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            self.config.access_token = token_data['access_token']
            self.config.refresh_token = token_data['refresh_token']
            self.headers['Authorization'] = f'Bearer {self.config.access_token}'
            
            print("Access token refreshed successfully!")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"Error refreshing token: {e}")
            return False
    
    def make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Make a request to the Strava API with automatic token refresh."""
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            
            # If token is expired, try to refresh it
            if response.status_code == 401:
                print("Token expired, attempting to refresh...")
                if self.refresh_access_token():
                    response = requests.get(url, headers=self.headers, params=params)
                else:
                    return None
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Error making request to {endpoint}: {e}")
            return None
    
    # Athlete-related methods
    def get_athlete_info(self) -> Optional[Dict]:
        """Get current athlete information."""
        return self.make_request("athlete")
    
    # Activity-related methods
    def get_activities(self, per_page: int = 200, page: int = 1, 
                      before: Optional[int] = None, after: Optional[int] = None) -> Optional[List[Dict]]:
        """
        Get athlete activities.
        
        Args:
            per_page: Number of activities per page (max 200)
            page: Page number
            before: Unix timestamp for activities before this date
            after: Unix timestamp for activities after this date
        """
        params = {
            'per_page': per_page,
            'page': page
        }
        
        if before:
            params['before'] = before
        if after:
            params['after'] = after
            
        return self.make_request("athlete/activities", params)
    
    def get_activity_details(self, activity_id: int) -> Optional[Dict]:
        """Get detailed information about a specific activity."""
        return self.make_request(f"activities/{activity_id}")
    
    def get_activity_streams(self, activity_id: int, 
                           types: List[str] = None) -> Optional[Dict]:
        """
        Get activity streams (time series data).
        
        Args:
            activity_id: The activity ID
            types: List of stream types (e.g., ['time', 'distance', 'latlng', 'altitude', 'heartrate', 'velocity_smooth', 'cadence', 'moving'])
        """
        if types is None:
            types = ['time', 'distance', 'latlng', 'altitude', 'heartrate', 'velocity_smooth', 'cadence', 'moving']
        
        # Strava API expects 'keys' parameter with comma-separated stream types
        params = {'keys': ','.join(types)}
        return self.make_request(f"activities/{activity_id}/streams", params)
    
    def get_all_activities(self, days_back: int = 365) -> List[Dict]:
        """
        Get all activities from the last N days.
        
        Args:
            days_back: Number of days to look back
        """
        all_activities = []
        page = 1
        per_page = 200
        
        # Calculate timestamp for days_back
        after_timestamp = int((datetime.now() - timedelta(days=days_back)).timestamp())
        
        while True:
            print(f"Fetching page {page}...")
            activities = self.get_activities(
                per_page=per_page, 
                page=page, 
                after=after_timestamp
            )
            
            if not activities:
                break
                
            all_activities.extend(activities)
            
            # If we got fewer activities than per_page, we've reached the end
            if len(activities) < per_page:
                break
                
            page += 1
            time.sleep(0.2)  # Rate limiting
        
        print(f"Retrieved {len(all_activities)} activities")
        return all_activities
    
    def get_activities_by_person(self, person_initial: str, days_back: int = 365) -> List[Dict]:
        """
        Get activities for a specific person based on their initial.
        Expects activity names in format: "ActivityType x (DeviceName y)" or "ActivityType x [DeviceName y]"
        where:
          - ActivityType is one of: Running, Rest, Treppe
          - x is a number
          - DeviceName is one of: Polar, Apple, GarminT, GarminU, FitbitU, FitbitT, Xiaomi, Huawei, Wahoo
          - y is the person's initial (1-2 characters)
        
        Examples:
          - "Running 123 (Polar A)" -> person initial 'A'
          - "Rest 45 [GarminT JD]" -> person initial 'JD'
          - "Treppe 7 (Apple B)" -> person initial 'B'
        
        Args:
            person_initial: The person's initial to filter by (e.g., 'A', 'JD', 'B')
            days_back: Number of days to look back
        
        Returns:
            List of activities matching the person's initial
        """
        
        # Get all activities
        all_activities = self.get_all_activities(days_back=days_back)
        
        # Filter activities by person initial
        person_activities = []
        # Pattern matches: (Running|Rest|Treppe) <number> (DeviceName <initial>) or [DeviceName <initial>]
        # Captures the person's initial (y)
        pattern = re.compile(
            r'(?:Running|Rest|Treppe)\s+\d+\s+[\(\[](?:Polar|Suunto|Apple|GarminT|GarminU|FitbitU|FitbitT|Xiaomi|Huawei|Wahoo)\s+([A-Za-z]{1,2})[\)\]]',
            re.IGNORECASE
        )
        
        for activity in all_activities:
            activity_name = activity.get('name', '')
            match = pattern.search(activity_name)
            
            if match:
                initial = match.group(1).strip().upper()
                # Case-insensitive comparison
                if initial == person_initial.strip().upper():
                    person_activities.append(activity)
        
        print(f"Found {len(person_activities)} activities for person with initial '{person_initial}'")
        return person_activities
    
    def get_person_activity_streams(self, person_initial: str, days_back: int = 365,
                                   stream_types: Optional[List[str]] = None) -> Dict[int, Dict]:
        """
        Get activity streams for all activities belonging to a specific person.
        
        This function combines get_activities_by_person() and get_activity_streams():
        1. Finds all activities for the specified person using their initial
        2. Iterates through each activity and retrieves its stream data
        
        Args:
            person_initial: The person's initial to filter by (e.g., 'A', 'JD', 'B')
            days_back: Number of days to look back
            stream_types: List of stream types to retrieve (default: ['time', 'distance', 'latlng', 'altitude', 'heartrate'])
        
        Returns:
            Dictionary mapping activity_id to stream data
            Format: {activity_id: stream_data, ...}
        """
        # Get all activities for this person
        print(f"\nRetrieving activities for person '{person_initial}'...")
        person_activities = self.get_activities_by_person(person_initial, days_back=days_back)
        
        if not person_activities:
            print(f"No activities found for person '{person_initial}'")
            return {}
        
        # Retrieve streams for each activity
        activity_streams = {}
        total_activities = len(person_activities)
        
        print(f"\nRetrieving streams for {total_activities} activities...")
        
        for idx, activity in enumerate(person_activities, 1):
            activity_id = activity.get('id')
            activity_name = activity.get('name', 'Unknown')
            
            if not activity_id:
                print(f"[{idx}/{total_activities}] Skipping activity with no ID")
                continue
            
            print(f"[{idx}/{total_activities}] Fetching streams for activity {activity_id}: {activity_name}")
            
            # Get streams for this activity
            streams = self.get_activity_streams(activity_id, types=stream_types)
            
            if streams:
                activity_streams[activity_id] = {
                    'activity_name': activity_name,
                    'activity_date': activity.get('start_date'),
                    'distance': activity.get('distance'),
                    'moving_time': activity.get('moving_time'),
                    'streams': streams
                }
                print(f"    ✓ Retrieved {len(streams)} stream types")
            else:
                print(f"    ✗ No streams available")
            
            # Rate limiting - be nice to Strava's API
            time.sleep(0.3)
        
        print(f"\n{'='*60}")
        print(f"Summary: Retrieved streams for {len(activity_streams)}/{total_activities} activities")
        print(f"{'='*60}\n")
        
        return activity_streams
    
    def get_person_streams_with_summary(self, person_initial: str, days_back: int = 365,
                                       stream_types: Optional[List[str]] = None,
                                       print_summary: bool = True) -> Dict[int, Dict]:
        """
        Get activity streams for a person and optionally print a summary report.
        
        This is a convenience method that combines get_person_activity_streams() with
        a summary report. For file saving and processing, use StravaDataProcessor methods.
        
        Args:
            person_initial: The person's initial to filter by
            days_back: Number of days to look back
            stream_types: List of stream types to retrieve
            print_summary: Whether to print a summary report
        
        Returns:
            Dictionary mapping activity_id to stream data
        """
        # Get streams
        activity_streams = self.get_person_activity_streams(
            person_initial=person_initial,
            days_back=days_back,
            stream_types=stream_types
        )
        
        if not activity_streams:
            return {}
        
        # Print summary report if requested
        if print_summary:
            print("\n" + "="*60)
            print("STREAMS SUMMARY REPORT")
            print("="*60)
            
            for activity_id, activity_data in activity_streams.items():
                print(f"\nActivity ID: {activity_id}")
                print(f"  Name: {activity_data['activity_name']}")
                print(f"  Date: {activity_data['activity_date']}")
                if activity_data.get('distance'):
                    print(f"  Distance: {activity_data['distance']/1000:.2f} km")
                if activity_data.get('moving_time'):
                    print(f"  Moving Time: {activity_data['moving_time']/60:.1f} minutes")
                
                streams = activity_data.get('streams', [])
                if streams:
                    stream_types_list = [s.get('type') for s in streams]
                    print(f"  Stream Types: {', '.join(stream_types_list)}")
                    print(f"  Stream Count: {len(streams)}")
            
            print("\n" + "="*60)
        
        return activity_streams


# StravaDataProcessor moved to strava_data_processing.py


def setup_strava_config() -> StravaConfig:
    """
    Set up Strava configuration from environment variables or user input.
    You'll need to get these values from your Strava app settings.
    """
    print("Setting up Strava configuration...")
    print("You'll need to create a Strava app at https://www.strava.com/settings/api")
    print("and get your Client ID, Client Secret, and generate tokens.")
    
    # Try to get from environment variables first
    client_id = 168193
    client_secret = "ENTER-YOUR-CLIENT-SECRET-KEY-HERE"
    access_token = "ENTER-YOUR-ACCESS-TOKEN-HERE"
    refresh_token = "ENTER-YOUR-REFRESH-TOKEN-HERE"
    
    if not all([client_id, client_secret, access_token, refresh_token]):
        print("\nPlease provide your Strava API credentials:")
        client_id = input("Client ID: ").strip()
        client_secret = input("Client Secret: ").strip()
        access_token = input("Access Token: ").strip()
        refresh_token = input("Refresh Token: ").strip()
    
    return StravaConfig(
        client_id=client_id,
        client_secret=client_secret,
        access_token=access_token,
        refresh_token=refresh_token
    )


def main():
    """Main function to demonstrate usage."""
    try:
        # Setup configuration
        config = setup_strava_config()
        
        # Initialize API
        api = StravaAPI(config)
        
        # Test connection
        print("Testing connection to Strava API...")
        athlete_info = api.get_athlete_info()
        if athlete_info:
            print(f"Connected successfully! Hello {athlete_info.get('firstname', '')} {athlete_info.get('lastname', '')}")
        else:
            print("Failed to connect to Strava API. Please check your credentials.")
            return
        
        # Get activities from the last year
        print("\nFetching activities from the last 365 days...")
        all_activities = api.get_all_activities(days_back=365)
        
        if not all_activities:
            print("No activities found.")
            return
        
        # Example: Get activities for a specific person by their initial
        # You can change 'A' to any person's initial (e.g., 'B', 'JD', etc.)
        person_initial = 'An'
        print(f"\nFetching activities for person with initial '{person_initial}'...")
        person_activities = api.get_activities_by_person(person_initial, days_back=365)
        
        if person_activities:
            print(f"Processing {len(person_activities)} activities for person {person_initial}...")
            person_processor = StravaDataProcessor(person_activities)
            person_df = person_processor.activities_to_dataframe()
            
            # Save person-specific activities to CSV
            person_output_file = f"strava_person_{person_initial.lower()}_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            person_df.to_csv(person_output_file, index=False)
            print(f"Person-specific data saved to: {person_output_file}")
            
            # Get summary for this person
            person_summary = person_processor.get_activity_summary(person_df)
            print(f"\n=== ACTIVITIES SUMMARY FOR PERSON {person_initial.upper()} ===")
            print(f"Total activities: {person_summary['total_activities']}")
            print(f"Total distance: {person_summary['total_distance_km']:.2f} km")
            print(f"Total time: {person_summary['total_time_hours']:.2f} hours")
            print(f"Average distance: {person_summary['average_distance_km']:.2f} km")
            if person_summary.get('average_pace_min_per_km'):
                print(f"Average pace: {person_summary['average_pace_min_per_km']:.2f} min/km")
        else:
            print(f"No activities found for person with initial '{person_initial}'")

        # Get detailed stream data for a specific activity
        print("\nFetching detailed stream data for activity 15127990666...")
        activity_streams = api.get_activity_streams(15127990666)

        if not activity_streams:
            print("No activity stream data found.")
        else:
            print(f"Retrieved stream data with {len(activity_streams)} stream types")

        # Get activity details data for a specific activity
        print("\nFetching activity details data for activity 15127990666...")
        activity_details = api.get_activity_details(15199768725)

        if not activity_details:
            print("No activity details data found.")
        else:
            print(f"Retrieved activity details data with {len(activity_details)} details")

        # Initialize data processor with activities list (can re-instantiate for other data types)
        processor = StravaDataProcessor(all_activities)
        
        # Filter for running activities
        running_activities = processor.filter_running_activities(all_activities)
        
        if not running_activities:
            print("No running activities found.")
            return
        
        # Convert to DataFrame via processor (source data provided in constructor or args)
        running_df = StravaDataProcessor(running_activities).activities_to_dataframe()
        
        # Convert activity details to DataFrame if available
        if activity_details:
            df_details = StravaDataProcessor(activity_details).activity_details_to_dataframe()
        
        # Convert stream data to DataFrame if available
        if activity_streams:
            df_streams = StravaDataProcessor(activity_streams).streams_to_dataframe()
        
        # Generate summary
        summary = processor.get_activity_summary(running_df)
        
        print("\n=== RUNNING ACTIVITIES SUMMARY ===")
        print(f"Total running activities: {summary['total_activities']}")
        print(f"Total distance: {summary['total_distance_km']:.2f} km")
        print(f"Total time: {summary['total_time_hours']:.2f} hours")
        print(f"Average distance: {summary['average_distance_km']:.2f} km")
        print(f"Average pace: {summary['average_pace_min_per_km']:.2f} min/km")
        print(f"Total elevation gain: {summary['total_elevation_gain_m']:.0f} m")
        if summary['average_heartrate']:
            print(f"Average heart rate: {summary['average_heartrate']:.0f} bpm")
        print(f"Date range: {summary['date_range']['first_activity'].date()} to {summary['date_range']['last_activity'].date()}")
        
        # Save to CSV
        output_file = f"strava_running_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        running_df.to_csv(output_file, index=False)
        print(f"\nData saved to: {output_file}")

        # Save activity details if available
        if not df_details.empty:
            output_file_details = f"strava_details_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df_details.to_csv(output_file_details, index=False)
            print(f"Activity details saved to: {output_file_details}")
            print(f"Activity details shape: {df_details.shape}")
            print("Available detail fields:", list(df_details.columns))
        else:
            print("No activity details available to save.")
        
        # Save stream data if available
        if not df_streams.empty:
            print(df_streams)
            output_streams = f"strava_streams_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df_streams.to_csv(output_streams, index=False)
            print(f"Stream data saved to: {output_streams}")
            print(f"Stream data shape: {df_streams.shape}")
            print("Available stream types:", list(df_streams.columns))
        else:
            print("No stream data available to save.")
        # Display first few rows
        print("\nFirst 5 activities:")
        print(running_df[['name', 'date', 'distance', 'moving_time', 'average_speed']].head())
        
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
