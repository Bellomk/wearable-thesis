"""
ChatGPT Connector
A Python class to connect to OpenAI's ChatGPT API, send files/data and prompts,
and receive responses.
"""

import os
from typing import Optional, List, Dict, Any
from openai import OpenAI
import pandas as pd
import json


class ChatGPTConnector:
    """Class to handle interactions with ChatGPT API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize ChatGPT connector.
        
        Args:
            api_key: OpenAI API key. If not provided, will try to get from environment variable OPENAI_API_KEY
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        
        if not self.api_key:
            raise ValueError(
                "OpenAI API key is required. Either pass it as an argument or set OPENAI_API_KEY environment variable."
            )
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = "gpt-4o"  # Can be changed to gpt-4o-mini, gpt-4-turbo, etc.
    
    def send_prompt(self, prompt: str, system_message: Optional[str] = None) -> str:
        """
        Send a simple text prompt to ChatGPT.
        
        Args:
            prompt: The user prompt to send
            system_message: Optional system message to set context
        
        Returns:
            ChatGPT's response as a string
        """
        messages = []
        
        if system_message:
            messages.append({"role": "system", "content": system_message})
        
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error sending prompt to ChatGPT: {e}")
            return None
    
    def send_file_with_prompt(self, file_path: str, prompt: str, 
                             system_message: Optional[str] = None) -> str:
        """
        Send a file along with a prompt to ChatGPT.
        Reads the file content and includes it in the prompt.
        
        Args:
            file_path: Path to the file to send
            prompt: The prompt/question about the file
            system_message: Optional system message to set context
        
        Returns:
            ChatGPT's response as a string
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
            
            # Send to ChatGPT
            return self.send_prompt(full_prompt, system_message)
            
        except Exception as e:
            print(f"Error reading or sending file: {e}")
            return None
    
    def send_dataframe_with_prompt(self, df: pd.DataFrame, prompt: str,
                                   system_message: Optional[str] = None,
                                   include_full_data: bool = False) -> str:
        """
        Send a pandas DataFrame along with a prompt to ChatGPT.
        
        Args:
            df: The pandas DataFrame to send
            prompt: The prompt/question about the data
            system_message: Optional system message to set context
            include_full_data: If True, sends entire DataFrame. If False, sends summary + first 10 rows
        
        Returns:
            ChatGPT's response as a string
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
            
            # Send to ChatGPT
            return self.send_prompt(full_prompt, system_message)
            
        except Exception as e:
            print(f"Error sending DataFrame: {e}")
            return None
    
    def send_dict_with_prompt(self, data: Dict[str, Any], prompt: str,
                             system_message: Optional[str] = None) -> str:
        """
        Send a dictionary (like activity details) along with a prompt to ChatGPT.
        
        Args:
            data: Dictionary containing data to send
            prompt: The prompt/question about the data
            system_message: Optional system message to set context
        
        Returns:
            ChatGPT's response as a string
        """
        try:
            # Format dictionary as JSON
            data_content = "Data:\n\n"
            data_content += json.dumps(data, indent=2, default=str)
            
            # Combine data with prompt
            full_prompt = f"{data_content}\n\n{'='*50}\n\n{prompt}"
            
            # Send to ChatGPT
            return self.send_prompt(full_prompt, system_message)
            
        except Exception as e:
            print(f"Error sending dictionary: {e}")
            return None
    
    def set_model(self, model: str):
        """
        Change the ChatGPT model to use.
        
        Args:
            model: Model name (e.g., 'gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo')
        """
        self.model = model
        print(f"Model changed to: {model}")
    
    def create_conversation(self, messages: List[Dict[str, str]]) -> str:
        """
        Send a multi-turn conversation to ChatGPT.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
                     Example: [
                         {"role": "system", "content": "You are a helpful assistant."},
                         {"role": "user", "content": "Hello!"},
                         {"role": "assistant", "content": "Hi! How can I help?"},
                         {"role": "user", "content": "Tell me about running."}
                     ]
        
        Returns:
            ChatGPT's response as a string
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error in conversation: {e}")
            return None


# Example usage functions
def analyze_strava_activity(file_path: str, api_key: Optional[str] = None) -> str:
    """
    Example function to analyze a Strava activity CSV file.
    
    Args:
        file_path: Path to the CSV file containing Strava data
        api_key: Optional OpenAI API key
    
    Returns:
        Analysis from ChatGPT
    """
    connector = ChatGPTConnector(api_key)
    
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
    Example function to analyze a Strava DataFrame.
    
    Args:
        df: DataFrame containing Strava activity data
        api_key: Optional OpenAI API key
    
    Returns:
        Analysis from ChatGPT
    """
    connector = ChatGPTConnector(api_key)
    
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
    print("ChatGPT Connector initialized.")
    print("\nExample usage:")
    print("1. connector = ChatGPTConnector(api_key='your-api-key')")
    print("2. response = connector.send_file_with_prompt('data.csv', 'Analyze this data')")
    print("3. print(response)")

