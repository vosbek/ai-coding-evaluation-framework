"""
CLI commands for generating reports and analysis.
"""

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from pathlib import Path

from ..database.database import get_db
from ..database.models import TestSession
from .metrics_calculator import MetricsCalculator
from .report_generator import ReportGenerator


console = Console()


@click.group()
def reports():
    """Generate reports and analysis."""
    pass


@reports.command()
@click.option('--session-id', type=int, required=True, help='Session ID to generate report for')
@click.option('--format', type=click.Choice(['html', 'json']), default='html', help='Report format')
@click.option('--open-browser', is_flag=True, help='Open report in browser after generation')
def session_report(session_id: int, format: str, open_browser: bool):
    """Generate a detailed report for a specific evaluation session."""
    try:
        generator = ReportGenerator()
        report_path = generator.generate_session_report(session_id, format)
        
        console.print(f"[green]Session report generated: {report_path}[/green]")
        
        if open_browser and format == 'html':
            import webbrowser
            webbrowser.open(f'file://{Path(report_path).absolute()}')
            console.print("[blue]Report opened in browser[/blue]")
            
    except Exception as e:
        console.print(f"[red]Failed to generate session report: {e}[/red]")


@reports.command()
@click.option('--tool-a', required=True, help='First AI tool to compare')
@click.option('--tool-b', required=True, help='Second AI tool to compare')
@click.option('--test-case-type', help='Filter by specific test case type')
@click.option('--format', type=click.Choice(['html', 'json']), default='html', help='Report format')
@click.option('--open-browser', is_flag=True, help='Open report in browser after generation')
def comparison_report(tool_a: str, tool_b: str, test_case_type: str, format: str, open_browser: bool):
    """Generate a comparative analysis report between two AI tools."""
    try:
        generator = ReportGenerator()
        report_path = generator.generate_comparison_report(tool_a, tool_b, test_case_type, format)
        
        console.print(f"[green]Comparison report generated: {report_path}[/green]")
        
        if open_browser and format == 'html':
            import webbrowser
            webbrowser.open(f'file://{Path(report_path).absolute()}')
            console.print("[blue]Report opened in browser[/blue]")
            
    except Exception as e:
        console.print(f"[red]Failed to generate comparison report: {e}[/red]")


@reports.command()
@click.option('--tools', help='Comma-separated list of tools to include')
@click.option('--test-types', help='Comma-separated list of test case types to include')
@click.option('--open-browser', is_flag=True, help='Open report in browser after generation')
def executive_summary(tools: str, test_types: str, open_browser: bool):
    """Generate an executive summary report across all evaluations."""
    try:
        tools_list = tools.split(',') if tools else None
        test_types_list = test_types.split(',') if test_types else None
        
        generator = ReportGenerator()
        report_path = generator.generate_executive_summary(tools_list, test_types_list)
        
        console.print(f"[green]Executive summary generated: {report_path}[/green]")
        
        if open_browser:
            import webbrowser
            webbrowser.open(f'file://{Path(report_path).absolute()}')
            console.print("[blue]Report opened in browser[/blue]")
            
    except Exception as e:
        console.print(f"[red]Failed to generate executive summary: {e}[/red]")


