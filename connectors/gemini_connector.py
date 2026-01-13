"""
Gemini AI Connector
A Python class to connect to Google's Gemini API, send files/data and prompts,
and receive responses.
"""

import os
from typing import Optional, List, Dict, Any
import google.generativeai as genai
import pandas as pd
import json


class GeminiConnector:
    """Class to handle interactions with Google Gemini API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini connector.
        
        Args:
            api_key: Google API key. If not provided, will try to get from environment variable GEMINI_API_KEY
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        
        if not self.api_key:
            raise ValueError(
                "Gemini API key is required. Either pass it as an argument or set GEMINI_API_KEY environment variable."
            )
        
        genai.configure(api_key=self.api_key)
        self.model_name = "gemini-1.5-flash"  # Can be changed to gemini-1.5-pro, gemini-1.0-pro, etc.
        self.model = genai.GenerativeModel(self.model_name)
    
    def send_prompt(self, prompt: str, system_message: Optional[str] = None) -> str:
        """
        Send a simple text prompt to Gemini.
        
        Args:
            prompt: The user prompt to send
            system_message: Optional system message to set context
        
        Returns:
            Gemini's response as a string
        """
        try:
            # Combine system message and prompt if system message provided
            if system_message:
                full_prompt = f"{system_message}\n\n{prompt}"
            else:
                full_prompt = prompt
            
            response = self.model.generate_content(full_prompt)
            
            return response.text
            
        except Exception as e:
            print(f"Error sending prompt to Gemini: {e}")
            return None
    
    def send_file_with_prompt(self, file_path: str, prompt: str, 
                             system_message: Optional[str] = None) -> str:
        """
        Send a file along with a prompt to Gemini.
        Reads the file content and includes it in the prompt.
        
        Args:
            file_path: Path to the file to send
            prompt: The prompt/question about the file
            system_message: Optional system message to set context
        
        Returns:
            Gemini's response as a string
        """
        try:
            # Read file content based on file type
            if file_path.endswith('.csv'):
                # For CSV files, read and convert to a formatted string
                df = pd.read_csv(file_path)
                file_content = f"CSV File: {file_path}\n\n"
                file_content += f"Shape: {df.shape[0]} rows, {df.shape[1]} columns\n\n"
                file_content += f"Columns: {', '.join(df.columns.tolist())}\n\n"
                file_content += "First 10 rows:\n"
                file_content += df.head(10).to_string(index=False)
                
                # Add summary statistics if numeric columns exist
                numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                if numeric_cols:
                    file_content += "\n\nSummary Statistics:\n"
                    file_content += df[numeric_cols].describe().to_string()
            
            elif file_path.endswith('.json'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                    file_content = f"JSON File: {file_path}\n\n"
                    file_content += json.dumps(json_data, indent=2)
            
            else:
                # For other text files, read as plain text
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_content = f"File: {file_path}\n\n"
                    file_content += f.read()
            
            # Combine file content with prompt
            full_prompt = f"{file_content}\n\n{'='*50}\n\n{prompt}"
            
            # Send to Gemini
            return self.send_prompt(full_prompt, system_message)
            
        except Exception as e:
            print(f"Error reading or sending file: {e}")
            return None
    
    def send_dataframe_with_prompt(self, df: pd.DataFrame, prompt: str,
                                   system_message: Optional[str] = None,
                                   include_full_data: bool = False) -> str:
        """
        Send a pandas DataFrame along with a prompt to Gemini.
        
        Args:
            df: The pandas DataFrame to send
            prompt: The prompt/question about the data
            system_message: Optional system message to set context
            include_full_data: If True, sends entire DataFrame. If False, sends summary + first 10 rows
        
        Returns:
            Gemini's response as a string
        """
        try:
            # Format DataFrame information
            data_content = f"DataFrame Information:\n\n"
            data_content += f"Shape: {df.shape[0]} rows, {df.shape[1]} columns\n\n"
            data_content += f"Columns: {', '.join(df.columns.tolist())}\n\n"
            
            if include_full_data:
                data_content += "Full Data:\n"
                data_content += df.to_string(index=False)
            else:
                data_content += "First 10 rows:\n"
                data_content += df.head(10).to_string(index=False)
            
            # Add summary statistics if numeric columns exist
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            if numeric_cols:
                data_content += "\n\nSummary Statistics:\n"
                data_content += df[numeric_cols].describe().to_string()
            
            # Combine data with prompt
            full_prompt = f"{data_content}\n\n{'='*50}\n\n{prompt}"
            
            # Send to Gemini
            return self.send_prompt(full_prompt, system_message)
            
        except Exception as e:
            print(f"Error sending DataFrame: {e}")
            return None
    
    def send_dict_with_prompt(self, data: Dict[str, Any], prompt: str,
                             system_message: Optional[str] = None) -> str:
        """
        Send a dictionary (like activity details) along with a prompt to Gemini.
        
        Args:
            data: Dictionary containing data to send
            prompt: The prompt/question about the data
            system_message: Optional system message to set context
        
        Returns:
            Gemini's response as a string
        """
        try:
            # Format dictionary as JSON
            data_content = "Data:\n\n"
            data_content += json.dumps(data, indent=2, default=str)
            
            # Combine data with prompt
            full_prompt = f"{data_content}\n\n{'='*50}\n\n{prompt}"
            
            # Send to Gemini
            return self.send_prompt(full_prompt, system_message)
            
        except Exception as e:
            print(f"Error sending dictionary: {e}")
            return None
    
    def set_model(self, model_name: str):
        """
        Change the Gemini model to use.
        
        Args:
            model_name: Model name (e.g., 'gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-1.0-pro')
        """
        self.model_name = model_name
        self.model = genai.GenerativeModel(model_name)
        print(f"Model changed to: {model_name}")
    
    def create_conversation(self, messages: List[Dict[str, str]]) -> str:
        """
        Send a multi-turn conversation to Gemini.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
                     Example: [
                         {"role": "system", "content": "You are a helpful assistant."},
                         {"role": "user", "content": "Hello!"},
                         {"role": "assistant", "content": "Hi! How can I help?"},
                         {"role": "user", "content": "Tell me about running."}
                     ]
        
        Returns:
            Gemini's response as a string
        """
        try:
            # Start a chat session
            chat = self.model.start_chat(history=[])
            
            # Build conversation history
            # Gemini uses 'user' and 'model' roles
            system_msg = None
            conversation_history = []
            
            for msg in messages:
                role = msg.get('role')
                content = msg.get('content')
                
                if role == 'system':
                    system_msg = content
                elif role == 'user':
                    conversation_history.append({'role': 'user', 'parts': [content]})
                elif role == 'assistant':
                    conversation_history.append({'role': 'model', 'parts': [content]})
            
            # Restart chat with history
            if conversation_history:
                chat = self.model.start_chat(history=conversation_history[:-1])
                
                # Get the last user message
                last_message = conversation_history[-1]['parts'][0] if conversation_history else ""
                
                # Prepend system message if exists
                if system_msg:
                    last_message = f"{system_msg}\n\n{last_message}"
                
                response = chat.send_message(last_message)
            else:
                # No history, just send the prompt
                last_msg = messages[-1]['content'] if messages else ""
                if system_msg:
                    last_msg = f"{system_msg}\n\n{last_msg}"
                response = self.model.generate_content(last_msg)
            
            return response.text
            
        except Exception as e:
            print(f"Error in conversation: {e}")
            return None


# Example usage functions
def analyze_strava_activity(file_path: str, api_key: Optional[str] = None) -> str:
    """
    Example function to analyze a Strava activity CSV file with Gemini.
    
    Args:
        file_path: Path to the CSV file containing Strava data
        api_key: Optional Gemini API key
    
    Returns:
        Analysis from Gemini
    """
    connector = GeminiConnector(api_key)
    
    system_message = """You are a sports scientist and running coach expert. 
    Analyze the provided Strava activity data and provide insights about the athlete's fitness, 
    performance, and training recommendations."""
    
    prompt = """Please analyze this Strava running activity data and provide:

