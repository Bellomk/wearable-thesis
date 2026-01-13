"""
Stream JSONL Processor
Functions for processing Strava activity streams into JSON/JSONL format.
"""

from typing import List, Dict, Optional, Any, Tuple, Callable
import json
import random
import numpy as np

# Constants
QUANTILE_LEVELS = [5, 25, 50, 75, 95]
CADENCE_MULTIPLIER = 2  # Strava cadence is for cycling, running cadence should be doubled


def _stream_key_for_quantiles(stream_type: str) -> str:
    """Convert Strava stream name to the corresponding quantile key."""
    mapping = {
        'heartrate': 'hr_bpm',
        'altitude': 'altitude_m',
        'distance': 'distance_m',
        'velocity_smooth': 'velocity_smooth_ms',
        'cadence': 'cadence_spm',
        'time': 'time_s'
    }
    return mapping.get(stream_type, stream_type)


def _is_running_activity(activity_name: Optional[str]) -> bool:
    """Return True if activity name indicates a running workout."""
    if not activity_name:
        return False
    return activity_name.strip().lower().startswith("running")


def _is_rest_activity(activity_name: Optional[str]) -> bool:
    """Return True if activity name indicates a rest activity."""
    if not activity_name:
        return False
    return activity_name.strip().lower().startswith("rest")


def _is_numeric_value(value: Any) -> bool:
    """Check if a value is numeric (int or float) and not None/empty."""
    return value is not None and value != "" and isinstance(value, (int, float))


def _extract_numeric_values(data: List[Any]) -> List[float]:
    """Extract numeric values from a list, filtering out None/empty values."""
    return [float(value) for value in data if _is_numeric_value(value)]


def _convert_streams_to_dict(streams_data: List[Dict]) -> Dict[str, List[Any]]:
    """Convert streams list to dictionary for easier access."""
    streams_dict = {}
    for stream in streams_data:
        stream_type = stream.get('type')
        stream_data = stream.get('data', [])
        if stream_type and stream_data:
            streams_dict[stream_type] = stream_data
    return streams_dict


def _filter_by_moving(streams_dict: Dict[str, List[Any]]) -> Dict[str, List[Any]]:
    """Filter streams to only include data points where athlete was moving."""
    moving_data = streams_dict.get('moving')
    if not isinstance(moving_data, list):
        return streams_dict
    
    # Check if moving stream has any meaningful values
    if not any(value not in (None, "") for value in moving_data):
        return streams_dict
    
    valid_indices = [idx for idx, value in enumerate(moving_data) if bool(value)]
    if not valid_indices:
        return {}
    
    def filter_data(data: List[Any]) -> List[Any]:
        return [data[i] for i in valid_indices if i < len(data)]
    
    filtered_streams = {
        stream_type: filter_data(data)
        for stream_type, data in streams_dict.items()
    }
    return filtered_streams


def _double_cadence_values(streams_dict: Dict[str, List[Any]]) -> None:
    """Double cadence values (Strava cadence is for cycling, running cadence should be doubled)."""
    if 'cadence' in streams_dict and isinstance(streams_dict['cadence'], list):
        streams_dict['cadence'] = [
            value * CADENCE_MULTIPLIER if _is_numeric_value(value) else value
            for value in streams_dict['cadence']
        ]


def _calculate_quantiles(streams_dict: Dict[str, List[Any]], 
                        include_velocity: bool) -> Dict[str, Dict[str, float]]:
    """Calculate quantiles for all numeric streams."""
    quantiles_result: Dict[str, Dict[str, float]] = {}
    
    for stream_type, data in streams_dict.items():
        if not isinstance(data, list) or not data:
            continue
        
        numeric_values = _extract_numeric_values(data)
        if not numeric_values:
            continue
        
        percentile_values = np.percentile(numeric_values, QUANTILE_LEVELS)
        key_name = _stream_key_for_quantiles(stream_type)
        
        # Skip velocity_smooth quantiles if we are not including velocity data
        if key_name == 'velocity_smooth_ms' and not include_velocity:
            continue
        
        quantiles_result[key_name] = {
            str(level): float(np.round(percentile_values[idx], 6))
            for idx, level in enumerate(QUANTILE_LEVELS)
        }
    
    return quantiles_result


