"""
Example analysis script for Strava running data.
This script demonstrates how to analyze the data retrieved from Strava.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import numpy as np


def load_strava_data(csv_file: str) -> pd.DataFrame:
    """Load Strava data from CSV file."""
    df = pd.read_csv(csv_file)
    df['start_date'] = pd.to_datetime(df['start_date'])
    df['date'] = pd.to_datetime(df['date'])
    return df


def analyze_running_trends(df: pd.DataFrame):
    """Analyze running trends over time."""
    print("=== RUNNING TRENDS ANALYSIS ===\n")
    
    # Monthly summary
    df['year_month'] = df['start_date'].dt.to_period('M')
    monthly_stats = df.groupby('year_month').agg({
        'distance': ['count', 'sum', 'mean'],
        'moving_time': 'sum',
        'average_speed': 'mean',
        'total_elevation_gain': 'sum'
    }).round(2)
    
    print("Monthly Running Statistics:")
    print(monthly_stats)
    print()
    
    # Weekly patterns
    df['day_of_week'] = df['start_date'].dt.day_name()
    df['weekday'] = df['start_date'].dt.dayofweek
    weekly_patterns = df.groupby('day_of_week').agg({
        'distance': ['count', 'mean'],
        'average_speed': 'mean'
    }).round(2)
    
    print("Running Patterns by Day of Week:")
    print(weekly_patterns)
    print()
    
    # Distance distribution
    print("Distance Distribution:")
    print(f"Short runs (< 5km): {len(df[df['distance'] < 5])} activities")
    print(f"Medium runs (5-15km): {len(df[(df['distance'] >= 5) & (df['distance'] < 15)])} activities")
    print(f"Long runs (15-30km): {len(df[(df['distance'] >= 15) & (df['distance'] < 30)])} activities")
    print(f"Very long runs (30km+): {len(df[df['distance'] >= 30])} activities")
    print()


def create_visualizations(df: pd.DataFrame):
    """Create visualizations of running data."""
    # Filter out invalid data (distance > 0, moving_time > 0)
    valid_df = df[(df['distance'] > 0) & (df['moving_time'] > 0)].copy()
    
    if len(valid_df) == 0:
        print("No valid data for visualization (all activities have zero distance or time).")
        return
    
    plt.style.use('seaborn-v0_8')
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('Strava Running Data Analysis', fontsize=16, fontweight='bold')
    
    # 1. Distance over time
    axes[0, 0].scatter(valid_df['start_date'], valid_df['distance'], alpha=0.6, s=20)
    axes[0, 0].set_title('Distance Over Time')
    axes[0, 0].set_xlabel('Date')
    axes[0, 0].set_ylabel('Distance (km)')
    axes[0, 0].tick_params(axis='x', rotation=45)
    
    # 2. Pace distribution
    pace_min_per_km = (valid_df['moving_time'] / 60) / valid_df['distance']
    # Remove any inf or NaN values
    pace_min_per_km = pace_min_per_km.replace([np.inf, -np.inf], np.nan).dropna()
    
    if len(pace_min_per_km) > 0:
        axes[0, 1].hist(pace_min_per_km, bins=30, alpha=0.7, edgecolor='black')
        axes[0, 1].set_title('Pace Distribution')
        axes[0, 1].set_xlabel('Pace (min/km)')
        axes[0, 1].set_ylabel('Frequency')
        if pace_min_per_km.mean() > 0 and np.isfinite(pace_min_per_km.mean()):
            axes[0, 1].axvline(pace_min_per_km.mean(), color='red', linestyle='--', 
                              label=f'Average: {pace_min_per_km.mean():.1f} min/km')
            axes[0, 1].legend()
    else:
        axes[0, 1].text(0.5, 0.5, 'No valid pace data', 
                       ha='center', va='center', transform=axes[0, 1].transAxes)
        axes[0, 1].set_title('Pace Distribution')
    
    # 3. Distance vs Pace
    if len(pace_min_per_km) > 0:
        valid_indices = pace_min_per_km.index
        axes[1, 0].scatter(valid_df.loc[valid_indices, 'distance'], pace_min_per_km, 
                          alpha=0.6, s=20)
        axes[1, 0].set_title('Distance vs Pace')
        axes[1, 0].set_xlabel('Distance (km)')
        axes[1, 0].set_ylabel('Pace (min/km)')
    else:
        axes[1, 0].text(0.5, 0.5, 'No valid pace data', 
                       ha='center', va='center', transform=axes[1, 0].transAxes)
        axes[1, 0].set_title('Distance vs Pace')
    
    # 4. Weekly running pattern
    valid_df['day_of_week'] = valid_df['start_date'].dt.day_name()
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    weekly_counts = valid_df['day_of_week'].value_counts().reindex(day_order)
    weekly_counts = weekly_counts.fillna(0)  # Fill missing days with 0
    axes[1, 1].bar(range(len(weekly_counts)), weekly_counts.values)
    axes[1, 1].set_title('Running Frequency by Day of Week')
    axes[1, 1].set_xlabel('Day of Week')
    axes[1, 1].set_ylabel('Number of Runs')
    axes[1, 1].set_xticks(range(len(day_order)))
    axes[1, 1].set_xticklabels(day_order, rotation=45)
    
    plt.tight_layout()
    # Save to project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_path = os.path.join(project_root, 'strava_running_analysis.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.show()


def find_personal_records(df: pd.DataFrame):
    """Find personal records and notable achievements."""
    print("=== PERSONAL RECORDS & ACHIEVEMENTS ===\n")
    
    # Longest run
    longest_run = df.loc[df['distance'].idxmax()]
    print(f"Longest Run: {longest_run['distance']:.2f} km on {longest_run['date']}")
    print(f"  Time: {longest_run['moving_time']/60:.1f} minutes")
    print(f"  Pace: {(longest_run['moving_time']/60)/longest_run['distance']:.2f} min/km")
    print()
    
    # Fastest average pace
    valid_pace_df = df[(df['distance'] > 0) & (df['moving_time'] > 0)].copy()
    if len(valid_pace_df) > 0:
        pace_min_per_km = (valid_pace_df['moving_time'] / 60) / valid_pace_df['distance']
        pace_min_per_km = pace_min_per_km.replace([np.inf, -np.inf], np.nan).dropna()
        if len(pace_min_per_km) > 0:
            fastest_pace_idx = pace_min_per_km.idxmin()
            fastest_run = valid_pace_df.loc[fastest_pace_idx]
            print(f"Fastest Pace: {(fastest_run['moving_time']/60)/fastest_run['distance']:.2f} min/km")
            print(f"  Distance: {fastest_run['distance']:.2f} km on {fastest_run['date']}")
            print()
    
    # Most elevation gain
    if df['total_elevation_gain'].max() > 0:
        most_elevation = df.loc[df['total_elevation_gain'].idxmax()]
        print(f"Most Elevation Gain: {most_elevation['total_elevation_gain']:.0f} m")
        print(f"  Distance: {most_elevation['distance']:.2f} km on {most_elevation['date']}")
        print()
    
    # Monthly totals
    df['year_month'] = df['start_date'].dt.to_period('M')
    monthly_distance = df.groupby('year_month')['distance'].sum()
    best_month = monthly_distance.idxmax()
    print(f"Best Month: {best_month} with {monthly_distance[best_month]:.2f} km")
    print()


def analyze_heart_rate_data(df: pd.DataFrame):
    """Analyze heart rate data if available."""
    if 'average_heartrate' in df.columns and df['average_heartrate'].notna().any():
        print("=== HEART RATE ANALYSIS ===\n")
        
        hr_data = df[df['average_heartrate'].notna()]
        if len(hr_data) > 0:
            print(f"Activities with heart rate data: {len(hr_data)}")
            print(f"Average heart rate: {hr_data['average_heartrate'].mean():.1f} bpm")
            print(f"Maximum heart rate: {hr_data['max_heartrate'].max():.1f} bpm")
            print(f"Minimum average heart rate: {hr_data['average_heartrate'].min():.1f} bpm")
            print()
            
            # Heart rate vs pace correlation
            valid_hr_data = hr_data[(hr_data['distance'] > 0) & (hr_data['moving_time'] > 0)].copy()
            if len(valid_hr_data) > 0:
                pace_min_per_km = (valid_hr_data['moving_time'] / 60) / valid_hr_data['distance']
                pace_min_per_km = pace_min_per_km.replace([np.inf, -np.inf], np.nan).dropna()
                if len(pace_min_per_km) > 0 and len(pace_min_per_km) == len(valid_hr_data.loc[pace_min_per_km.index]):
                    correlation = np.corrcoef(pace_min_per_km, valid_hr_data.loc[pace_min_per_km.index, 'average_heartrate'])[0, 1]
                    if np.isfinite(correlation):
                        print(f"Heart rate vs pace correlation: {correlation:.3f}")
                        print()
    else:
        print("No heart rate data available in the dataset.\n")


def generate_training_insights(df: pd.DataFrame):
    """Generate insights for training improvement."""
    print("=== TRAINING INSIGHTS ===\n")
    
    # Recent vs older performance
    valid_df = df[(df['distance'] > 0) & (df['moving_time'] > 0)].copy()
    if len(valid_df) == 0:
        print("No valid data for pace analysis.\n")
        return
    
    recent_cutoff = valid_df['start_date'].max() - timedelta(days=30)
    recent_runs = valid_df[valid_df['start_date'] >= recent_cutoff]
    older_runs = valid_df[valid_df['start_date'] < recent_cutoff]
    
    if len(recent_runs) > 0 and len(older_runs) > 0:
        recent_pace = (recent_runs['moving_time'] / 60) / recent_runs['distance']
        recent_pace = recent_pace.replace([np.inf, -np.inf], np.nan).dropna()
        older_pace = (older_runs['moving_time'] / 60) / older_runs['distance']
        older_pace = older_pace.replace([np.inf, -np.inf], np.nan).dropna()
        
        if len(recent_pace) > 0 and len(older_pace) > 0:
            recent_avg_pace = recent_pace.mean()
            older_avg_pace = older_pace.mean()
            
            if np.isfinite(recent_avg_pace) and np.isfinite(older_avg_pace):
                pace_improvement = older_avg_pace - recent_avg_pace
                print(f"Recent 30 days average pace: {recent_avg_pace:.2f} min/km")
                print(f"Previous period average pace: {older_avg_pace:.2f} min/km")
                if pace_improvement > 0:
                    print(f"Pace improvement: {pace_improvement:.2f} min/km faster! 🎉")
                else:
                    print(f"Pace change: {abs(pace_improvement):.2f} min/km slower")
                print()
    
    # Consistency analysis
    weekly_runs = df.groupby(df['start_date'].dt.isocalendar().week).size()
    avg_runs_per_week = weekly_runs.mean()
    consistency_score = 1 - (weekly_runs.std() / weekly_runs.mean()) if weekly_runs.mean() > 0 else 0
    
    print(f"Average runs per week: {avg_runs_per_week:.1f}")
    print(f"Consistency score: {consistency_score:.2f} (1.0 = perfectly consistent)")
    print()
    
    # Distance progression
    df_sorted = df.sort_values('start_date')
    if len(df_sorted) >= 10:
        first_10_avg = df_sorted.head(10)['distance'].mean()
        last_10_avg = df_sorted.tail(10)['distance'].mean()
        distance_progression = last_10_avg - first_10_avg
        
        print(f"First 10 runs average distance: {first_10_avg:.2f} km")
        print(f"Last 10 runs average distance: {last_10_avg:.2f} km")
        if distance_progression > 0:
            print(f"Distance progression: +{distance_progression:.2f} km increase! 📈")
        else:
            print(f"Distance change: {distance_progression:.2f} km")
        print()


def main():
    """Main analysis function."""
    # You can modify this to point to your specific CSV file
    # Look in parent directory (project root) for CSV files
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_files = [f for f in os.listdir(project_root) if f.startswith('strava_running_data_') and f.endswith('.csv')]
    csv_files = [os.path.join(project_root, f) for f in csv_files]
    
    if not csv_files:
        print("No Strava data CSV files found. Please run strava_data_puller.py first.")
        return
    
    # Use the most recent file
    latest_file = max(csv_files)
    print(f"Analyzing data from: {latest_file}\n")
    
    # Load data
    df = load_strava_data(latest_file)
    
    if df.empty:
        print("No data found in the CSV file.")
        return
    
    # Run analyses
    analyze_running_trends(df)
    find_personal_records(df)
    analyze_heart_rate_data(df)
    generate_training_insights(df)
    
    # Create visualizations
    try:
        create_visualizations(df)
        print("Visualizations saved as 'strava_running_analysis.png'")
    except ImportError:
        print("Matplotlib not available. Install with: pip install matplotlib seaborn")
    except Exception as e:
        print(f"Error creating visualizations: {e}")


if __name__ == "__main__":
    import os
    main()
