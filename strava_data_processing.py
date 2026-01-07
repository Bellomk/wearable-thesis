import pandas as pd
import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime


class StravaDataProcessor:
    """Class to process, filter, and analyze Strava data."""
    
    def __init__(self, data: Any):
        """
        Initialize with data returned by StravaAPI.
        This can be:
        - List[Dict]: activities list
        - Dict: single activity details
        - List[Dict]: streams array (list of stream dicts)
        """
        self.data = data
    
    def filter_running_activities(self, activities: Optional[List[Dict]] = None) -> List[Dict]:
        """Filter activities to only include runs."""
        source = activities if activities is not None else self.data or []
        running_types = ['Run', 'TrailRun', 'Treadmill']
        return [a for a in source if isinstance(a, dict) and a.get('type') in running_types]
    
    def get_activity_summary(self, df: pd.DataFrame) -> Dict:
        """Generate summary statistics for activities."""
        if df.empty:
            return {}
        summary = {
            'total_activities': len(df),
            'total_distance_km': df['distance'].sum(),
            'total_time_hours': df['moving_time'].sum() / 3600,
            'average_distance_km': df['distance'].mean(),
            'average_pace_min_per_km': (df['moving_time'] / 60 / df['distance']).mean(),
            'total_elevation_gain_m': df['total_elevation_gain'].sum(),
            'average_heartrate': df['average_heartrate'].mean() if 'average_heartrate' in df.columns else None,
            'date_range': {
                'first_activity': df['start_date'].min(),
                'last_activity': df['start_date'].max()
            }
        }
        return summary
    
    def streams_to_dataframe(self, streams_data: Optional[Dict] = None) -> pd.DataFrame:
        """Convert activity streams data to a pandas DataFrame."""
        source = streams_data if streams_data is not None else self.data
        if not source or not isinstance(source, list):
            return pd.DataFrame()
        stream_dict = {}
        for stream in source:
            stream_type = stream.get('type')
            data = stream.get('data', [])
            if stream_type and data:
                stream_dict[stream_type] = data
        if not stream_dict:
            return pd.DataFrame()
        max_length = max(len(data) for data in stream_dict.values())
        df_data = {}
        for stream_type, data in stream_dict.items():
            padded_data = data + [None] * (max_length - len(data))
            df_data[stream_type] = padded_data
        df = pd.DataFrame(df_data)
        # if 'distance' in df.columns:
        #     df['distance_km'] = df['distance'] / 1000
        return df

    def activities_to_dataframe(self, activities: Optional[List[Dict]] = None) -> pd.DataFrame:
        """Convert activities list to pandas DataFrame."""
        source = activities if activities is not None else self.data
        if not source:
            return pd.DataFrame()
        data_rows = []
        for activity in source:
            if not isinstance(activity, dict):
                continue
            row = {
                'id': activity.get('id'),
                'name': activity.get('name'),
                'type': activity.get('type'),
                'start_date': activity.get('start_date'),
                'distance': activity.get('distance', 0) / 1000,
                'moving_time': activity.get('moving_time', 0),
                'elapsed_time': activity.get('elapsed_time', 0),
                'total_elevation_gain': activity.get('total_elevation_gain', 0),
                'average_speed': activity.get('average_speed', 0) * 3.6,
                'max_speed': activity.get('max_speed', 0) * 3.6,
                'average_heartrate': activity.get('average_heartrate'),
                'max_heartrate': activity.get('max_heartrate'),
                'calories': activity.get('calories'),
                'kudos_count': activity.get('kudos_count', 0),
                'comment_count': activity.get('comment_count', 0),
                'achievement_count': activity.get('achievement_count', 0),
                'pr_count': activity.get('pr_count', 0),
                'suffer_score': activity.get('suffer_score'),
                'description': activity.get('description', ''),
                'gear_id': activity.get('gear_id'),
                'trainer': activity.get('trainer', False),
                'commute': activity.get('commute', False),
                'manual': activity.get('manual', False),
                'private': activity.get('private', False),
                'flagged': activity.get('flagged', False)
            }
            data_rows.append(row)
        df = pd.DataFrame(data_rows)
        if not df.empty:
            df['start_date'] = pd.to_datetime(df['start_date'])
            df['date'] = df['start_date'].dt.date
            df['time'] = df['start_date'].dt.time
        return df

    def activity_details_to_dataframe(self, activity_details: Optional[Dict] = None) -> pd.DataFrame:
        """Convert a single activity details object to a pandas DataFrame."""
        source = activity_details if activity_details is not None else self.data
        if not source or not isinstance(source, dict):
            return pd.DataFrame()
        row = {
            'id': source.get('id'),
            'name': source.get('name'),
            'type': source.get('type'),
            'start_date': source.get('start_date'),
            'start_date_local': source.get('start_date_local'),
            'timezone': source.get('timezone'),
            'utc_offset': source.get('utc_offset'),
            'distance': source.get('distance', 0) / 1000,
            'moving_time': source.get('moving_time', 0),
            'elapsed_time': source.get('elapsed_time', 0),
            'total_elevation_gain': source.get('total_elevation_gain', 0),
            'elev_high': source.get('elev_high', 0),
            'elev_low': source.get('elev_low', 0),
            'average_speed': source.get('average_speed', 0) * 3.6,
            'max_speed': source.get('max_speed', 0) * 3.6,
            'average_cadence': source.get('average_cadence'),
            'average_temp': source.get('average_temp'),
            'average_watts': source.get('average_watts'),
            'weighted_average_watts': source.get('weighted_average_watts'),
            'kilojoules': source.get('kilojoules'),
            'device_watts': source.get('device_watts', False),
            'has_heartrate': source.get('has_heartrate', False),
            'average_heartrate': source.get('average_heartrate'),
            'max_heartrate': source.get('max_heartrate'),
            'heartrate_opt_out': source.get('heartrate_opt_out', False),
            'display_hide_heartrate_option': source.get('display_hide_heartrate_option', False),
            'calories': source.get('calories'),
            'suffer_score': source.get('suffer_score'),
            'description': source.get('description', ''),
            'gear_id': source.get('gear_id'),
            'gear_name': source.get('gear', {}).get('name', '') if source.get('gear') else '',
            'gear_distance': source.get('gear', {}).get('distance', 0) / 1000 if source.get('gear') else 0,
            'trainer': source.get('trainer', False),
            'commute': source.get('commute', False),
            'manual': source.get('manual', False),
            'private': source.get('private', False),
            'flagged': source.get('flagged', False),
            'workout_type': source.get('workout_type'),
            'external_id': source.get('external_id', ''),
            'upload_id': source.get('upload_id'),
            'upload_id_str': source.get('upload_id_str', ''),
            'from_accepted_tag': source.get('from_accepted_tag', False),
            'kudos_count': source.get('kudos_count', 0),
            'comment_count': source.get('comment_count', 0),
            'athlete_count': source.get('athlete_count', 0),
            'photo_count': source.get('photo_count', 0),
            'achievement_count': source.get('achievement_count', 0),
            'pr_count': source.get('pr_count', 0),
            'total_photo_count': source.get('total_photo_count', 0),
            'has_kudoed': source.get('has_kudoed', False),
            'segment_efforts': len(source.get('segment_efforts', [])),
            'splits_metric': len(source.get('splits_metric', [])),
            'splits_standard': len(source.get('splits_standard', [])),
            'laps': len(source.get('laps', [])),
            'best_efforts': len(source.get('best_efforts', [])),
            'device_name': source.get('device_name', ''),
            'embed_token': source.get('embed_token', ''),
            'segment_leaderboard_opt_out': source.get('segment_leaderboard_opt_out', False),
            'leaderboard_opt_out': source.get('leaderboard_opt_out', False),
            'perceived_exertion': source.get('perceived_exertion'),
            'prefer_perceived_exertion': source.get('prefer_perceived_exertion', False),
            'photos': len(source.get('photos', {}).get('data', [])) if source.get('photos') else 0,
            'has_photos': source.get('has_photos', False),
            'instagram_primary_photo': source.get('instagram_primary_photo'),
            'instagram_hashtags': source.get('instagram_hashtags', []),
            'resource_state': source.get('resource_state'),
            'athlete_id': source.get('athlete', {}).get('id') if source.get('athlete') else None,
            'athlete_username': source.get('athlete', {}).get('username', '') if source.get('athlete') else '',
            'athlete_firstname': source.get('athlete', {}).get('firstname', '') if source.get('athlete') else '',
            'athlete_lastname': source.get('athlete', {}).get('lastname', '') if source.get('athlete') else '',
            'athlete_city': source.get('athlete', {}).get('city', '') if source.get('athlete') else '',
            'athlete_state': source.get('athlete', {}).get('state', '') if source.get('athlete') else '',
            'athlete_country': source.get('athlete', {}).get('country', '') if source.get('athlete') else '',
            'athlete_sex': source.get('athlete', {}).get('sex', '') if source.get('athlete') else '',
            'athlete_premium': source.get('athlete', {}).get('premium', False) if source.get('athlete') else False,
            'athlete_summit': source.get('athlete', {}).get('summit', False) if source.get('athlete') else False,
            'athlete_created_at': source.get('athlete', {}).get('created_at', '') if source.get('athlete') else '',
            'athlete_updated_at': source.get('athlete', {}).get('updated_at', '') if source.get('athlete') else '',
            'athlete_badge_type_id': source.get('athlete', {}).get('badge_type_id') if source.get('athlete') else None,
            'athlete_weight': source.get('athlete', {}).get('weight') if source.get('athlete') else None,
            'athlete_profile_medium': source.get('athlete', {}).get('profile_medium', '') if source.get('athlete') else '',
            'athlete_profile': source.get('athlete', {}).get('profile', '') if source.get('athlete') else '',
            'athlete_friend': source.get('athlete', {}).get('friend') if source.get('athlete') else None,
            'athlete_follower': source.get('athlete', {}).get('follower') if source.get('athlete') else None,
            'athlete_follower_count': source.get('athlete', {}).get('follower_count') if source.get('athlete') else None,
            'athlete_friend_count': source.get('athlete', {}).get('friend_count') if source.get('athlete') else None,
            'athlete_mutual_friend_count': source.get('athlete', {}).get('mutual_friend_count') if source.get('athlete') else None,
            'athlete_athlete_type': source.get('athlete', {}).get('athlete_type') if source.get('athlete') else None,
            'athlete_date_preference': source.get('athlete', {}).get('date_preference', '') if source.get('athlete') else '',
            'athlete_measurement_preference': source.get('athlete', {}).get('measurement_preference', '') if source.get('athlete') else '',
            'athlete_clubs': len(source.get('athlete', {}).get('clubs', [])) if source.get('athlete') else 0,
            'athlete_ftp': source.get('athlete', {}).get('ftp') if source.get('athlete') else None,
            'athlete_bikes': len(source.get('athlete', {}).get('bikes', [])) if source.get('athlete') else 0,
            'athlete_shoes': len(source.get('athlete', {}).get('shoes', [])) if source.get('athlete') else 0
        }
        df = pd.DataFrame([row])
        if not df.empty:
            df['start_date'] = pd.to_datetime(df['start_date'])
            df['start_date_local'] = pd.to_datetime(df['start_date_local'])
            df['date'] = df['start_date'].dt.date
            df['time'] = df['start_date'].dt.time
            df['date_local'] = df['start_date_local'].dt.date
            df['time_local'] = df['start_date_local'].dt.time
        return df
    
    def process_multiple_activity_streams(self, activity_streams_dict: Dict[int, Dict]) -> Dict[int, pd.DataFrame]:
        """
        Process multiple activity streams into DataFrames.
        
        Args:
            activity_streams_dict: Dictionary from get_person_activity_streams()
                                  Format: {activity_id: {'streams': stream_data, ...}, ...}
        
        Returns:
            Dictionary mapping activity_id to DataFrame
            Format: {activity_id: DataFrame, ...}
        """
        processed_streams = {}
        
        for activity_id, activity_data in activity_streams_dict.items():
            streams = activity_data.get('streams')
            
            if streams:
                df = self.streams_to_dataframe(streams)
                
                if not df.empty:
                    # Add metadata columns
                    df['activity_id'] = activity_id
                    df['activity_name'] = activity_data.get('activity_name', '')
                    df['activity_date'] = activity_data.get('activity_date', '')
                    
                    processed_streams[activity_id] = df
        
        return processed_streams
    
    def save_person_streams_to_files(self, activity_streams_dict: Dict[int, Dict], 
                                     person_initial: str, 
                                     output_dir: str = "streams") -> Dict[int, pd.DataFrame]:
        """
        Process and save person activity streams to individual CSV files.
        
        Args:
            activity_streams_dict: Dictionary from get_person_activity_streams()
            person_initial: Person's initial for file naming
            output_dir: Directory to save files (default: "streams")
        
        Returns:
            Dictionary mapping activity_id to DataFrame
        """
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Process streams
        processed_streams = self.process_multiple_activity_streams(activity_streams_dict)
        
        if not processed_streams:
            print("No streams to save")
            return {}
        
        # Save each activity's streams to a separate CSV
        print(f"\nSaving stream data to CSV files in '{output_dir}'...")
        for activity_id, df_streams in processed_streams.items():
            output_file = os.path.join(output_dir, f"streams_person_{person_initial}_activity_{activity_id}.csv")
            df_streams.to_csv(output_file, index=False)
            print(f"  ✓ Saved: {output_file} ({len(df_streams)} data points)")
        
        return processed_streams
    
    def create_streams_summary_json(self, activity_streams_dict: Dict[int, Dict],
                                   person_initial: str,
                                   output_dir: str = "streams") -> str:
        """
        Create and save a JSON summary of activity streams.
        
        Args:
            activity_streams_dict: Dictionary from get_person_activity_streams()
            person_initial: Person's initial for file naming
            output_dir: Directory to save file (default: "streams")
        
        Returns:
            Path to the saved summary file
        """
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Create summary data
        summary_data = {}
        for activity_id, activity_data in activity_streams_dict.items():
            summary_data[str(activity_id)] = {
                'activity_name': activity_data['activity_name'],
                'activity_date': activity_data['activity_date'],
                'distance_km': activity_data['distance']/1000 if activity_data['distance'] else 0,
                'moving_time_min': activity_data['moving_time']/60 if activity_data['moving_time'] else 0,
                'stream_types': [s.get('type') for s in activity_data['streams']] if activity_data['streams'] else []
            }
        
        # Save summary to JSON
        summary_file = os.path.join(output_dir, f"streams_summary_person_{person_initial}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2)
        
        print(f"\n✓ Summary saved to: {summary_file}")
        return summary_file
    
    def combine_person_streams(self, activity_streams_dict: Dict[int, Dict],
                              person_initial: str,
                              output_dir: str = "streams") -> Optional[pd.DataFrame]:
        """
        Combine all person activity streams into a single DataFrame and save to CSV.
        
        Args:
            activity_streams_dict: Dictionary from get_person_activity_streams()
            person_initial: Person's initial for file naming
            output_dir: Directory to save file (default: "streams")
        
        Returns:
            Combined DataFrame, or None if no streams to combine
        """
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Process streams
        processed_streams = self.process_multiple_activity_streams(activity_streams_dict)
        
        if not processed_streams:
            print("No streams to combine")
            return None
        
        # Combine all streams into one DataFrame
        all_streams_list = list(processed_streams.values())
        combined_df = pd.concat(all_streams_list, ignore_index=True)
        
        # Save combined DataFrame
        output_file = os.path.join(output_dir, f"combined_streams_person_{person_initial}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        combined_df.to_csv(output_file, index=False)
        
        print(f"\n✓ Combined streams saved to: {output_file}")
        print(f"  Total data points: {len(combined_df)}")
        print(f"  Activities included: {combined_df['activity_id'].nunique()}")
        print(f"  Columns: {list(combined_df.columns)}")
        
        return combined_df