def _calculate_pace_quantiles(time_data: List[float], 
                               distance_data: List[Any]) -> Optional[Dict[str, float]]:
    """Calculate pace quantiles from time and distance data."""
    raw_pace_values: List[float] = []
    
    for i in range(1, len(time_data)):
        dt = time_data[i] - time_data[i-1]
        if dt <= 0:
            continue
        
        if (i >= len(distance_data) or 
            distance_data[i] is None or 
            distance_data[i-1] is None):
            continue
        
        dd = distance_data[i] - distance_data[i-1]
        if dd <= 0:
            continue
        
        pace = (dt / dd) * 1000  # seconds per km
        raw_pace_values.append(pace)
    
    if not raw_pace_values:
        return None
    
    percentile_values = np.percentile(raw_pace_values, QUANTILE_LEVELS)
    return {
        str(level): float(np.round(percentile_values[idx], 6))
        for idx, level in enumerate(QUANTILE_LEVELS)
    }


def _find_sampling_indices(time_data: List[float], 
                          interval_seconds: float) -> List[int]:
    """Find indices in time_data that correspond to sampling intervals."""
    if not time_data:
        return []
    
    max_time = time_data[-1]
    target_times = []
    current_time = 0.0
    while current_time <= max_time:
        target_times.append(current_time)
        current_time += interval_seconds
    
    # Find closest index for each target time
    sampled_indices = []
    for target_time in target_times:
        closest_idx = min(
            range(len(time_data)),
            key=lambda i: abs(time_data[i] - target_time)
        )
        sampled_indices.append(closest_idx)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_indices = []
    for idx in sampled_indices:
        if idx not in seen:
            seen.add(idx)
            unique_indices.append(idx)
    
    return unique_indices


def _calculate_pace_values(sampled_time: List[float], 
                          sampled_distance: List[Optional[float]]) -> List[str]:
    """Calculate pace (seconds per km) for each sampled interval."""
    pace_values = []
    
    for i in range(len(sampled_time)):
        if i == 0:
            # First point: calculate from current to next point
            if (len(sampled_time) > 1 and 
                sampled_distance[0] is not None and 
                sampled_distance[1] is not None):
                dt = sampled_time[1] - sampled_time[0]
                dd = sampled_distance[1] - sampled_distance[0]
                if dd > 0 and dt > 0:
                    pace = (dt / dd) * 1000
                    pace_values.append(str(int(round(pace))))
                else:
                    pace_values.append("")
            else:
                pace_values.append("")
        else:
            # Calculate pace from previous point to current point
            dt = sampled_time[i] - sampled_time[i-1]
            if (sampled_distance[i] is not None and 
                sampled_distance[i-1] is not None):
                dd = sampled_distance[i] - sampled_distance[i-1]
                if dd > 0 and dt > 0:
                    pace = (dt / dd) * 1000
                    pace_values.append(str(int(round(pace))))
                else:
                    pace_values.append("")
            else:
                pace_values.append("")
    
    return pace_values


def _sample_stream_data(data: List[Any], indices: List[int]) -> List[Any]:
    """Sample data at specified indices."""
    return [
        data[i] if i < len(data) and data[i] is not None else None
        for i in indices
    ]


def _format_sampled_values(values: List[Any], 
                          format_func: Optional[Callable[[Any], str]] = None) -> str:
    """Format sampled values as CSV string."""
    if format_func is None:
        format_func = lambda v: str(int(round(v))) if v is not None else ""
    
    formatted = [format_func(v) if v is not None else "" for v in values]
    return ",".join(formatted)


