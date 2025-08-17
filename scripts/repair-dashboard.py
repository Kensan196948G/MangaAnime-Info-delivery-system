#!/usr/bin/env python3

"""
Comprehensive Python dashboard for the 30-minute auto-repair system
Provides system overview, statistics, trends, and export capabilities
"""

import json
import csv
import sys
import os
import time
import argparse
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import subprocess

try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.animation import FuncAnimation
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("Warning: matplotlib not available. Graphical features disabled.")

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

# Color codes for terminal output
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

@dataclass
class RepairStats:
    """Statistics for repair operations"""
    total_repairs: int = 0
    successful_repairs: int = 0
    failed_repairs: int = 0
    average_duration: float = 0.0
    success_rate: float = 0.0
    failure_rate: float = 0.0
    repairs_per_hour: float = 0.0
    most_common_failure: str = "None"
    last_repair_time: Optional[str] = None

@dataclass
class SystemMetrics:
    """System performance metrics"""
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    disk_usage: float = 0.0
    uptime: str = "0h 0m"
    active_processes: int = 0
    github_api_remaining: int = 0
    github_api_reset_time: str = "Unknown"

class RepairDashboard:
    """Main dashboard class for monitoring and analytics"""
    
    def __init__(self, base_path: str = ".."):
        self.base_path = Path(base_path)
        self.state_file = self.base_path / ".repair_state.json"
        self.log_dir = self.base_path / "logs"
        self.db_path = self.base_path / "repair_analytics.db"
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database for analytics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create tables for analytics
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS repair_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    repair_type TEXT,
                    status TEXT,
                    duration REAL,
                    error_message TEXT,
                    workflow_name TEXT,
                    commit_hash TEXT
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    cpu_usage REAL,
                    memory_usage REAL,
                    disk_usage REAL,
                    github_api_remaining INTEGER,
                    active_repairs INTEGER
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS failure_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    failure_type TEXT,
                    count INTEGER DEFAULT 1,
                    last_occurrence DATETIME DEFAULT CURRENT_TIMESTAMP,
                    resolution_strategy TEXT
                )
            """)
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"{Colors.RED}Error initializing database: {e}{Colors.END}")
    
    def load_state(self) -> Dict[str, Any]:
        """Load current system state"""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"{Colors.RED}Error loading state: {e}{Colors.END}")
            return {}
    
    def get_repair_stats(self) -> RepairStats:
        """Calculate comprehensive repair statistics"""
        state = self.load_state()
        
        stats = RepairStats(
            total_repairs=state.get('total_repairs', 0),
            successful_repairs=state.get('successful_repairs', 0),
            failed_repairs=state.get('failed_repairs', 0),
            last_repair_time=state.get('last_repair_time')
        )
        
        if stats.total_repairs > 0:
            stats.success_rate = (stats.successful_repairs / stats.total_repairs) * 100
            stats.failure_rate = (stats.failed_repairs / stats.total_repairs) * 100
        
        # Calculate from database if available
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Average duration
            cursor.execute("SELECT AVG(duration) FROM repair_history WHERE status = 'success'")
            avg_duration = cursor.fetchone()[0]
            if avg_duration:
                stats.average_duration = avg_duration
            
            # Repairs per hour (last 24 hours)
            cursor.execute("""
                SELECT COUNT(*) FROM repair_history 
                WHERE timestamp > datetime('now', '-24 hours')
            """)
            repairs_24h = cursor.fetchone()[0] or 0
            stats.repairs_per_hour = repairs_24h / 24.0
            
            # Most common failure
            cursor.execute("""
                SELECT error_message, COUNT(*) as count 
                FROM repair_history 
                WHERE status = 'failure' 
                GROUP BY error_message 
                ORDER BY count DESC 
                LIMIT 1
            """)
            result = cursor.fetchone()
            if result:
                stats.most_common_failure = result[0][:50] + "..." if len(result[0]) > 50 else result[0]
            
            conn.close()
        except Exception as e:
            print(f"{Colors.YELLOW}Warning: Could not load extended stats from database: {e}{Colors.END}")
        
        return stats
    
    def get_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics"""
        metrics = SystemMetrics()
        
        try:
            # CPU usage
            cpu_cmd = "top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | sed 's/%us,//'"
            cpu_result = subprocess.run(cpu_cmd, shell=True, capture_output=True, text=True)
            if cpu_result.returncode == 0:
                metrics.cpu_usage = float(cpu_result.stdout.strip())
        except:
            pass
        
        try:
            # Memory usage
            mem_cmd = "free | grep Mem | awk '{printf \"%.1f\", $3/$2 * 100.0}'"
            mem_result = subprocess.run(mem_cmd, shell=True, capture_output=True, text=True)
            if mem_result.returncode == 0:
                metrics.memory_usage = float(mem_result.stdout.strip())
        except:
            pass
        
        try:
            # Disk usage
            disk_cmd = "df . | tail -1 | awk '{print $5}' | sed 's/%//'"
            disk_result = subprocess.run(disk_cmd, shell=True, capture_output=True, text=True)
            if disk_result.returncode == 0:
                metrics.disk_usage = float(disk_result.stdout.strip())
        except:
            pass
        
        try:
            # Uptime
            uptime_cmd = "uptime -p"
            uptime_result = subprocess.run(uptime_cmd, shell=True, capture_output=True, text=True)
            if uptime_result.returncode == 0:
                metrics.uptime = uptime_result.stdout.strip()
        except:
            pass
        
        try:
            # GitHub API rate limit
            gh_cmd = "gh api rate_limit --jq '.rate.remaining'"
            gh_result = subprocess.run(gh_cmd, shell=True, capture_output=True, text=True)
            if gh_result.returncode == 0:
                metrics.github_api_remaining = int(gh_result.stdout.strip())
        except:
            pass
        
        # Store metrics in database
        self.store_system_metrics(metrics)
        
        return metrics
    
    def store_system_metrics(self, metrics: SystemMetrics):
        """Store system metrics in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO system_metrics 
                (cpu_usage, memory_usage, disk_usage, github_api_remaining, active_repairs)
                VALUES (?, ?, ?, ?, ?)
            """, (
                metrics.cpu_usage,
                metrics.memory_usage,
                metrics.disk_usage,
                metrics.github_api_remaining,
                0  # TODO: Calculate active repairs
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"{Colors.YELLOW}Warning: Could not store metrics: {e}{Colors.END}")
    
    def display_dashboard(self):
        """Display the main dashboard"""
        os.system('clear')
        
        print(f"{Colors.BLUE}{'='*80}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}        AUTO-REPAIR SYSTEM DASHBOARD        {Colors.END}")
        print(f"{Colors.BLUE}{'='*80}{Colors.END}")
        print(f"{Colors.CYAN}Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.END}\n")
        
        # Repair Statistics
        stats = self.get_repair_stats()
        self.display_repair_stats(stats)
        
        # System Metrics
        metrics = self.get_system_metrics()
        self.display_system_metrics(metrics)
        
        # Recent Activity
        self.display_recent_activity()
        
        # Failure Patterns
        self.display_failure_patterns()
        
        print(f"\n{Colors.BLUE}{'='*80}{Colors.END}")
    
    def display_repair_stats(self, stats: RepairStats):
        """Display repair statistics section"""
        print(f"{Colors.YELLOW}📊 REPAIR STATISTICS{Colors.END}")
        print(f"   Total Repairs:     {Colors.BOLD}{stats.total_repairs:,}{Colors.END}")
        print(f"   Successful:        {Colors.GREEN}{stats.successful_repairs:,}{Colors.END}")
        print(f"   Failed:            {Colors.RED}{stats.failed_repairs:,}{Colors.END}")
        print(f"   Success Rate:      {Colors.GREEN}{stats.success_rate:.1f}%{Colors.END}")
        print(f"   Avg Duration:      {Colors.CYAN}{stats.average_duration:.2f}s{Colors.END}")
        print(f"   Repairs/Hour:      {Colors.PURPLE}{stats.repairs_per_hour:.2f}{Colors.END}")
        print(f"   Last Repair:       {Colors.CYAN}{stats.last_repair_time or 'Never'}{Colors.END}")
        print(f"   Common Failure:    {Colors.RED}{stats.most_common_failure}{Colors.END}")
        print()
    
    def display_system_metrics(self, metrics: SystemMetrics):
        """Display system metrics section"""
        print(f"{Colors.YELLOW}💻 SYSTEM METRICS{Colors.END}")
        print(f"   CPU Usage:         {self.colorize_metric(metrics.cpu_usage, 80, 90)}")
        print(f"   Memory Usage:      {self.colorize_metric(metrics.memory_usage, 80, 90)}")
        print(f"   Disk Usage:        {self.colorize_metric(metrics.disk_usage, 80, 90)}")
        print(f"   System Uptime:     {Colors.CYAN}{metrics.uptime}{Colors.END}")
        print(f"   GitHub API:        {self.colorize_api_limit(metrics.github_api_remaining)}")
        print()
    
    def colorize_metric(self, value: float, warning: float, critical: float) -> str:
        """Colorize metric based on thresholds"""
        if value >= critical:
            return f"{Colors.RED}{value:.1f}%{Colors.END}"
        elif value >= warning:
            return f"{Colors.YELLOW}{value:.1f}%{Colors.END}"
        else:
            return f"{Colors.GREEN}{value:.1f}%{Colors.END}"
    
    def colorize_api_limit(self, remaining: int) -> str:
        """Colorize GitHub API limit"""
        if remaining < 100:
            return f"{Colors.RED}{remaining:,} remaining{Colors.END}"
        elif remaining < 500:
            return f"{Colors.YELLOW}{remaining:,} remaining{Colors.END}"
        else:
            return f"{Colors.GREEN}{remaining:,} remaining{Colors.END}"
    
    def display_recent_activity(self):
        """Display recent repair activity"""
        print(f"{Colors.YELLOW}📋 RECENT ACTIVITY (Last 10){Colors.END}")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT timestamp, repair_type, status, duration, workflow_name
                FROM repair_history 
                ORDER BY timestamp DESC 
                LIMIT 10
            """)
            
            results = cursor.fetchall()
            
            if results:
                for row in results:
                    timestamp, repair_type, status, duration, workflow_name = row
                    status_color = Colors.GREEN if status == 'success' else Colors.RED
                    workflow_name = workflow_name or 'Unknown'
                    duration = duration or 0.0
                    
                    print(f"   {Colors.CYAN}{timestamp}{Colors.END} "
                          f"{status_color}[{status.upper()}]{Colors.END} "
                          f"{repair_type} in {workflow_name} ({duration:.1f}s)")
            else:
                print(f"   {Colors.YELLOW}No recent activity recorded{Colors.END}")
            
            conn.close()
        except Exception as e:
            print(f"   {Colors.RED}Error loading activity: {e}{Colors.END}")
        
        print()
    
    def display_failure_patterns(self):
        """Display failure pattern analysis"""
        print(f"{Colors.YELLOW}🔍 FAILURE PATTERNS{Colors.END}")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT failure_type, count, last_occurrence, resolution_strategy
                FROM failure_patterns 
                ORDER BY count DESC 
                LIMIT 5
            """)
            
            results = cursor.fetchall()
            
            if results:
                for row in results:
                    failure_type, count, last_occurrence, resolution_strategy = row
                    print(f"   {Colors.RED}{failure_type}{Colors.END} "
                          f"({count} occurrences, last: {last_occurrence})")
                    if resolution_strategy:
                        print(f"     └─ Strategy: {Colors.GREEN}{resolution_strategy}{Colors.END}")
            else:
                print(f"   {Colors.GREEN}No failure patterns detected{Colors.END}")
            
            conn.close()
        except Exception as e:
            print(f"   {Colors.RED}Error loading patterns: {e}{Colors.END}")
        
        print()
    
    def generate_trend_graph(self, output_file: str = "repair_trends.png"):
        """Generate trend analysis graph"""
        if not HAS_MATPLOTLIB:
            print(f"{Colors.RED}Matplotlib not available for graphing{Colors.END}")
            return
        
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Load data for plotting
            query = """
                SELECT DATE(timestamp) as date, 
                       COUNT(*) as total_repairs,
                       SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful
                FROM repair_history 
                WHERE timestamp > datetime('now', '-30 days')
                GROUP BY DATE(timestamp)
                ORDER BY date
            """
            
            if HAS_PANDAS:
                df = pd.read_sql_query(query, conn)
                
                if not df.empty:
                    df['date'] = pd.to_datetime(df['date'])
                    df['success_rate'] = (df['successful'] / df['total_repairs']) * 100
                    
                    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
                    
                    # Repair count over time
                    ax1.plot(df['date'], df['total_repairs'], 'b-', label='Total Repairs')
                    ax1.plot(df['date'], df['successful'], 'g-', label='Successful')
                    ax1.set_title('Repair Activity Over Time (Last 30 Days)')
                    ax1.set_ylabel('Number of Repairs')
                    ax1.legend()
                    ax1.grid(True, alpha=0.3)
                    
                    # Success rate over time
                    ax2.plot(df['date'], df['success_rate'], 'r-', linewidth=2)
                    ax2.set_title('Success Rate Over Time')
                    ax2.set_ylabel('Success Rate (%)')
                    ax2.set_xlabel('Date')
                    ax2.grid(True, alpha=0.3)
                    ax2.set_ylim(0, 100)
                    
                    plt.tight_layout()
                    plt.savefig(output_file, dpi=300, bbox_inches='tight')
                    print(f"{Colors.GREEN}Trend graph saved to: {output_file}{Colors.END}")
                else:
                    print(f"{Colors.YELLOW}No data available for trending{Colors.END}")
            
            conn.close()
            
        except Exception as e:
            print(f"{Colors.RED}Error generating trend graph: {e}{Colors.END}")
    
    def export_data(self, format_type: str, output_file: str):
        """Export analytics data to file"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            if format_type.lower() == 'json':
                self.export_json(conn, output_file)
            elif format_type.lower() == 'csv':
                self.export_csv(conn, output_file)
            else:
                print(f"{Colors.RED}Unsupported format: {format_type}{Colors.END}")
                return
            
            conn.close()
            print(f"{Colors.GREEN}Data exported to: {output_file}{Colors.END}")
            
        except Exception as e:
            print(f"{Colors.RED}Error exporting data: {e}{Colors.END}")
    
    def export_json(self, conn: sqlite3.Connection, output_file: str):
        """Export data to JSON format"""
        cursor = conn.cursor()
        
        data = {
            'export_timestamp': datetime.now().isoformat(),
            'repair_history': [],
            'system_metrics': [],
            'failure_patterns': []
        }
        
        # Export repair history
        cursor.execute("SELECT * FROM repair_history ORDER BY timestamp DESC LIMIT 1000")
        columns = [description[0] for description in cursor.description]
        for row in cursor.fetchall():
            data['repair_history'].append(dict(zip(columns, row)))
        
        # Export system metrics
        cursor.execute("SELECT * FROM system_metrics ORDER BY timestamp DESC LIMIT 1000")
        columns = [description[0] for description in cursor.description]
        for row in cursor.fetchall():
            data['system_metrics'].append(dict(zip(columns, row)))
        
        # Export failure patterns
        cursor.execute("SELECT * FROM failure_patterns ORDER BY count DESC")
        columns = [description[0] for description in cursor.description]
        for row in cursor.fetchall():
            data['failure_patterns'].append(dict(zip(columns, row)))
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def export_csv(self, conn: sqlite3.Connection, output_file: str):
        """Export data to CSV format"""
        cursor = conn.cursor()
        
        with open(output_file, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            # Export repair history
            cursor.execute("SELECT * FROM repair_history ORDER BY timestamp DESC")
            columns = [description[0] for description in cursor.description]
            writer.writerow(['=== REPAIR HISTORY ==='])
            writer.writerow(columns)
            writer.writerows(cursor.fetchall())
            
            writer.writerow([])  # Empty row
            
            # Export system metrics
            cursor.execute("SELECT * FROM system_metrics ORDER BY timestamp DESC LIMIT 100")
            columns = [description[0] for description in cursor.description]
            writer.writerow(['=== SYSTEM METRICS ==='])
            writer.writerow(columns)
            writer.writerows(cursor.fetchall())
    
    def interactive_mode(self):
        """Run dashboard in interactive mode"""
        print(f"{Colors.GREEN}Starting interactive dashboard...{Colors.END}")
        print(f"{Colors.CYAN}Commands: 'q' to quit, 'r' to refresh, 'e' to export, 'g' to generate graph{Colors.END}")
        
        while True:
            self.display_dashboard()
            print(f"{Colors.CYAN}Command (q/r/e/g): {Colors.END}", end='', flush=True)
            
            try:
                command = input().strip().lower()
                
                if command == 'q':
                    print(f"{Colors.YELLOW}Dashboard closed{Colors.END}")
                    break
                elif command == 'r':
                    continue
                elif command == 'e':
                    format_type = input(f"{Colors.CYAN}Export format (json/csv): {Colors.END}").strip()
                    if format_type in ['json', 'csv']:
                        filename = f"repair_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format_type}"
                        self.export_data(format_type, filename)
                    input(f"{Colors.CYAN}Press Enter to continue...{Colors.END}")
                elif command == 'g':
                    if HAS_MATPLOTLIB:
                        filename = f"repair_trends_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                        self.generate_trend_graph(filename)
                    else:
                        print(f"{Colors.RED}Matplotlib not available{Colors.END}")
                    input(f"{Colors.CYAN}Press Enter to continue...{Colors.END}")
                else:
                    print(f"{Colors.YELLOW}Unknown command: {command}{Colors.END}")
                    time.sleep(1)
                    
            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}Dashboard closed{Colors.END}")
                break
            except EOFError:
                print(f"\n{Colors.YELLOW}Dashboard closed{Colors.END}")
                break

def main():
    """Main function with command line argument parsing"""
    parser = argparse.ArgumentParser(description="Auto-Repair System Dashboard")
    parser.add_argument('--base-path', default='..', help='Base path to project directory')
    parser.add_argument('--interactive', '-i', action='store_true', help='Run in interactive mode')
    parser.add_argument('--export', choices=['json', 'csv'], help='Export data to file')
    parser.add_argument('--output', '-o', help='Output filename for export')
    parser.add_argument('--graph', '-g', action='store_true', help='Generate trend graph')
    parser.add_argument('--watch', '-w', type=int, metavar='SECONDS', help='Watch mode with refresh interval')
    
    args = parser.parse_args()
    
    dashboard = RepairDashboard(args.base_path)
    
    if args.interactive:
        dashboard.interactive_mode()
    elif args.export:
        output_file = args.output or f"repair_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{args.export}"
        dashboard.export_data(args.export, output_file)
    elif args.graph:
        output_file = args.output or f"repair_trends_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        dashboard.generate_trend_graph(output_file)
    elif args.watch:
        try:
            while True:
                dashboard.display_dashboard()
                time.sleep(args.watch)
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Watch mode stopped{Colors.END}")
    else:
        dashboard.display_dashboard()

if __name__ == "__main__":
    main()