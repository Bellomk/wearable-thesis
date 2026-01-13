"""
Example script showing how to use stream_jsonl_processor functions
to create JSONL files from Strava activity streams.
"""

import sys
import os

# Add parent directory to path for imports when running as script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strava.strava_data_puller import StravaAPI, setup_strava_config
from strava.stream_jsonl_processor import (
    sample_streams_at_intervals,
    create_streams_compact_json,
    create_activity_jsonl_object,
    save_jsonl_file,
    combine_activities_to_jsonl,
    modify_heartrate_to_abnormal
)


def example_sample_single_activity_streams():
    """
    Example: Sample streams from a single activity.
    """
    # Setup Strava API
    config = setup_strava_config()
    api = StravaAPI(config)
    
    # Get streams for a specific activity
    activity_id = 16324835978  # Change to your activity ID
    print(f"Fetching streams for activity {activity_id}...")
    
    streams_data = api.get_activity_streams(
        activity_id,
        types=['time', 'distance', 'latlng', 'altitude', 'heartrate', 'velocity_smooth', 'cadence', 'moving']
    )
    
    if not streams_data:
        print("No streams found")
        return
    
    # Sample streams at 5-second intervals
    print("\nSampling streams at 5-second intervals...")
    compact_streams, quantiles = sample_streams_at_intervals(streams_data, interval_seconds=5.0)
    
    print("\nCompact Streams Format:")
    print("=" * 60)
    for key, value in compact_streams.items():
        if isinstance(value, str) and len(value) > 100:
            print(f"{key}: {value[:100]}... (truncated)")
        else:
            print(f"{key}: {value}")

    if quantiles:
        print("\nQuantiles:")
        print("=" * 60)
        for stream_type, q_values in quantiles.items():
            print(f"{stream_type}: {q_values}")
    
    # Create full JSON object
    json_obj = create_streams_compact_json(
        streams_data,
        interval_seconds=5.0,
        activity_name="Running activity"
    )
    
    print("\n\nFull JSON Object:")
    print("=" * 60)
    import json
    print(json.dumps(json_obj, indent=2))
    
    return compact_streams


def example_create_activity_jsonl():
    """
    Example: Create a complete JSONL object for an activity with streams.
    """
    config = setup_strava_config()
    api = StravaAPI(config)
    
    activity_id = 15093834011
    print(f"Creating JSONL object for activity {activity_id}...")
    
    # Get activity details
    activity_details = api.get_activity_details(activity_id)
    if not activity_details:
        print("Activity not found")
        return
    
    # Get streams
    streams_data = api.get_activity_streams(
        activity_id,
        types=['time', 'distance', 'altitude', 'heartrate', 'velocity_smooth', 'cadence', 'moving']
    )
    
    # Create JSONL object
    jsonl_obj = create_activity_jsonl_object(
        activity_data=activity_details,
        streams_data=streams_data,
        interval_seconds=5.0
    )
    
    print("\nJSONL Object:")
    print("=" * 60)
    import json
    print(json.dumps(jsonl_obj, indent=2))
    
    return jsonl_obj


def example_create_jsonl_file():
    """
    Example: Create a JSONL file from multiple activities.
    """
    config = setup_strava_config()
    api = StravaAPI(config)
    
    # Get activities for a person
    person_initial = 'An'
    print(f"Getting activities for person '{person_initial}'...")
    
    activities = api.get_activities_by_person(person_initial, days_back=180)
    
    if not activities:
        print("No activities found")
        return
    
    print(f"Found {len(activities)} activities")
    print("Fetching streams for each activity...")
    
    # Get streams for each activity
    streams_dict = {}
    for activity in activities[:5]:  # Limit to first 5 for example
        activity_id = activity.get('id')
        if activity_id:
            print(f"  Fetching streams for activity {activity_id}...")
            streams = api.get_activity_streams(
                activity_id,
                types=['time', 'distance', 'altitude', 'heartrate', 'velocity_smooth', 'cadence', 'moving']
            )
            if streams:
                streams_dict[activity_id] = streams
    
    # Create JSONL objects
    print("\nCreating JSONL objects...")
    jsonl_objects = combine_activities_to_jsonl(
        activities=activities[:5],
        streams_dict=streams_dict,
        interval_seconds=5.0
    )
    
    # Save to JSONL file (at project root)
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(PROJECT_ROOT, "streams")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"activities_{person_initial}_5s.jsonl")
    
    save_jsonl_file(jsonl_objects, output_file)
    
    print(f"\n✓ Saved {len(jsonl_objects)} activities to: {output_file}")
    
    # Show first object as example
    if jsonl_objects:
        print("\nFirst JSONL object (example):")
        print("=" * 60)
        import json
        print(json.dumps(jsonl_objects[0], indent=2))
    
    return jsonl_objects