def _sample_streams_common(streams_data: List[Dict],
                           interval_seconds: float,
                           filter_moving: bool,
                           include_pace: bool,
                           include_velocity: bool) -> Tuple[Dict[str, Any], Dict[str, Dict[str, Any]]]:
    """Shared sampling logic used by the public sampling helpers."""
    if not streams_data:
        return {}, {}
    
    # Convert streams list to dictionary
    streams_dict = _convert_streams_to_dict(streams_data)
    
    # Filter by moving if requested
    if filter_moving:
        streams_dict = _filter_by_moving(streams_dict)
        if not streams_dict:
            return {}, {}
    
    # Remove moving stream from output (used only for filtering)
    streams_dict.pop('moving', None)
    
    # Double cadence values for running
    _double_cadence_values(streams_dict)
    
    # Validate time stream exists
    if 'time' not in streams_dict or not streams_dict['time']:
        return {}, {}
    
    time_data = streams_dict['time']
    
    # Rebase time to start at zero
    time_offset = time_data[0] if time_data else 0
    time_data = [float(t) - float(time_offset) for t in time_data]
    streams_dict['time'] = time_data
    
    # Calculate quantiles
    quantiles_result = _calculate_quantiles(streams_dict, include_velocity)
    
    # Calculate pace quantiles if needed
    if include_pace and 'distance' in streams_dict:
        pace_quantiles = _calculate_pace_quantiles(
            time_data, 
            streams_dict['distance']
        )
        if pace_quantiles:
            quantiles_result['pace_s_per_km'] = pace_quantiles
    
    # Find sampling indices
    unique_indices = _find_sampling_indices(time_data, interval_seconds)
    if not unique_indices:
        return {}, {}
    
    # Sample time data
    sampled_time = [time_data[i] for i in unique_indices]
    
    # Build result dictionary
    result = {
        "sampling": f"approx_{int(interval_seconds)}s",
        "time_s_csv": ",".join(str(int(round(t))) for t in sampled_time)
    }
    
    # Add pace if requested
    if include_pace and 'distance' in streams_dict:
        sampled_distance = _sample_stream_data(
            streams_dict['distance'], 
            unique_indices
        )
        pace_values = _calculate_pace_values(sampled_time, sampled_distance)
        result["pace_s_per_km_csv"] = ",".join(pace_values)
    
    # Add heart rate
    if 'heartrate' in streams_dict:
        sampled_hr = _sample_stream_data(streams_dict['heartrate'], unique_indices)
        result["hr_bpm_csv"] = _format_sampled_values(sampled_hr)
    
    # Add altitude
    if 'altitude' in streams_dict:
        sampled_alt = _sample_stream_data(streams_dict['altitude'], unique_indices)
        result["alt_m_csv"] = _format_sampled_values(sampled_alt)
    
    # Add velocity_smooth
    if include_velocity and 'velocity_smooth' in streams_dict:
        sampled_velocity = _sample_stream_data(
            streams_dict['velocity_smooth'], 
            unique_indices
        )
        result["velocity_smooth_ms_csv"] = _format_sampled_values(
            sampled_velocity, 
            format_func=lambda v: f"{float(v):.2f}" if v is not None else ""
        )
    
    # Add cadence
    if 'cadence' in streams_dict:
        sampled_cadence = _sample_stream_data(streams_dict['cadence'], unique_indices)
        result["cadence_spm_csv"] = _format_sampled_values(sampled_cadence)
    
    return result, quantiles_result


def sample_streams_at_intervals(streams_data: List[Dict],
                                interval_seconds: float = 5.0) -> Tuple[Dict[str, str], Dict[str, Dict[str, Any]]]:
    """
    Sample activity streams at regular intervals and return compact CSV format.

    Takes the output of StravaAPI.get_activity_streams() and samples data at
    specified intervals (default: 5 seconds), then formats as CSV strings. If
    the 'moving' stream is available, samples are limited to data points where
    the athlete was moving. The resulting compact object can include time,
    distance, pace, heart rate, altitude, velocity_smooth, and cadence series.

    Args:
        streams_data: List of stream dictionaries from get_activity_streams()
                     Format: [{'type': 'time', 'data': [0, 1, 2, ...]}, ...]
        interval_seconds: Sampling interval in seconds (default: 5.0)

    Returns:
        Dictionary with compact CSV format:
        {
            "sampling": "approx_5s",
            "time_s_csv": "0,5,10,15,...",
            "pace_s_per_km_csv": "395,392,389,...",
            "hr_bpm_csv": "140,142,145,...",
            "alt_m_csv": "18,18,19,...",
            "velocity_smooth_ms_csv": "3.2,3.4,3.5,...",
            "cadence_spm_csv": "160,162,164,..."
        }
    """
    return _sample_streams_common(
        streams_data=streams_data,
        interval_seconds=interval_seconds,
        filter_moving=True,
        include_pace=True,
        include_velocity=True
    )


def sample_streams_without_moving_filter(streams_data: List[Dict],
                                         interval_seconds: float = 5.0) -> Tuple[Dict[str, str], Dict[str, Dict[str, Any]]]:
    """
    Sample activity streams at regular intervals without using the 'moving' stream.

    This helper is useful for activities where the athlete might be stationary
    (e.g., stair climbs, rest/meditation sessions) but we still want consistent
    sampling of the time series data. The output excludes pace and velocity
    fields, providing only the core sensor streams.

    Args:
        streams_data: List of stream dictionaries from get_activity_streams()
        interval_seconds: Sampling interval in seconds (default: 5.0)

    Returns:
        Dictionary with compact CSV format similar to sample_streams_at_intervals
        but without pace or velocity fields.
    """
    return _sample_streams_common(
        streams_data=streams_data,
        interval_seconds=interval_seconds,
        filter_moving=False,
        include_pace=False,
        include_velocity=False
    )


