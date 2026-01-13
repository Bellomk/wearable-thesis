"""
Example script showing how to use ChatGPTConnector with Strava data.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from connectors.chatgpt_connector import ChatGPTConnector, analyze_strava_activity, analyze_strava_dataframe
from strava.strava_data_puller import StravaAPI, StravaConfig, setup_strava_config
from strava.strava_data_processing import StravaDataProcessor
import os
import json


def example_analyze_csv_file():
    """Example: Analyze a CSV file that was saved from Strava data."""
    
    # Set your OpenAI API key (or set OPENAI_API_KEY environment variable)
    api_key = os.getenv('OPENAI_API_KEY') or 'ENTER-YOUR-OPENAI-API-KEY-HERE'
    print(api_key)
    # Path to your CSV file (relative to project root or absolute path)
    csv_file = os.path.join('..', 'strava_person_a_data_20251011_010454.csv')  # Change to your file name
    
    # Create connector
    connector = ChatGPTConnector(api_key)
    
    # System message to set context
    system_message = """You are a sports scientist and running coach expert. 
    You are provided a csv file with acitivities performed by a single person.
    The activities are of 3 different types: Running, Stair Climbing and Idle Resting.
    Running has 2 further subtypes: Higher paced running and Lower paced running. These activities all have "Running" in their name.
    Stair Climbing activities have"Treppe" in their name.
    Idle Resting activities have "Rest" in their name.
    Analyze the provided Strava activity data and provide insights about the athlete's fitness."""
    
    # Your custom prompt
    prompt = """Please analyze this Strava running activity and provide:

1. Activity Summary (distance, time, pace, elevation, HR)
2. Performance Assessment and fitness level
3. Aerobic efficiency analysis
4. Heart rate zone distribution estimates
5. Fitness grade (A-F)
6. Three specific training recommendations

Be specific and data-driven."""
    
    # Send file and prompt to ChatGPT
    print("Sending data to ChatGPT for analysis...")
    response = connector.send_file_with_prompt(csv_file, prompt, system_message)
    
    print("\n" + "="*80)
    print("CHATGPT ANALYSIS:")
    print("="*80)
    print(response)
    
    return response


def example_analyze_live_data():
    """Example: Fetch Strava data and analyze it with ChatGPT."""
    
    # Setup Strava
    config = setup_strava_config()
    api = StravaAPI(config)
    
    # Get activities for a specific person
    person_initial = 'A'
    activities = api.get_activities_by_person(person_initial, days_back=180)
    
    if not activities:
        print("No activities found.")
        return
    
    # Convert to DataFrame
    processor = StravaDataProcessor(activities)
    df = processor.activities_to_dataframe()
    
    # Setup ChatGPT
    api_key = os.getenv('OPENAI_API_KEY') or 'ENTER-YOUR-OPENAI-API-KEY-HERE'
    connector = ChatGPTConnector(api_key)
    
    # Analyze with ChatGPT
    system_message = """You are a sports scientist and running coach expert. 
    You are provided a csv file with acitivities performed by a single person.
    The activities are of 3 different types: Running, Stair Climbing and Idle Resting.
    Running has 2 further subtypes: Higher paced running and Lower paced running. These activities all have "Running" in their name.
    Stair Climbing activities have "Treppe" in their name.
    Idle Resting activities have "Rest" in their name.
    Analyze the provided Strava activity data and provide insights about the athlete's fitness."""
    
    prompt = f"""Analyze the last 180 days of running activities for athlete {person_initial}:

1. Training volume summary
2. Consistency and frequency patterns
3. Performance trends
4. Key insights and observations
5. Training recommendations for the next month

Be specific and actionable."""
    
    print(f"\nAnalyzing {len(activities)} activities for person {person_initial}...")
    response = connector.send_dataframe_with_prompt(df, prompt, system_message)
    
    print("\n" + "="*80)
    print("CHATGPT ANALYSIS:")
    print("="*80)
    print(response)
    
    return response