@reports.command()
@click.option('--session-id', type=int, help='Specific session ID to analyze')
@click.option('--tool', help='Filter by AI tool name')
@click.option('--test-type', help='Filter by test case type')
def quick_analysis(session_id: int, tool: str, test_type: str):
    """Show quick analysis and metrics in the terminal."""
    calculator = MetricsCalculator()
    
    if session_id:
        # Analyze specific session
        metrics = calculator.calculate_session_metrics(session_id)
        if not metrics:
            console.print(f"[red]No metrics found for session {session_id}[/red]")
            return
        
        # Display session metrics
        table = Table(title=f"Session Analysis: {metrics.session_name}")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="magenta")
        
        table.add_row("Tool", metrics.tool_name)
        table.add_row("Test Case Type", metrics.test_case_type)
        table.add_row("Duration", f"{metrics.total_duration_minutes:.1f} minutes")
        table.add_row("AI Interactions", str(metrics.total_ai_interactions))
        table.add_row("Lines Added", str(metrics.lines_added))
        table.add_row("Lines per Minute", f"{metrics.lines_per_minute:.2f}")
        table.add_row("Avg AI Quality", f"{metrics.average_quality_rating:.1f}/5")
        table.add_row("Code Quality Score", f"{metrics.code_quality_score:.1f}%")
        table.add_row("Satisfaction", f"{metrics.satisfaction_rating or 'N/A'}")
        table.add_row("Total Cost", f"${metrics.total_cost_estimate:.2f}")
        
        console.print(table)
        
    else:
        # Show summary statistics
        summary = calculator.get_session_summary_stats(tool, test_type)
        if not summary:
            console.print("[yellow]No completed sessions found with the specified filters[/yellow]")
            return
        
        # Display summary
        panel_content = f"""
[bold]Total Sessions:[/bold] {summary['total_sessions']}

[bold]Duration Statistics:[/bold]
• Average: {summary['duration']['mean']:.1f} minutes
• Median: {summary['duration']['median']:.1f} minutes
• Range: {summary['duration']['min']:.1f} - {summary['duration']['max']:.1f} minutes

[bold]Productivity:[/bold]
• Average: {summary['productivity']['mean']:.2f} lines/minute
• Best: {summary['productivity']['max']:.2f} lines/minute

[bold]Quality:[/bold]
• Average Score: {summary['quality']['mean']:.1f}%
• Best Score: {summary['quality']['max']:.1f}%

[bold]Satisfaction:[/bold]
• Average Rating: {summary['satisfaction']['mean']:.1f}/5
• Based on {summary['satisfaction']['count']} responses
        """
        
        title = "Overall Statistics"
        if tool:
            title += f" - {tool}"
        if test_type:
            title += f" - {test_type}"
        
        console.print(Panel(panel_content, title=title))


@reports.command()
def list_sessions():
    """List all completed evaluation sessions."""
    try:
        with next(get_db()) as db:
            sessions = db.query(TestSession).filter(
                TestSession.status == 'completed'
            ).order_by(TestSession.start_time.desc()).all()
        
        if not sessions:
            console.print("[yellow]No completed sessions found[/yellow]")
            return
        
        table = Table(title="Completed Evaluation Sessions")
        table.add_column("ID", justify="right", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Tool", style="blue")
        table.add_column("Type", style="yellow")
        table.add_column("Duration", justify="right", style="magenta")
        table.add_column("Start Time", style="dim")
        
        calculator = MetricsCalculator()
        
        for session in sessions:
            # Get basic duration
            if session.end_time:
                duration = (session.end_time - session.start_time).total_seconds() / 60
                duration_str = f"{duration:.1f}m"
            else:
                duration_str = "Incomplete"
            
            table.add_row(
                str(session.id),
                session.session_name,
                session.tool_name,
                session.test_case_type,
                duration_str,
                session.start_time.strftime("%Y-%m-%d %H:%M")
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Failed to list sessions: {e}[/red]")


@reports.command()
def available_tools():
    """List all AI tools that have been evaluated."""
    try:
        with next(get_db()) as db:
            tools = db.query(TestSession.tool_name).distinct().all()
            tools = [t[0] for t in tools]
        
        if not tools:
            console.print("[yellow]No tools found in database[/yellow]")
            return
        
        console.print("[blue]Available AI Tools:[/blue]")
        for tool in sorted(tools):
            # Get session count for each tool
            with next(get_db()) as db:
                count = db.query(TestSession).filter(
                    TestSession.tool_name == tool,
                    TestSession.status == 'completed'
                ).count()
            
            console.print(f"  • {tool} ({count} completed sessions)")
            
    except Exception as e:
        console.print(f"[red]Failed to list tools: {e}[/red]")


if __name__ == '__main__':
    reports()