def create_streams_compact_json(streams_data: List[Dict],
                                interval_seconds: float = 5.0,
                                activity_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Create a complete JSON object with compact stream format.

    Args:
        streams_data: List of stream dictionaries from get_activity_streams()
        interval_seconds: Sampling interval in seconds (default: 5.0)
        activity_name: Optional activity name to determine if it's a running activity

    Returns:
        Dictionary with "streams_compact" and "quantiles" keys containing sampled data
    """
    is_running = _is_running_activity(activity_name)
    is_rest = _is_rest_activity(activity_name)

    compact_streams, quantiles = _sample_streams_common(
        streams_data=streams_data,
        interval_seconds=interval_seconds,
        filter_moving=is_running,
        include_pace=is_running,
        include_velocity=is_running
    )

    # For non-running activities, remove distance quantiles
    if not is_running and quantiles:
        quantiles.pop("distance_m", None)

    # For Rest activities, remove altitude data from compact streams and quantiles
    if is_rest:
        if compact_streams:
            compact_streams.pop("alt_m_csv", None)
        if quantiles:
            quantiles.pop("altitude_m", None)

    return {
        "streams_compact": compact_streams,
        "quantiles": quantiles
    }


def create_activity_jsonl_object(activity_data: Dict,
                                 streams_data: Optional[List[Dict]] = None,
                                 interval_seconds: float = 5.0) -> Dict[str, Any]:
    """
    Create a complete JSONL object for an activity with optional stream data.

    Args:
        activity_data: Activity details dictionary (from get_activity_details or activity list)
        streams_data: Optional streams data (from get_activity_streams())
        interval_seconds: Sampling interval for streams (default: 5.0)

    Returns:
        Complete JSONL object with activity metadata and compact streams
    """
    jsonl_obj = {
        "activity_id": activity_data.get('id'),
        "name": activity_data.get('name'),
        "type": activity_data.get('type'),
        "start_date": activity_data.get('start_date'),
        "distance_m": activity_data.get('distance'),
        "moving_time_s": activity_data.get('moving_time'),
        "elapsed_time_s": activity_data.get('elapsed_time'),
        "total_elevation_gain_m": activity_data.get('total_elevation_gain'),
        "average_speed_ms": activity_data.get('average_speed'),
        "max_speed_ms": activity_data.get('max_speed'),
        "average_heartrate_bpm": activity_data.get('average_heartrate'),
        "max_heartrate_bpm": activity_data.get('max_heartrate'),
        "calories": activity_data.get('calories'),
    }

    # Add compact streams if provided
    if streams_data:
        activity_name = activity_data.get('name')
        is_running = _is_running_activity(activity_name)
        is_rest = _is_rest_activity(activity_name)

        compact_streams, quantiles = _sample_streams_common(
            streams_data=streams_data,
            interval_seconds=interval_seconds,
            filter_moving=is_running,
            include_pace=is_running,
            include_velocity=is_running
        )

        # For non-running activities, remove distance quantiles
        if not is_running and quantiles:
            quantiles.pop("distance_m", None)

        # For Rest activities, remove altitude data from compact streams and quantiles
        if is_rest:
            if compact_streams:
                compact_streams.pop("alt_m_csv", None)
            if quantiles:
                quantiles.pop("altitude_m", None)

        if compact_streams:
            jsonl_obj["streams_compact"] = compact_streams
        if quantiles:
            jsonl_obj["quantiles"] = quantiles

    # Remove None values
    jsonl_obj = {k: v for k, v in jsonl_obj.items() if v is not None}

    return jsonl_obj


def save_jsonl_file(jsonl_objects: List[Dict[str, Any]],
                   filepath: str) -> None:
    """
    Save a list of JSON objects to a JSONL file (one JSON object per line).

    Args:
        jsonl_objects: List of dictionaries to save
        filepath: Path to output JSONL file
    """
    with open(filepath, 'w', encoding='utf-8') as f:
        for obj in jsonl_objects:
            json_line = json.dumps(obj, ensure_ascii=False)
            f.write(json_line + '\n')


def load_jsonl_file(filepath: str) -> List[Dict[str, Any]]:
    """
    Load JSONL file and return list of JSON objects.

    Args:
        filepath: Path to JSONL file

    Returns:
        List of dictionaries
    """
    jsonl_objects = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                jsonl_objects.append(json.loads(line))
    return jsonl_objects


def combine_activities_to_jsonl(activities: List[Dict],
                                streams_dict: Optional[Dict[int, List[Dict]]] = None,
                                interval_seconds: float = 5.0) -> List[Dict[str, Any]]:
    """
    Combine multiple activities into a list of JSONL objects.

    Args:
        activities: List of activity dictionaries
        streams_dict: Optional dictionary mapping activity_id to streams data
        interval_seconds: Sampling interval for streams (default: 5.0)

    Returns:
        List of JSONL objects ready to be saved
    """
    jsonl_objects = []

    for activity in activities:
        activity_id = activity.get('id')
        streams_data = streams_dict.get(activity_id) if streams_dict else None

        jsonl_obj = create_activity_jsonl_object(
            activity_data=activity,
            streams_data=streams_data,
            interval_seconds=interval_seconds
        )

        jsonl_objects.append(jsonl_obj)

    return jsonl_objects


def modify_heartrate_to_abnormal(jsonl_filepath: str, output_filepath: str,
                                  min_hr: int = 210, max_hr: int = 240) -> None:
    """
    Modify heartrate values in a JSONL file to abnormally high values.
    
    This function reads a JSONL file, replaces all heartrate values with random
    values in the specified range (default: 210-240 bpm), and saves the modified
    data to a new file. The function updates:
    - streams_compact.hr_bpm_csv (comma-separated heartrate values)
    - quantiles.hr_bpm (if present, recalculated from new values)
    - average_heartrate_bpm (if present, recalculated from new values)
    - max_heartrate_bpm (if present, set to max_hr)
    
    Args:
        jsonl_filepath: Path to input JSONL file
        output_filepath: Path to output JSONL file (modified data)
        min_hr: Minimum heartrate value for abnormal range (default: 210)
        max_hr: Maximum heartrate value for abnormal range (default: 240)
    
    Raises:
        FileNotFoundError: If input file doesn't exist
        ValueError: If min_hr >= max_hr
    """
    if min_hr >= max_hr:
        raise ValueError(f"min_hr ({min_hr}) must be less than max_hr ({max_hr})")
    
    modified_objects = []
    
    try:
        with open(jsonl_filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                obj = json.loads(line)
                modified_obj = obj.copy()
                
                # Modify streams_compact.hr_bpm_csv if present
                if 'streams_compact' in modified_obj and 'hr_bpm_csv' in modified_obj['streams_compact']:
                    hr_csv = modified_obj['streams_compact']['hr_bpm_csv']
                    
                    # Parse CSV string, replace each value with random abnormal value
                    if hr_csv:
                        hr_values = [val.strip() for val in hr_csv.split(',') if val.strip()]
                        # Replace each value with a random value in the abnormal range
                        new_hr_values = [str(random.randint(min_hr, max_hr)) for _ in hr_values]
                        modified_obj['streams_compact']['hr_bpm_csv'] = ','.join(new_hr_values)
                        
                        # Recalculate quantiles from new values
                        numeric_hr = [int(val) for val in new_hr_values]
                        if numeric_hr:
                            percentile_values = np.percentile(numeric_hr, QUANTILE_LEVELS)
                            
                            # Update or create quantiles.hr_bpm
                            if 'quantiles' not in modified_obj:
                                modified_obj['quantiles'] = {}
                            
                            modified_obj['quantiles']['hr_bpm'] = {
                                str(level): float(np.round(percentile_values[idx], 6))
                                for idx, level in enumerate(QUANTILE_LEVELS)
                            }
                            
                            # Update average_heartrate_bpm and max_heartrate_bpm
                            avg_hr = int(np.mean(numeric_hr))
                            max_hr_value = max(numeric_hr)
                            
                            if 'average_heartrate_bpm' in modified_obj:
                                modified_obj['average_heartrate_bpm'] = avg_hr
                            if 'max_heartrate_bpm' in modified_obj:
                                modified_obj['max_heartrate_bpm'] = max_hr_value
                
                modified_objects.append(modified_obj)
    except FileNotFoundError:
        raise FileNotFoundError(f"Input file not found: {jsonl_filepath}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in file {jsonl_filepath}: {e}")
    
    # Save modified objects to new file
    save_jsonl_file(modified_objects, output_filepath)
    print(f"Modified {len(modified_objects)} activities. Saved to: {output_filepath}")
