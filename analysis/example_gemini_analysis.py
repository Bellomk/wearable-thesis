"""
Example script showing how to use GeminiConnector with Strava data.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from connectors.gemini_connector import GeminiConnector, analyze_strava_activity, analyze_strava_dataframe
from strava.strava_data_puller import StravaAPI, StravaConfig, setup_strava_config
from strava.strava_data_processing import StravaDataProcessor
import os


def example_analyze_csv_file():
    """Example: Analyze a CSV file that was saved from Strava data."""
    
    # Set your Gemini API key (or set GEMINI_API_KEY environment variable)
    api_key = os.getenv('GEMINI_API_KEY') or 'ENTER-YOUR-GEMINI-API-KEY-HERE'
    
    # Path to your CSV file (relative to project root or absolute path)
    csv_file = os.path.join('..', 'strava_details_data_20250907_193806.csv')  # Change to your file name
    
    # Create connector
    connector = GeminiConnector(api_key)
    
    # System message to set context
    system_message = """You are a sports scientist and running coach expert. 
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
    
    # Send file and prompt to Gemini
    print("Sending data to Gemini AI for analysis...")
    response = connector.send_file_with_prompt(csv_file, prompt, system_message)
    
    print("\n" + "="*80)
    print("GEMINI AI ANALYSIS:")
    print("="*80)
    print(response)
    
    return response


def example_analyze_live_data():
    """Example: Fetch Strava data and analyze it with Gemini."""
    
    # Setup Strava
    config = setup_strava_config()
    api = StravaAPI(config)
    
    # Get activities for a specific person
    person_initial = 'A'
    activities = api.get_activities_by_person(person_initial, days_back=30)
    
    if not activities:
        print("No activities found.")
        return
    
    # Convert to DataFrame
    processor = StravaDataProcessor(activities)
    df = processor.activities_to_dataframe()
    
    # Setup Gemini
    api_key = os.getenv('GEMINI_API_KEY') or 'ENTER-YOUR-GEMINI-API-KEY-HERE'
    connector = GeminiConnector(api_key)
    
    # Analyze with Gemini
    system_message = """You are a sports scientist analyzing training data. 
    Provide insights about training patterns, volume, and recommendations."""
    
    prompt = f"""Analyze the last 30 days of running activities for athlete {person_initial}:

1. Training volume summary
2. Consistency and frequency patterns
3. Performance trends
4. Key insights and observations
5. Training recommendations for the next month

Be specific and actionable."""
    
    print(f"\nAnalyzing {len(activities)} activities for person {person_initial}...")
    response = connector.send_dataframe_with_prompt(df, prompt, system_message)
    
    print("\n" + "="*80)
    print("GEMINI AI ANALYSIS:")
    print("="*80)
    print(response)
    
    return response


def example_analyze_specific_activity():
    """Example: Get a specific activity's details and analyze with Gemini."""
    
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
    
    # Setup Gemini
    api_key = os.getenv('GEMINI_API_KEY') or 'ENTER-YOUR-GEMINI-API-KEY-HERE'
    connector = GeminiConnector(api_key)
    
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
    print("GEMINI AI ANALYSIS:")
    print("="*80)
    print(response)
    
    # Optionally save the response
    output_file = f"gemini_analysis_{activity_id}.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(response)
    print(f"\nAnalysis saved to: {output_file}")
    
    return response


def example_custom_prompt():
    """Example: Use a completely custom prompt with your own file."""
    
    api_key = os.getenv('GEMINI_API_KEY') or 'ENTER-YOUR-GEMINI-API-KEY-HERE'
    connector = GeminiConnector(api_key)
    
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
    print("GEMINI AI RESPONSE:")
    print("="*80)
    print(response)
    
    return response


def example_multi_turn_conversation():
    """Example: Have a multi-turn conversation about the data."""
    
    api_key = os.getenv('GEMINI_API_KEY') or 'ENTER-YOUR-GEMINI-API-KEY-HERE'
    connector = GeminiConnector(api_key)
    
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


def example_compare_with_chatgpt():
    """Example: Compare Gemini and ChatGPT analysis of the same data."""
    
    # Try importing both connectors
    try:
        from connectors.chatgpt_connector import ChatGPTConnector
        has_chatgpt = True
    except:
        has_chatgpt = False
    
    # File path (relative to project root or absolute path)
    csv_file = os.path.join('..', 'strava_details_data_20250907_193806.csv')
    
    # Prompt
    prompt = """Analyze this running activity and provide:
    1. Activity summary
    2. Fitness assessment (A-F grade)
    3. Top 3 recommendations"""
    
    system_msg = "You are a sports scientist."
    
    # Gemini Analysis
    print("=" * 80)
    print("GEMINI AI ANALYSIS:")
    print("=" * 80)
    gemini_key = os.getenv('GEMINI_API_KEY') or 'ENTER-YOUR-GEMINI-API-KEY-HERE'
    gemini = GeminiConnector(gemini_key)
    gemini_response = gemini.send_file_with_prompt(csv_file, prompt, system_msg)
    print(gemini_response)
    
    # ChatGPT Analysis (if available)
    if has_chatgpt:
        print("\n" + "=" * 80)
        print("CHATGPT ANALYSIS:")
        print("=" * 80)
        chatgpt_key = os.getenv('OPENAI_API_KEY') or 'ENTER-YOUR-OPENAI-API-KEY-HERE'
        chatgpt = ChatGPTConnector(chatgpt_key)
        chatgpt_response = chatgpt.send_file_with_prompt(csv_file, prompt, system_msg)
        print(chatgpt_response)
        
        # Save comparison
        with open('ai_comparison.txt', 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("GEMINI AI ANALYSIS:\n")
            f.write("=" * 80 + "\n")
            f.write(gemini_response + "\n\n")
            f.write("=" * 80 + "\n")
            f.write("CHATGPT ANALYSIS:\n")
            f.write("=" * 80 + "\n")
            f.write(chatgpt_response + "\n")
        
        print("\n\nComparison saved to: ai_comparison.txt")
    
    return gemini_response


if __name__ == "__main__":
    print("Gemini AI + Strava Integration Examples\n")
    print("Choose an example to run:")
    print("1. Analyze a CSV file")
    print("2. Analyze live Strava data (last 30 days)")
    print("3. Analyze a specific activity with detailed analysis")
    print("4. Use custom prompt")
    print("5. Multi-turn conversation")
    print("6. Compare Gemini vs ChatGPT analysis")
    
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
            example_compare_with_chatgpt()
        else:
            print("Invalid choice. Please run again and select 1-6.")
    except Exception as e:
        print(f"\nError: {e}")
        print("\nMake sure you have:")
        print("1. Set GEMINI_API_KEY environment variable or update the api_key in the script")
        print("2. Installed required packages: pip install -r requirements.txt")
        print("3. Have valid Strava data files or credentials")

