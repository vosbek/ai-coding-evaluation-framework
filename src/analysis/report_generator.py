"""
Report generation engine for AI coding assistant evaluation results.
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import asdict

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import pandas as pd
from jinja2 import Environment, FileSystemLoader

from .metrics_calculator import MetricsCalculator, SessionMetrics, ComparisonMetrics
from ..database.database import get_db
from ..database.models import TestSession


class ReportGenerator:
    """Generates comprehensive evaluation reports in multiple formats."""
    
    def __init__(self, output_dir: str = "reports/generated"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.metrics_calculator = MetricsCalculator()
        
        # Set up plotting style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
    
    def generate_session_report(self, session_id: int, format: str = 'html') -> str:
        """Generate a detailed report for a single evaluation session."""
        metrics = self.metrics_calculator.calculate_session_metrics(session_id)
        if not metrics:
            raise ValueError(f"No metrics found for session {session_id}")
        
        # Generate visualizations
        charts = self._generate_session_charts(metrics)
        
        # Generate report content
        if format.lower() == 'html':
            return self._generate_html_session_report(metrics, charts)
        elif format.lower() == 'json':
            return self._generate_json_session_report(metrics)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def generate_comparison_report(self, tool_a: str, tool_b: str, test_case_type: str = None, format: str = 'html') -> str:
        """Generate a comparative analysis report between two AI tools."""
        comparison = self.metrics_calculator.calculate_tool_comparison(tool_a, tool_b, test_case_type)
        if not comparison:
            raise ValueError(f"No comparison data found for {tool_a} vs {tool_b}")
        
        # Get individual session metrics for both tools
        tool_a_sessions = self._get_tool_sessions(tool_a, test_case_type)
        tool_b_sessions = self._get_tool_sessions(tool_b, test_case_type)
        
        # Generate visualizations
        charts = self._generate_comparison_charts(tool_a_sessions, tool_b_sessions, comparison)
        
        if format.lower() == 'html':
            return self._generate_html_comparison_report(comparison, tool_a_sessions, tool_b_sessions, charts)
        elif format.lower() == 'json':
            return self._generate_json_comparison_report(comparison, tool_a_sessions, tool_b_sessions)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def generate_executive_summary(self, tools: List[str] = None, test_case_types: List[str] = None) -> str:
        """Generate an executive summary report across all evaluations."""
        # Get all sessions
        with next(get_db()) as db:
            query = db.query(TestSession).filter(TestSession.status == 'completed')
            
            if tools:
                query = query.filter(TestSession.tool_name.in_(tools))
            if test_case_types:
                query = query.filter(TestSession.test_case_type.in_(test_case_types))
            
            sessions = query.all()
        
        if not sessions:
            raise ValueError("No completed sessions found")
        
        # Calculate summary statistics
        summary_data = self._calculate_executive_summary_data(sessions)
        
        # Generate visualizations
        charts = self._generate_executive_charts(summary_data)
        
        return self._generate_html_executive_summary(summary_data, charts)
    
    def _get_tool_sessions(self, tool_name: str, test_case_type: str = None) -> List[SessionMetrics]:
        """Get session metrics for a specific tool."""
        with next(get_db()) as db:
            query = db.query(TestSession).filter(
                TestSession.tool_name == tool_name,
                TestSession.status == 'completed'
            )
            
            if test_case_type:
                query = query.filter(TestSession.test_case_type == test_case_type)
            
            sessions = query.all()
        
        metrics = []
        for session in sessions:
            session_metrics = self.metrics_calculator.calculate_session_metrics(session.id)
            if session_metrics:
                metrics.append(session_metrics)
        
        return metrics
    
    def _generate_session_charts(self, metrics: SessionMetrics) -> Dict[str, str]:
        """Generate charts for a single session report."""
        charts = {}
        
        # AI Interaction Timeline Chart
        if metrics.total_ai_interactions > 0:
            fig, ax = plt.subplots(figsize=(12, 6))
            # This would need actual interaction timestamps from database
            # For now, create a placeholder
            ax.set_title(f'AI Interactions Timeline - {metrics.session_name}')
            ax.set_xlabel('Time')
            ax.set_ylabel('Interactions')
            
            chart_path = self.output_dir / f'session_{metrics.session_id}_interactions.png'
            plt.tight_layout()
            plt.savefig(chart_path, dpi=150, bbox_inches='tight')
            plt.close()
            charts['interactions_timeline'] = str(chart_path)
        
        # Code Changes by Type
        change_types = ['Created', 'Modified', 'Deleted']
        change_counts = [metrics.files_created, metrics.files_modified, metrics.files_deleted]
        
        if sum(change_counts) > 0:
            fig, ax = plt.subplots(figsize=(8, 6))
            bars = ax.bar(change_types, change_counts, color=['#2ecc71', '#3498db', '#e74c3c'])
            ax.set_title(f'Code Changes by Type - {metrics.session_name}')
            ax.set_ylabel('Number of Files')
            
            # Add value labels on bars
            for bar, count in zip(bars, change_counts):
                if count > 0:
                    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                           str(count), ha='center', va='bottom')
            
            chart_path = self.output_dir / f'session_{metrics.session_id}_changes.png'
            plt.tight_layout()
            plt.savefig(chart_path, dpi=150, bbox_inches='tight')
            plt.close()
            charts['code_changes'] = str(chart_path)
        
        # Phase Duration Chart
        if metrics.phase_durations:
            fig, ax = plt.subplots(figsize=(10, 6))
            phases = list(metrics.phase_durations.keys())
            durations = list(metrics.phase_durations.values())
            
            bars = ax.barh(phases, durations, color='#9b59b6')
            ax.set_title(f'Development Phase Durations - {metrics.session_name}')
            ax.set_xlabel('Duration (minutes)')
            
            # Add value labels
            for bar, duration in zip(bars, durations):
                ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2, 
                       f'{duration:.1f}m', ha='left', va='center')
            
            chart_path = self.output_dir / f'session_{metrics.session_id}_phases.png'
            plt.tight_layout()
            plt.savefig(chart_path, dpi=150, bbox_inches='tight')
            plt.close()
            charts['phase_durations'] = str(chart_path)
        
        return charts
    
    def _generate_comparison_charts(self, tool_a_sessions: List[SessionMetrics], 
                                  tool_b_sessions: List[SessionMetrics], 
                                  comparison: ComparisonMetrics) -> Dict[str, str]:
        """Generate comparison charts between two tools."""
        charts = {}
        
        # Performance Comparison Chart
        metrics = ['Speed', 'Productivity', 'Quality']
        improvements = [
            comparison.speed_improvement_percentage,
            comparison.productivity_improvement_percentage,
            comparison.code_quality_improvement_percentage
        ]
        
        fig, ax = plt.subplots(figsize=(10, 6))
        colors = ['#2ecc71' if x > 0 else '#e74c3c' for x in improvements]
        bars = ax.bar(metrics, improvements, color=colors)
        
        ax.set_title(f'Performance Comparison: {comparison.tool_a_name} vs {comparison.tool_b_name}')
        ax.set_ylabel('Improvement Percentage')
        ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        
        # Add value labels
        for bar, improvement in zip(bars, improvements):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, height + (1 if height >= 0 else -3), 
                   f'{improvement:.1f}%', ha='center', va='bottom' if height >= 0 else 'top')
        
        chart_path = self.output_dir / f'comparison_{comparison.tool_a_name}_vs_{comparison.tool_b_name}_performance.png'
        plt.tight_layout()
        plt.savefig(chart_path, dpi=150, bbox_inches='tight')
        plt.close()
        charts['performance_comparison'] = str(chart_path)
        
        # Duration Distribution Comparison
        durations_a = [s.total_duration_minutes for s in tool_a_sessions]
        durations_b = [s.total_duration_minutes for s in tool_b_sessions]
        
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.hist([durations_a, durations_b], bins=10, alpha=0.7, 
               label=[comparison.tool_a_name, comparison.tool_b_name],
               color=['#3498db', '#e67e22'])
        
        ax.set_title('Session Duration Distribution Comparison')
        ax.set_xlabel('Duration (minutes)')
        ax.set_ylabel('Frequency')
        ax.legend()
        
        chart_path = self.output_dir / f'comparison_{comparison.tool_a_name}_vs_{comparison.tool_b_name}_durations.png'
        plt.tight_layout()
        plt.savefig(chart_path, dpi=150, bbox_inches='tight')
        plt.close()
        charts['duration_distribution'] = str(chart_path)
        
        return charts
    
    def _generate_executive_charts(self, summary_data: Dict[str, Any]) -> Dict[str, str]:
        """Generate charts for executive summary."""
        charts = {}
        
        # Tool Performance Overview
        if 'tool_performance' in summary_data:
            tools = list(summary_data['tool_performance'].keys())
            avg_durations = [summary_data['tool_performance'][tool]['avg_duration'] for tool in tools]
            avg_satisfaction = [summary_data['tool_performance'][tool]['avg_satisfaction'] for tool in tools]
            
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
            
            # Average Duration by Tool
            bars1 = ax1.bar(tools, avg_durations, color='#3498db')
            ax1.set_title('Average Session Duration by Tool')
            ax1.set_ylabel('Duration (minutes)')
            ax1.tick_params(axis='x', rotation=45)
            
            for bar, duration in zip(bars1, avg_durations):
                ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                        f'{duration:.1f}m', ha='center', va='bottom')
            
            # Average Satisfaction by Tool
            bars2 = ax2.bar(tools, avg_satisfaction, color='#2ecc71')
            ax2.set_title('Average Satisfaction Rating by Tool')
            ax2.set_ylabel('Satisfaction (1-5)')
            ax2.set_ylim(0, 5)
            ax2.tick_params(axis='x', rotation=45)
            
            for bar, satisfaction in zip(bars2, avg_satisfaction):
                ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05, 
                        f'{satisfaction:.1f}', ha='center', va='bottom')
            
            chart_path = self.output_dir / 'executive_tool_performance.png'
            plt.tight_layout()
            plt.savefig(chart_path, dpi=150, bbox_inches='tight')
            plt.close()
            charts['tool_performance'] = str(chart_path)
        
        return charts
    
    def _generate_html_session_report(self, metrics: SessionMetrics, charts: Dict[str, str]) -> str:
        """Generate HTML report for a single session."""
        template_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Session Report - {{ metrics.session_name }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .header { border-bottom: 2px solid #3498db; padding-bottom: 20px; margin-bottom: 30px; }
        .metric-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0; }
        .metric-card { background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #3498db; }
        .metric-value { font-size: 2em; font-weight: bold; color: #2c3e50; }
        .metric-label { color: #7f8c8d; font-size: 0.9em; margin-top: 5px; }
        .chart { text-align: center; margin: 30px 0; }
        .chart img { max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 8px; }
        .section { margin: 40px 0; }
        .section h2 { color: #2c3e50; border-bottom: 1px solid #ecf0f1; padding-bottom: 10px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Session Evaluation Report</h1>
        <h2>{{ metrics.session_name }}</h2>
        <p><strong>Tool:</strong> {{ metrics.tool_name }} | <strong>Test Case:</strong> {{ metrics.test_case_type }} | <strong>Developer:</strong> {{ metrics.developer_id }}</p>
        <p><strong>Duration:</strong> {{ "%.1f"|format(metrics.total_duration_minutes) }} minutes | <strong>Date:</strong> {{ metrics.start_time.strftime("%Y-%m-%d %H:%M") }}</p>
    </div>

    <div class="section">
        <h2>Key Metrics</h2>
        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-value">{{ metrics.total_ai_interactions }}</div>
                <div class="metric-label">AI Interactions</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{{ metrics.lines_added }}</div>
                <div class="metric-label">Lines Added</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{{ "%.1f"|format(metrics.lines_per_minute) }}</div>
                <div class="metric-label">Lines per Minute</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{{ "%.1f"|format(metrics.average_quality_rating) }}</div>
                <div class="metric-label">Avg AI Quality Rating</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{{ "%.1f"|format(metrics.code_quality_score) }}</div>
                <div class="metric-label">Code Quality Score</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{{ metrics.satisfaction_rating or "N/A" }}</div>
                <div class="metric-label">Satisfaction Rating</div>
            </div>
        </div>
    </div>

    {% if charts.code_changes %}
    <div class="section">
        <h2>Code Changes Analysis</h2>
        <div class="chart">
            <img src="{{ charts.code_changes }}" alt="Code Changes Chart">
        </div>
    </div>
    {% endif %}

    {% if charts.phase_durations %}
    <div class="section">
        <h2>Development Phases</h2>
        <div class="chart">
            <img src="{{ charts.phase_durations }}" alt="Phase Durations Chart">
        </div>
    </div>
    {% endif %}

    <div class="section">
        <h2>Detailed Statistics</h2>
        <table style="width: 100%; border-collapse: collapse;">
            <tr style="background: #f8f9fa;">
                <th style="padding: 12px; text-align: left; border: 1px solid #ddd;">Metric</th>
                <th style="padding: 12px; text-align: left; border: 1px solid #ddd;">Value</th>
            </tr>
            <tr><td style="padding: 12px; border: 1px solid #ddd;">Total Duration</td><td style="padding: 12px; border: 1px solid #ddd;">{{ "%.1f"|format(metrics.total_duration_minutes) }} minutes</td></tr>
            <tr><td style="padding: 12px; border: 1px solid #ddd;">Files Created</td><td style="padding: 12px; border: 1px solid #ddd;">{{ metrics.files_created }}</td></tr>
            <tr><td style="padding: 12px; border: 1px solid #ddd;">Files Modified</td><td style="padding: 12px; border: 1px solid #ddd;">{{ metrics.files_modified }}</td></tr>
            <tr><td style="padding: 12px; border: 1px solid #ddd;">Files Deleted</td><td style="padding: 12px; border: 1px solid #ddd;">{{ metrics.files_deleted }}</td></tr>
            <tr><td style="padding: 12px; border: 1px solid #ddd;">AI Interactions per Hour</td><td style="padding: 12px; border: 1px solid #ddd;">{{ "%.1f"|format(metrics.ai_interactions_per_hour) }}</td></tr>
            <tr><td style="padding: 12px; border: 1px solid #ddd;">Helpful Interactions</td><td style="padding: 12px; border: 1px solid #ddd;">{{ "%.1f"|format(metrics.helpful_interactions_percentage) }}%</td></tr>
            <tr><td style="padding: 12px; border: 1px solid #ddd;">Total Tokens Used</td><td style="padding: 12px; border: 1px solid #ddd;">{{ metrics.total_tokens_used }}</td></tr>
            <tr><td style="padding: 12px; border: 1px solid #ddd;">Estimated Cost</td><td style="padding: 12px; border: 1px solid #ddd;">${{ "%.2f"|format(metrics.total_cost_estimate) }}</td></tr>
            <tr><td style="padding: 12px; border: 1px solid #ddd;">Build Success Rate</td><td style="padding: 12px; border: 1px solid #ddd;">{{ "%.1f"|format(metrics.build_success_rate) }}%</td></tr>
        </table>
    </div>

    <div class="section">
        <p style="color: #7f8c8d; font-size: 0.9em; text-align: center;">
            Report generated on {{ datetime.now().strftime("%Y-%m-%d %H:%M:%S") }} by AI Coding Assistant Evaluation Framework
        </p>
    </div>
</body>
</html>
        """
        
        from jinja2 import Template
        template = Template(template_content)
        
        html_content = template.render(
            metrics=metrics,
            charts=charts,
            datetime=datetime
        )
        
        # Save to file
        report_path = self.output_dir / f'session_{metrics.session_id}_report.html'
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(report_path)
    
    def _generate_html_comparison_report(self, comparison: ComparisonMetrics,
                                       tool_a_sessions: List[SessionMetrics],
                                       tool_b_sessions: List[SessionMetrics],
                                       charts: Dict[str, str]) -> str:
        """Generate HTML comparison report."""
        template_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Tool Comparison Report - {{ comparison.tool_a_name }} vs {{ comparison.tool_b_name }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .header { border-bottom: 2px solid #3498db; padding-bottom: 20px; margin-bottom: 30px; }
        .winner { color: #27ae60; font-weight: bold; }
        .loser { color: #e74c3c; font-weight: bold; }
        .tie { color: #f39c12; font-weight: bold; }
        .comparison-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin: 20px 0; }
        .tool-section { background: #f8f9fa; padding: 20px; border-radius: 8px; }
        .metric-value { font-size: 1.5em; font-weight: bold; color: #2c3e50; }
        .improvement { color: #27ae60; }
        .decline { color: #e74c3c; }
        .chart { text-align: center; margin: 30px 0; }
        .chart img { max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 8px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>AI Tool Comparison Report</h1>
        <h2>{{ comparison.tool_a_name }} vs {{ comparison.tool_b_name }}</h2>
        <p><strong>Test Case Type:</strong> {{ comparison.test_case_type }}</p>
        <p><strong>Sample Sizes:</strong> {{ comparison.tool_a_name }}: {{ comparison.sample_size_a }} sessions | {{ comparison.tool_b_name }}: {{ comparison.sample_size_b }} sessions</p>
    </div>

    <div class="section">
        <h2>Overall Winner: 
            {% if comparison.preference_winner == comparison.tool_a_name %}
                <span class="winner">{{ comparison.tool_a_name }}</span>
            {% elif comparison.preference_winner == comparison.tool_b_name %}
                <span class="winner">{{ comparison.tool_b_name }}</span>
            {% else %}
                <span class="tie">Tie</span>
            {% endif %}
        </h2>
    </div>

    <div class="section">
        <h2>Performance Comparison</h2>
        <table style="width: 100%; border-collapse: collapse;">
            <tr style="background: #f8f9fa;">
                <th style="padding: 12px; text-align: left; border: 1px solid #ddd;">Metric</th>
                <th style="padding: 12px; text-align: center; border: 1px solid #ddd;">{{ comparison.tool_a_name }} Advantage</th>
            </tr>
            <tr>
                <td style="padding: 12px; border: 1px solid #ddd;">Speed</td>
                <td style="padding: 12px; text-align: center; border: 1px solid #ddd;">
                    <span class="{% if comparison.speed_improvement_percentage > 0 %}improvement{% else %}decline{% endif %}">
                        {{ "%.1f"|format(comparison.speed_improvement_percentage) }}%
                    </span>
                </td>
            </tr>
            <tr>
                <td style="padding: 12px; border: 1px solid #ddd;">Productivity</td>
                <td style="padding: 12px; text-align: center; border: 1px solid #ddd;">
                    <span class="{% if comparison.productivity_improvement_percentage > 0 %}improvement{% else %}decline{% endif %}">
                        {{ "%.1f"|format(comparison.productivity_improvement_percentage) }}%
                    </span>
                </td>
            </tr>
            <tr>
                <td style="padding: 12px; border: 1px solid #ddd;">Code Quality</td>
                <td style="padding: 12px; text-align: center; border: 1px solid #ddd;">
                    <span class="{% if comparison.code_quality_improvement_percentage > 0 %}improvement{% else %}decline{% endif %}">
                        {{ "%.1f"|format(comparison.code_quality_improvement_percentage) }}%
                    </span>
                </td>
            </tr>
            <tr>
                <td style="padding: 12px; border: 1px solid #ddd;">Satisfaction</td>
                <td style="padding: 12px; text-align: center; border: 1px solid #ddd;">
                    <span class="{% if comparison.satisfaction_difference > 0 %}improvement{% else %}decline{% endif %}">
                        {{ "+%.1f"|format(comparison.satisfaction_difference) if comparison.satisfaction_difference > 0 else "%.1f"|format(comparison.satisfaction_difference) }} points
                    </span>
                </td>
            </tr>
        </table>
    </div>

    {% if charts.performance_comparison %}
    <div class="section">
        <h2>Performance Visualization</h2>
        <div class="chart">
            <img src="{{ charts.performance_comparison }}" alt="Performance Comparison Chart">
        </div>
    </div>
    {% endif %}

    {% if charts.duration_distribution %}
    <div class="section">
        <h2>Duration Distribution</h2>
        <div class="chart">
            <img src="{{ charts.duration_distribution }}" alt="Duration Distribution Chart">
        </div>
    </div>
    {% endif %}

    <div class="section">
        <p style="color: #7f8c8d; font-size: 0.9em; text-align: center;">
            Report generated on {{ datetime.now().strftime("%Y-%m-%d %H:%M:%S") }} by AI Coding Assistant Evaluation Framework
        </p>
    </div>
</body>
</html>
        """
        
        from jinja2 import Template
        template = Template(template_content)
        
        html_content = template.render(
            comparison=comparison,
            tool_a_sessions=tool_a_sessions,
            tool_b_sessions=tool_b_sessions,
            charts=charts,
            datetime=datetime
        )
        
        # Save to file
        report_path = self.output_dir / f'comparison_{comparison.tool_a_name}_vs_{comparison.tool_b_name}.html'
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(report_path)
    
    def _generate_html_executive_summary(self, summary_data: Dict[str, Any], charts: Dict[str, str]) -> str:
        """Generate HTML executive summary report."""
        # Implementation for executive summary HTML
        report_path = self.output_dir / 'executive_summary.html'
        # ... HTML template implementation
        return str(report_path)
    
    def _generate_json_session_report(self, metrics: SessionMetrics) -> str:
        """Generate JSON report for a single session."""
        report_data = asdict(metrics)
        report_path = self.output_dir / f'session_{metrics.session_id}_report.json'
        
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        return str(report_path)
    
    def _generate_json_comparison_report(self, comparison: ComparisonMetrics,
                                       tool_a_sessions: List[SessionMetrics],
                                       tool_b_sessions: List[SessionMetrics]) -> str:
        """Generate JSON comparison report."""
        report_data = {
            'comparison': asdict(comparison),
            'tool_a_sessions': [asdict(s) for s in tool_a_sessions],
            'tool_b_sessions': [asdict(s) for s in tool_b_sessions]
        }
        
        report_path = self.output_dir / f'comparison_{comparison.tool_a_name}_vs_{comparison.tool_b_name}.json'
        
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        return str(report_path)
    
    def _calculate_executive_summary_data(self, sessions: List[TestSession]) -> Dict[str, Any]:
        """Calculate data for executive summary."""
        # Group sessions by tool
        tools_data = defaultdict(list)
        for session in sessions:
            metrics = self.metrics_calculator.calculate_session_metrics(session.id)
            if metrics:
                tools_data[session.tool_name].append(metrics)
        
        # Calculate summary statistics for each tool
        tool_performance = {}
        for tool_name, tool_sessions in tools_data.items():
            durations = [s.total_duration_minutes for s in tool_sessions]
            satisfactions = [s.satisfaction_rating for s in tool_sessions if s.satisfaction_rating]
            
            tool_performance[tool_name] = {
                'session_count': len(tool_sessions),
                'avg_duration': sum(durations) / len(durations) if durations else 0,
                'avg_satisfaction': sum(satisfactions) / len(satisfactions) if satisfactions else 0
            }
        
        return {
            'total_sessions': len(sessions),
            'tools_evaluated': list(tools_data.keys()),
            'evaluation_period': {
                'start': min(s.start_time for s in sessions),
                'end': max(s.end_time or datetime.now() for s in sessions)
            },
            'tool_performance': tool_performance
        }