def example_analyze_specific_activity():
    """Example: Get a specific activity's details and analyze with ChatGPT."""
    
    # Setup Strava
    config = setup_strava_config()
    api = StravaAPI(config)
    
    # Get specific activity details
    activity_id = 15093834011  # Change to your activity ID
    activity_details = api.get_activity_details(activity_id)
    
    if not activity_details:
        print("Activity not found.")
        return
    
    # Convert to DataFrame
    processor = StravaDataProcessor(activity_details)
    df = processor.activity_details_to_dataframe()
    
    # Setup ChatGPT
    api_key = os.getenv('OPENAI_API_KEY') or 'ENTER-YOUR-OPENAI-API-KEY-HERE'
    connector = ChatGPTConnector(api_key)
    
    # Create detailed analysis prompt
    system_message = """You are an expert sports scientist specializing in endurance training. 
    Analyze activity data with scientific rigor and provide evidence-based recommendations."""
    
    prompt = """Analyze this specific running activity in detail:

1. **Session Overview**: Summarize key metrics
2. **Aerobic Fitness Assessment**: 
   - Calculate and analyze pace vs heart rate relationship
   - Estimate aerobic efficiency (min/km per 10 bpm)
3. **Intensity Distribution**: 
   - Estimate time in different HR zones
   - Assess if intensity was appropriate for the session
4. **Performance Indicators**:
   - Pace sustainability
   - Cadence analysis
   - Elevation/terrain impact
5. **Fitness Grade**: Provide A-F grade with detailed justification
6. **Specific Recommendations**: 3 actionable next steps

Use the data to make specific, measurable observations."""
    
    print(f"\nAnalyzing activity {activity_id}...")
    response = connector.send_dataframe_with_prompt(df, prompt, system_message)
    
    print("\n" + "="*80)
    print("CHATGPT ANALYSIS:")
    print("="*80)
    print(response)
    
    # Optionally save the response
    output_file = f"chatgpt_analysis_{activity_id}.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(response)
    print(f"\nAnalysis saved to: {output_file}")
    
    return response


def example_custom_prompt():
    """Example: Use a completely custom prompt with your own file."""
    
    api_key = os.getenv('OPENAI_API_KEY') or 'ENTER-YOUR-OPENAI-API-KEY-HERE'
    connector = ChatGPTConnector(api_key)
    
    # Your file path (relative to project root or absolute path)
    file_path = os.path.join('..', 'strava_person_a_data_20250907_163239.csv')
    
    # Your custom system message
    system_message = "You are a data analyst specializing in fitness and health metrics."
    
    # Your custom prompt
    prompt = """Look at this data and tell me:
    1. What patterns do you see?
    2. Is this person improving over time?
    3. What should they focus on next?"""
    
    response = connector.send_file_with_prompt(file_path, prompt, system_message)
    
    print("\n" + "="*80)
    print("CHATGPT RESPONSE:")
    print("="*80)
    print(response)
    
    return response


def example_multi_turn_conversation():
    """Example: Have a multi-turn conversation about the data."""
    
    api_key = os.getenv('OPENAI_API_KEY') or 'ENTER-YOUR-OPENAI-API-KEY-HERE'
    connector = ChatGPTConnector(api_key)
    
    # Build a conversation
    messages = [
        {"role": "system", "content": "You are a running coach analyzing training data."},
        {"role": "user", "content": "I ran 10km in 55 minutes with average HR of 165. Is this good?"},
    ]
    
    response1 = connector.create_conversation(messages)
    print("Assistant:", response1)
    
    # Continue conversation
    messages.append({"role": "assistant", "content": response1})
    messages.append({"role": "user", "content": "My max HR is 195. What zone was I in?"})
    
    response2 = connector.create_conversation(messages)
    print("\nAssistant:", response2)
    
    return response2


