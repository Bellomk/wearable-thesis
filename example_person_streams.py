"""
Example script showing how to use get_person_activity_streams() to retrieve
all stream data for activities belonging to a specific person.
"""

from strava_data_puller import StravaAPI, setup_strava_config
from strava_data_processing import StravaDataProcessor
import os

# Create streams directory if it doesn't exist
STREAMS_DIR = "streams"
os.makedirs(STREAMS_DIR, exist_ok=True)


def example_get_person_streams():
    """
    Example: Get all activity streams for a specific person using class methods.
    """
    # Setup Strava API
    print("Setting up Strava connection...")
    config = setup_strava_config()
    api = StravaAPI(config)
    
    # Test connection
    athlete_info = api.get_athlete_info()
    if athlete_info:
        print(f"Connected! Hello {athlete_info.get('firstname', '')} {athlete_info.get('lastname', '')}\n")
    else:
        print("Failed to connect to Strava API")
        return
    
    # Get streams for person 'A'
    person_initial = 'An'  # Change to your person's initial
    days_back = 180  # Last 180 days
    
    print(f"Fetching all activity streams for person '{person_initial}'...")
    print("="*60)
    
    # Use StravaAPI method to get streams with summary
    activity_streams = api.get_person_streams_with_summary(
        person_initial=person_initial,
        days_back=days_back,
        stream_types=['time', 'distance', 'latlng', 'altitude', 'heartrate', 'velocity_smooth', 'cadence', 'grade_adjusted_speed', 'velocity', 'moving'],
        print_summary=True
    )
    
    if not activity_streams:
        print(f"No streams found for person '{person_initial}'")
        return
    
    # Process and save streams using StravaDataProcessor methods
    processor = StravaDataProcessor(None)
    
    # Save individual CSV files
    processed_streams = processor.save_person_streams_to_files(
        activity_streams_dict=activity_streams,
        person_initial=person_initial,
        output_dir=STREAMS_DIR
    )
    
    # Create and save summary JSON
    summary_file = processor.create_streams_summary_json(
        activity_streams_dict=activity_streams,
        person_initial=person_initial,
        output_dir=STREAMS_DIR
    )
    
    # Print detailed summary with DataFrame info
    print("\n" + "="*60)
    print("DETAILED SUMMARY WITH DATA INFO")
    print("="*60)
    
    for activity_id, activity_data in activity_streams.items():
        print(f"\nActivity ID: {activity_id}")
        print(f"  Name: {activity_data['activity_name']}")
        print(f"  Date: {activity_data['activity_date']}")
        print(f"  Distance: {activity_data['distance']/1000:.2f} km")
        print(f"  Moving Time: {activity_data['moving_time']/60:.1f} minutes")
        
        if activity_id in processed_streams:
            df = processed_streams[activity_id]
            print(f"  Stream Data Points: {len(df)}")
            print(f"  Available Streams: {[col for col in df.columns if col not in ['activity_id', 'activity_name', 'activity_date']]}")
    
    return activity_streams, processed_streams


def example_analyze_person_streams():
    """
    Example: Get streams and perform analysis.
    """
    # Get streams
    person_initial = 'An'
    print(f"Analyzing streams for person '{person_initial}'...\n")
    
    config = setup_strava_config()
    api = StravaAPI(config)
    
    # Get streams for last 7 days (fewer activities for quick testing)
    activity_streams = api.get_person_activity_streams(
        person_initial=person_initial,
        days_back=180
    )
    
    if not activity_streams:
        print("No streams found")
        return
    
    # Process streams
    processor = StravaDataProcessor(None)
    processed_streams = processor.process_multiple_activity_streams(activity_streams)
    
    # Analyze each activity
    print("\n" + "="*60)
    print("STREAM ANALYSIS")
    print("="*60)
    
    for activity_id, df in processed_streams.items():
        print(f"\n{df['activity_name'].iloc[0]} (ID: {activity_id})")
        print("-" * 60)

        if 'distance' in df.columns:
            print(f"  Max Distance: {df['distance'].max():.2f} m")
        
        if 'altitude' in df.columns:
            altitude_gain = df['altitude'].diff().clip(lower=0).sum()
            print(f"  Total Elevation Gain: {altitude_gain:.0f} m")
            print(f"  Max Altitude: {df['altitude'].max():.0f} m")
            print(f"  Min Altitude: {df['altitude'].min():.0f} m")
        
        if 'heartrate' in df.columns:
            print(f"  Average Heart Rate: {df['heartrate'].mean():.0f} bpm")
            print(f"  Max Heart Rate: {df['heartrate'].max():.0f} bpm")
        
        if 'time' in df.columns:
            print(f"  Total Time: {df['time'].max():.0f} seconds ({df['time'].max()/60:.1f} min)")
        
        print(f"  Data Points: {len(df)}")


def example_combine_person_streams():
    """
    Example: Combine all streams for a person into a single DataFrame using class method.
    """
    person_initial = 'A'
    
    config = setup_strava_config()
    api = StravaAPI(config)
    
    print(f"Getting all streams for person '{person_initial}'...")
    activity_streams = api.get_person_activity_streams(person_initial, days_back=180)
    
    if not activity_streams:
        print("No streams found")
        return None
    
    # Use StravaDataProcessor method to combine streams
    processor = StravaDataProcessor(None)
    combined_df = processor.combine_person_streams(
        activity_streams_dict=activity_streams,
        person_initial=person_initial,
        output_dir=STREAMS_DIR
    )
    
    return combined_df


if __name__ == "__main__":
    print("Person Activity Streams Examples\n")
    print("Choose an example to run:")
    print("1. Get all streams for a person and save to files")
    print("2. Get streams and perform analysis")
    print("3. Combine all streams into a single file")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    try:
        if choice == '1':
            example_get_person_streams()
        elif choice == '2':
            example_analyze_person_streams()
        elif choice == '3':
            example_combine_person_streams()
        else:
            print("Invalid choice. Running default example...")
            example_get_person_streams()
    except Exception as e:
        print(f"\nError: {e}")
        print("\nMake sure you have:")
        print("1. Valid Strava API credentials configured")
        print("2. Activities with the correct naming convention")
        print("3. Internet connection")

