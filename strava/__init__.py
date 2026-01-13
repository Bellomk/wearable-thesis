"""
Strava API integration and data processing package.
"""

from .strava_data_puller import StravaAPI, StravaConfig, setup_strava_config
from .strava_data_processing import StravaDataProcessor
from .stream_jsonl_processor import (
    sample_streams_at_intervals,
    sample_streams_without_moving_filter,
    create_streams_compact_json,
    create_activity_jsonl_object,
    save_jsonl_file,
    load_jsonl_file,
    combine_activities_to_jsonl,
    modify_heartrate_to_abnormal
)

__all__ = [
    'StravaAPI',
    'StravaConfig',
    'setup_strava_config',
    'StravaDataProcessor',
    'sample_streams_at_intervals',
    'sample_streams_without_moving_filter',
    'create_streams_compact_json',
    'create_activity_jsonl_object',
    'save_jsonl_file',
    'load_jsonl_file',
    'combine_activities_to_jsonl',
    'modify_heartrate_to_abnormal'
]