def example_analyze_jsonl_file():
    """Example: Send a JSONL file (e.g., output from stream_jsonl_processor) to ChatGPT."""

    # Setup ChatGPT connector
    api_key = os.getenv('OPENAI_API_KEY') or 'ENTER-YOUR-OPENAI-API-KEY-HERE'
    connector = ChatGPTConnector(api_key)

    # Path to the JSONL file (update with your generated file)
    jsonl_file = os.path.join('..', 'streams', 'person_An_streams_5s_abnormal.jsonl')

    if not os.path.exists(jsonl_file):
        print(f"JSONL file not found: {jsonl_file}\nGenerate one using example_stream_jsonl.py first.")
        return

    # Read JSONL content
    with open(jsonl_file, 'r', encoding='utf-8') as f:
        jsonl_lines = f.readlines()

    # Build prompt and system instructions
    system_message = """You are a sports scientist and data analyst. Analyze the provided JSONL activity stream data.
Each JSON line represents one activity with metadata (distance, time, etc.), sampled streams (at ~5s intervals),
and pre-computed quantiles. All the activities were performed by a single person, using multiple wearable devices.
There are in total 3 types of activities: Running, Stair Climbing and Idle Resting.
The running activities have 2 further subtypes: Higher paced running, and Lower paced running. These activities all have "Running" in their name.
Lower paced running activities have an odd number in their name, right after the "Running" in their name.
Higher paced running activities have an even number in their name, right after the "Running" in their name.
Stair Climbing activities have "Treppe" in their name.
Idle Resting activities have "Rest" in their name.
The running activities were performed in successive rounds, with each round starting with a lower paced running activity followed by a higher paced running activity and ending with a rest activity.
The stair climbing activities were performed seperately, a bit before the running activities.
All activities have a JSON object with the key "streams_compact" that contains the sampled streams.
The running activities streams are filtered before sampling to include only the points where movement was detected.
Furthermore, the running activities JSONs include pace and velocity data, unlike the stair climbing and the rest activities.
Identify patterns, compare activity types (Running, Treppe, Rest), and give insights."""

    prompt = f"""The attached JSONL file contains {len(jsonl_lines)} activities.
Please summarize:
1. Overall trends (distance, heart rate, cadence, altitude).
2. Differences between activity types (Running vs. Treppe vs. Rest).
3. Any outliers or unusual sessions.
4. Your assessment of the person's fitness.
5. Recommendations for training focus to improve the person's fitness.

If present, use quantiles to describe distributions."""

    print(f"Sending JSONL data to ChatGPT for analysis ({jsonl_file})...")

    response = connector.send_file_with_prompt(
        jsonl_file,
        prompt,
        system_message
    )

    print("\n" + "=" * 80)
    print("CHATGPT ANALYSIS (JSONL):")
    print("=" * 80)
    print(response)

    return response


if __name__ == "__main__":
    print("ChatGPT + Strava Integration Examples\n")
    print("Choose an example to run:")
    print("1. Analyze a CSV file")
    print("2. Analyze live Strava data (last 180 days)")
    print("3. Analyze a specific activity with detailed analysis")
    print("4. Use custom prompt")
    print("5. Multi-turn conversation")
    print("6. Analyze a JSONL file")
    
    choice = input("\nEnter choice (1-6): ").strip()
    
    try:
        if choice == '1':
            example_analyze_csv_file()
        elif choice == '2':
            example_analyze_live_data()
        elif choice == '3':
            example_analyze_specific_activity()
        elif choice == '4':
            example_custom_prompt()
        elif choice == '5':
            example_multi_turn_conversation()
        elif choice == '6':
            example_analyze_jsonl_file()
        else:
            print("Invalid choice. Please run again and select 1-6.")
    except Exception as e:
        print(f"\nError: {e}")
        print("\nMake sure you have:")
        print("1. Set OPENAI_API_KEY environment variable or update the api_key in the script")
        print("2. Installed required packages: pip install -r requirements.txt")
        print("3. Have valid Strava data files or credentials")