def example_create_person_jsonl_file():
    """
    Example: Create a JSONL file for all activities of a person with their streams.
    """
    config = setup_strava_config()
    api = StravaAPI(config)
    
    person_initial = 'An'
    days_back = 180
    
    print(f"Creating JSONL file for person '{person_initial}' (last {days_back} days)...")
    
    # Get all streams for the person
    activity_streams = api.get_person_activity_streams(
        person_initial=person_initial,
        days_back=days_back,
        stream_types=['time', 'distance', 'altitude', 'heartrate', 'velocity_smooth', 'cadence', 'moving']
    )
    
    if not activity_streams:
        print("No streams found")
        return
    
    # Extract activities and streams
    activities = []
    streams_dict = {}
    
    for activity_id, activity_data in activity_streams.items():
        # Create activity dict from the metadata
        activity = {
            'id': activity_id,
            'name': activity_data.get('activity_name'),
            'start_date': activity_data.get('activity_date'),
            'distance': activity_data.get('distance'),
            'moving_time': activity_data.get('moving_time'),
        }
        activities.append(activity)
        streams_dict[activity_id] = activity_data.get('streams', [])
    
    # Create JSONL objects
    print(f"\nCreating JSONL objects for {len(activities)} activities...")
    jsonl_objects = combine_activities_to_jsonl(
        activities=activities,
        streams_dict=streams_dict,
        interval_seconds=5.0
    )
    
    # Save to JSONL file (at project root)
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(PROJECT_ROOT, "streams")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"person_{person_initial}_streams_5s.jsonl")
    
    save_jsonl_file(jsonl_objects, output_file)
    
    print(f"\n✓ Saved {len(jsonl_objects)} activities to: {output_file}")
    print(f"  File size: {os.path.getsize(output_file) / 1024:.2f} KB")
    
    return jsonl_objects


def example_modify_heartrate_to_abnormal():
    """
    Example: Modify heartrate values in a JSONL file to abnormally high values.
    """
    # Default input file (you can change this)
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_file = os.path.join(PROJECT_ROOT, "streams", "person_An_streams_5s.jsonl")
    
    # Check if file exists
    if not os.path.exists(input_file):
        print(f"Input file not found: {input_file}")
        print("Please create a JSONL file first using example 4, or specify a different file path.")
        return
    
    # Create output filename
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    output_dir = os.path.join(PROJECT_ROOT, "streams")
    output_file = os.path.join(output_dir, f"{base_name}_abnormal.jsonl")
    
    print(f"Modifying heartrate values in: {input_file}")
    print(f"Output file: {output_file}")
    print("Heartrate range: 210-240 bpm")
    
    # Call the function to modify heartrate values
    modify_heartrate_to_abnormal(
        jsonl_filepath=input_file,
        output_filepath=output_file,
        min_hr=210,
        max_hr=240
    )
    
    print(f"\n✓ Successfully created modified file: {output_file}")
    print(f"  File size: {os.path.getsize(output_file) / 1024:.2f} KB")
    
    return output_file


if __name__ == "__main__":
    print("Stream JSONL Processing Examples\n")
    print("Choose an example to run:")
    print("1. Sample streams from a single activity")
    print("2. Create JSONL object for a single activity")
    print("3. Create JSONL file from multiple activities")
    print("4. Create JSONL file for all person's activities")
    print("5. Modify heartrate values to abnormal range (210-240 bpm)")
    
    choice = input("\nEnter choice (1-5): ").strip()
    
    try:
        if choice == '1':
            example_sample_single_activity_streams()
        elif choice == '2':
            example_create_activity_jsonl()
        elif choice == '3':
            example_create_jsonl_file()
        elif choice == '4':
            example_create_person_jsonl_file()
        elif choice == '5':
            example_modify_heartrate_to_abnormal()
        else:
            print("Invalid choice. Running default example...")
            example_sample_single_activity_streams()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

