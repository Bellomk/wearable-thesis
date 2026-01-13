"""
DeepSeek Connector
A Python class to interact with DeepSeek LLM API similarly to ChatGPTConnector.
"""

import os
import json
from typing import Optional, List, Dict
from openai import OpenAI


class DeepSeekConnector:
    """A lightweight connector for the DeepSeek LLM API."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or os.getenv('DEEPSEEK_API_KEY')
        if not self.api_key:
            raise ValueError("DeepSeek API key is required. Set DEEPSEEK_API_KEY or pass api_key explicitly.")

        self.base_url = base_url or os.getenv('DEEPSEEK_BASE_URL') or 'https://llms.innkube.fim.uni-passau.de'
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    # ------------------------------------------------------------------
    # Internal helper for POST requests
    # ------------------------------------------------------------------
    def _post(self, payload: Dict) -> Dict:
        response = self.client.chat.completions.create(
            model=payload.get('model', 'deepseek-v31-4bit'),
            messages=payload['messages'],
            stream=payload.get('stream', False),
            temperature=payload.get('temperature', 0.7)
        )
        return response.model_dump()

    # ------------------------------------------------------------------
    # Simple prompt
    # ------------------------------------------------------------------
    def send_prompt(self, prompt: str, system_message: Optional[str] = None) -> str:
        messages: List[Dict[str, str]] = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "messages": messages,
            "stream": False
        }

        data = self._post(payload)
        return data.get('choices', [{}])[0].get('message', {}).get('content', '')

    # ------------------------------------------------------------------
    # Prompt with file (simulate by embedding file content)
    # ------------------------------------------------------------------
    def send_file_with_prompt(self, file_path: str, prompt: str, system_message: Optional[str] = None) -> str:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
        except Exception as exc:
            return f"Error reading file: {exc}"

        combined_prompt = f"File: {file_path}\n\n{file_content}\n\n{'='*60}\n\n{prompt}"
        return self.send_prompt(combined_prompt, system_message)

    # ------------------------------------------------------------------
    # Prompt with pandas DataFrame
    # ------------------------------------------------------------------
    def send_dataframe_with_prompt(self, df, prompt: str, system_message: Optional[str] = None,
                                   include_full_data: bool = False) -> str:
        info = [
            f"Shape: {df.shape[0]} rows, {df.shape[1]} columns",
            f"Columns: {', '.join(df.columns)}",
        ]

        if include_full_data:
            info.append("\nFull Data:\n" + df.to_string(index=False))
        else:
            info.append("\nFirst 10 rows:\n" + df.head(10).to_string(index=False))

        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            info.append("\nSummary Statistics:\n" + df[numeric_cols].describe().to_string())

        combined_prompt = "\n\n".join(info) + "\n\n" + ('=' * 60) + "\n\n" + prompt
        return self.send_prompt(combined_prompt, system_message)

    # ------------------------------------------------------------------
    # Prompt with dictionary
    # ------------------------------------------------------------------
    def send_dict_with_prompt(self, data: Dict, prompt: str, system_message: Optional[str] = None) -> str:
        data_json = json.dumps(data, indent=2, default=str)
        combined_prompt = f"Data:\n{data_json}\n\n{'='*60}\n\n{prompt}"
        return self.send_prompt(combined_prompt, system_message)

    # ------------------------------------------------------------------
    # Conversation
    # ------------------------------------------------------------------
    def create_conversation(self, messages: List[Dict[str, str]]) -> str:
        payload = {
            "messages": messages,
            "stream": False
        }
        data = self._post(payload)
        return data.get('choices', [{}])[0].get('message', {}).get('content', '')
