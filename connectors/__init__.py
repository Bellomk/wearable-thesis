"""
LLM connector package for ChatGPT, Gemini, and DeepSeek.
"""

from .chatgpt_connector import ChatGPTConnector, analyze_strava_activity, analyze_strava_dataframe
from .gemini_connector import GeminiConnector
from .deepseek_connector import DeepSeekConnector

__all__ = [
    'ChatGPTConnector',
    'analyze_strava_activity',
    'analyze_strava_dataframe',
    'GeminiConnector',
    'DeepSeekConnector'
]