1. **Activity Summary**: Key metrics (distance, time, pace, elevation, heart rate if available)
2. **Performance Assessment**: Evaluate the athlete's performance level
3. **Aerobic Efficiency**: Analyze the relationship between pace and heart rate
4. **Intensity Analysis**: Estimate time spent in different heart rate zones
5. **Fitness Level**: Provide a fitness grade (A-F) with justification
6. **Recommendations**: Provide 3 specific training recommendations for improvement

Please be specific, data-driven, and provide actionable insights."""
    
    response = connector.send_file_with_prompt(file_path, prompt, system_message)
    return response


def analyze_strava_dataframe(df: pd.DataFrame, api_key: Optional[str] = None) -> str:
    """
    Example function to analyze a Strava DataFrame with Gemini.
    
    Args:
        df: DataFrame containing Strava activity data
        api_key: Optional Gemini API key
    
    Returns:
        Analysis from Gemini
    """
    connector = GeminiConnector(api_key)
    
    system_message = """You are a sports scientist and data analyst. 
    Analyze the provided activity data and provide insights about training patterns and performance."""
    
    prompt = """Please analyze this activity data and provide:

1. **Training Volume**: Total activities, distance, and time
2. **Training Consistency**: Pattern analysis and frequency
3. **Performance Trends**: Any improvements or changes over time
4. **Key Insights**: Notable patterns or observations
5. **Recommendations**: Suggestions for training optimization

Be specific and data-driven in your analysis."""
    
    response = connector.send_dataframe_with_prompt(df, prompt, system_message)
    return response


if __name__ == "__main__":
    # Example usage
    print("Gemini AI Connector initialized.")
    print("\nExample usage:")
    print("1. connector = GeminiConnector(api_key='your-api-key')")
    print("2. response = connector.send_file_with_prompt('data.csv', 'Analyze this data')")
    print("3. print(response)")

