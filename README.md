# Strava Data Analysis with LLMs

This project provides tools to connect to Strava API, retrieve activity data, process it into JSONL format, and analyze it using Large Language Models (LLMs) like DeepSeek and ChatGPT.

## 🎯 Main Goal

The primary use case is to send JSONL files containing Strava activity stream data to LLM services for intelligent analysis and insights.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Analyzing JSONL Files](#analyzing-jsonl-files)
- [Configuration](#configuration)
- [Examples](#examples)

## 🔧 Prerequisites

- Python 3.8 or higher
- Strava account (if you want to pull your own data)
- API keys for:
  - **DeepSeek**: API key and base URL (if using DeepSeek)
  - **OpenAI**: API key (if using ChatGPT)
  - **Google**: API key (if using Gemini)

## 📦 Installation

1. **Clone or download this repository**

2. **Install required Python packages:**

```bash
pip install requests pandas openai google-generativeai numpy matplotlib seaborn
```

Or if you have a `requirements.txt` file:

```bash
pip install -r requirements.txt
```

## 📁 Project Structure

```
Thesis_code/
├── strava/                  # Strava API integration and data processing
│   ├── strava_data_puller.py       # Connect to Strava API
│   ├── strava_data_processing.py   # Data processing utilities
│   ├── stream_jsonl_processor.py   # JSONL file creation
│   ├── example_stream_jsonl.py     # Examples for creating JSONL files
│   └── get_token.py                # Helper to get Strava tokens
│
├── connectors/              # LLM connector classes
│   ├── chatgpt_connector.py        # ChatGPT/OpenAI connector
│   ├── deepseek_connector.py       # DeepSeek connector
│   └── gemini_connector.py         # Google Gemini connector
│
├── analysis/                # Analysis example scripts
│   ├── example_deepseek_analysis.py  # DeepSeek analysis examples
│   ├── example_chatgpt_analysis.py   # ChatGPT analysis examples
│   └── example_gemini_analysis.py    # Gemini analysis examples
│
└── streams/                 # Output directory for JSONL files (created automatically)
```

## 🚀 Getting Started

### Step 1: Get a JSONL File

You have two options:

#### Option A: Use an Existing JSONL File

If you already have a JSONL file with Strava activity data, place it in the `streams/` directory (create it if it doesn't exist).

#### Option B: Create a JSONL File from Strava Data

1. **Set up Strava API credentials** (see `strava/strava_setup_guide.md` for details):
   - Create a Strava app at https://www.strava.com/settings/api
   - Get your Client ID and Client Secret
   - Generate access and refresh tokens (this video is helpful for that: https://www.youtube.com/watch?v=sgscChKfGyg&list=PLO6KswO64zVvcRyk0G0MAzh5oKMLb6rTW)

2. **Update Strava credentials** in `strava/strava_data_puller.py`:
   ```python
   def setup_strava_config():
       client_id = YOUR_CLIENT_ID
       client_secret = "YOUR_CLIENT_SECRET"
       access_token = "YOUR_ACCESS_TOKEN"
       refresh_token = "YOUR_REFRESH_TOKEN"
   ```

3. **Generate a JSONL file**:
   ```bash
   python strava/example_stream_jsonl.py
   ```
   - Choose option `4` (Create JSONL file for all person's activities)
   - Enter the person's initial when prompted
   - The JSONL file will be saved in `streams/person_{initial}_streams_5s.jsonl`

### Step 2: Configure API Keys

#### For DeepSeek Analysis:

Edit `analysis/example_deepseek_analysis.py` lines 19 & 20 and update:

```python
DEEPSEEK_API_KEY = 'your-api-key-here'
DEEPSEEK_BASE_URL = 'your-deepseek-base-url-here'  # Your DeepSeek endpoint
```

Or set environment variables:
```bash
export DEEPSEEK_API_KEY='your-api-key-here'
export DEEPSEEK_BASE_URL='your-deepseek-base-url-here'
```

#### For ChatGPT Analysis:

Edit `analysis/example_chatgpt_analysis.py` line 235 (if you just want to analyse a JSONL file) and update the API key, or set:
```bash
export OPENAI_API_KEY='your-openai-api-key-here'
```

## 📊 Analyzing JSONL Files

### Using DeepSeek

1. **Navigate to the analysis directory**:
   ```bash
   cd analysis
   ```

2. **Run the DeepSeek analysis script**:
   ```bash
   python example_deepseek_analysis.py
   ```

3. **Choose option `6`** (Analyze a JSONL file)

4. **Update the file path** in `example_analyze_jsonl_file()` if needed:
   ```python
   jsonl_file = os.path.join('..', 'streams', 'your_file.jsonl')
   ```

The script will:
- Read your JSONL file
- Send it to DeepSeek with a detailed prompt
- Receive and display analysis results
- Provide insights about:
  - Overall trends (distance, heart rate, cadence, altitude)
  - Differences between activity types (Running vs. Treppe vs. Rest)
  - Outliers or unusual sessions
  - Fitness assessment
  - Training recommendations

### Using ChatGPT

1. **Navigate to the analysis directory**:
   ```bash
   cd analysis
   ```

2. **Run the ChatGPT analysis script**:
   ```bash
   python example_chatgpt_analysis.py
   ```

3. **Choose option `6`** (Analyze a JSONL file)

4. **Update the file path** in `example_analyze_jsonl_file()` if needed:
   ```python
   jsonl_file = os.path.join('..', 'streams', 'your_file.jsonl')
   ```

The ChatGPT connector works similarly and will provide detailed analysis of your JSONL data.

## 🔧 Direct Usage (Python Code)

You can also use the connectors directly in your own Python scripts:

### Using DeepSeek Connector

```python
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from connectors.deepseek_connector import DeepSeekConnector

# Initialize connector
connector = DeepSeekConnector(
    api_key='your-api-key',
    base_url='your-deepseek-base-url-here'
)

# Analyze a JSONL file
jsonl_file = 'streams/person_An_streams_5s.jsonl'
response = connector.send_file_with_prompt(
    file_path=jsonl_file,
    prompt='Analyze this activity data and provide fitness insights.',
    system_message='You are a sports scientist.'
)

print(response)
```

### Using ChatGPT Connector

```python
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from connectors.chatgpt_connector import ChatGPTConnector

# Initialize connector
connector = ChatGPTConnector(api_key='your-openai-api-key')

# Analyze a JSONL file
jsonl_file = 'streams/person_An_streams_5s.jsonl'
response = connector.send_file_with_prompt(
    file_path=jsonl_file,
    prompt='Analyze this activity data and provide fitness insights.',
    system_message='You are a sports scientist.'
)

print(response)
```

## 📝 JSONL File Format

The JSONL files contain one JSON object per line. Each object represents a single activity with:

- **Metadata**: Activity name, date, distance, time, etc.
- **Streams Compact**: Sampled time-series data at ~5-second intervals. Contents of this object depend on the activity type.

  - **Running activities**:
    - `time_s_csv`: Timestamps
    - `hr_bpm_csv`: Heart rate values
    - `alt_m_csv`: Altitude values
    - `pace_s_per_km_csv`: Pace values (for running activities)
    - `velocity_smooth_csv`: Velocity values (for running activities)
    - `cadence_csv`: Cadence values

  - **Stair Climbing activities**:
    - `time_s_csv`: Timestamps
    - `hr_bpm_csv`: Heart rate values
    - `alt_m_csv`: Altitude values
    - `cadence_csv`: Cadence values

  - **Idle Rest sessions**:
    - `time_s_csv`: Timestamps
    - `hr_bpm_csv`: Heart rate values

- **Quantiles**: Pre-computed quantiles (5th, 25th, 50th, 75th, 95th percentiles) for key metrics

## 🎯 Activity Types

The system recognizes three main activity types:

1. **Running**: Activities with "Running" in the name
   - Lower paced: Odd number after "Running"
   - Higher paced: Even number after "Running"
2. **Treppe**: Stair climbing activities
3. **Rest**: Idle resting activities

## 📚 Additional Examples

### Creating JSONL Files

```bash
python strava/example_stream_jsonl.py
```

Options:
- Option 1: Sample streams from a single activity
- Option 2: Create JSONL object for a single activity
- Option 3: Create JSONL file from multiple activities
- Option 4: Create JSONL file for all person's activities (recommended)

### Analyzing CSV Files

You can also analyze CSV files directly:

```bash
python analysis/example_chatgpt_analysis.py
# Choose option 1: Analyze a CSV file
```

## 🔍 Troubleshooting

### Common Issues

1. **Import Errors**: Make sure you're running scripts from the project root directory, or adjust the paths in the sys.path.insert() calls.

2. **API Key Errors**: 
   - Verify your API keys are correct
   - Check that environment variables are set if using them
   - For DeepSeek, ensure the base_url is correct

3. **File Not Found**: 
   - Ensure JSONL files are in the `streams/` directory
   - Check that file paths use `os.path.join()` for cross-platform compatibility

4. **Strava API Errors (401 Unauthorized)**:
   - Your access token may have expired
   - Update your tokens using `strava/get_token.py`
   - The code will attempt automatic token refresh if you have a valid refresh token

