"""
Enhanced CLI with integrated monitoring capabilities.
"""

import click
import json
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

from ..database.database import init_database, db_manager
from .logger import EvaluationLogger
from ..monitoring.session_manager import EvaluationSessionManager
from ..monitoring.timing_tracker import StandardizedPhases


console = Console()


@click.group()
@click.version_option()
def cli():
    """AI Coding Assistant Evaluation Framework - Enhanced CLI with Monitoring"""
    pass


@cli.command()
def init():
    """Initialize the database and create tables."""
    console.print("[blue]Initializing database...[/blue]")
    try:
        init_database()
        info = db_manager.get_database_info()
        console.print(f"[green]Database initialized at: {info['database_path']}[/green]")
        console.print(f"[green]Created {info['total_tables']} tables[/green]")
    except Exception as e:
        console.print(f"[red]Failed to initialize database: {e}[/red]")


@cli.command()
@click.option('--name', prompt=True, help='Session name')
@click.option('--tool', prompt=True, help='AI tool name (cursor, github_copilot, etc.)')
@click.option('--type', 'test_type', prompt=True, help='Test case type (bug_fix, new_feature, refactoring)')
@click.option('--developer', help='Developer ID')
@click.option('--watch-path', default='.', help='Path to monitor for changes')
@click.option('--enable-monitoring/--disable-monitoring', default=True, help='Enable automatic monitoring')
def start_session(name: str, tool: str, test_type: str, developer: str, watch_path: str, enable_monitoring: bool):
    """Start a new evaluation session with integrated monitoring."""
    logger = EvaluationLogger()
    
    # Start basic session
    session_id = logger.start_session(
        session_name=name,
        tool_name=tool,
        test_case_type=test_type,
        developer_id=developer
    )
    
    # Start monitoring if enabled
    if enable_monitoring:
        try:
            session_manager = EvaluationSessionManager(session_id, watch_path)
            session_manager.start_monitoring()
            
            console.print(Panel(
                f"[green]Monitoring Active[/green]\n"
                f"File monitoring: ✅\n"
                f"Timing tracking: ✅\n"
                f"Watch path: {watch_path}",
                title="Session Monitoring"
            ))
            
            # Save session manager reference (in real app, this would be managed differently)
            import pickle
            with open(f'.session_{session_id}.pkl', 'wb') as f:
                pickle.dump(session_manager, f)
                
        except Exception as e:
            console.print(f"[yellow]Warning: Could not start monitoring: {e}[/yellow]")
    
    console.print(f"[green]Session {session_id} started successfully[/green]")


@cli.command()
@click.option('--notes', help='Session completion notes')
def end_session(notes: str):
    """End the current evaluation session."""
    logger = EvaluationLogger()
    
    if not logger.current_session_id:
        console.print("[red]No active session to end[/red]")
        return
    
    session_id = logger.current_session_id
    
    # Stop monitoring if active
    try:
        import pickle
        import os
        session_file = f'.session_{session_id}.pkl'
        
        if os.path.exists(session_file):
            with open(session_file, 'rb') as f:
                session_manager = pickle.load(f)
            
            summary = session_manager.stop_monitoring()
            
            # Display summary
            if summary:
                console.print("[blue]Session Summary:[/blue]")
                if 'timing' in summary:
                    console.print(f"Total duration: {summary['timing'].get('elapsed_time_formatted', 'Unknown')}")
                if 'file_changes' in summary:
                    console.print(f"Files changed: {summary['file_changes'].get('total_changes', 0)}")
                if 'statistics' in summary:
                    console.print(f"AI interactions: {summary['statistics'].get('ai_interactions', 0)}")
            
            # Clean up session file
            os.remove(session_file)
            
    except Exception as e:
        console.print(f"[yellow]Warning: Could not stop monitoring: {e}[/yellow]")
    
    # End the session
    if not notes:
        notes = Prompt.ask("Session completion notes (optional)", default="")
    
    logger.end_session(notes if notes else None)


@cli.command()
def monitor_start():
    """Start monitoring for the current session."""
    logger = EvaluationLogger()
    
    if not logger.current_session_id:
        console.print("[red]No active session. Start a session first.[/red]")
        return
    
    watch_path = Prompt.ask("Watch path", default=".")
    
    try:
        session_manager = EvaluationSessionManager(logger.current_session_id, watch_path)
        session_manager.start_monitoring()
        
        # Save session manager reference
        import pickle
        with open(f'.session_{logger.current_session_id}.pkl', 'wb') as f:
            pickle.dump(session_manager, f)
        
        console.print("[green]Monitoring started[/green]")
        
    except Exception as e:
        console.print(f"[red]Failed to start monitoring: {e}[/red]")


@cli.command()
def monitor_stop():
    """Stop monitoring for the current session."""
    logger = EvaluationLogger()
    
    if not logger.current_session_id:
        console.print("[red]No active session[/red]")
        return
    
    try:
        import pickle
        import os
        session_file = f'.session_{logger.current_session_id}.pkl'
        
        if not os.path.exists(session_file):
            console.print("[yellow]No active monitoring found[/yellow]")
            return
        
        with open(session_file, 'rb') as f:
            session_manager = pickle.load(f)
        
        summary = session_manager.stop_monitoring()
        console.print("[green]Monitoring stopped[/green]")
        
        # Display summary
        if summary.get('file_changes'):
            console.print(f"Total changes tracked: {summary['file_changes'].get('total_changes', 0)}")
        
        os.remove(session_file)
        
    except Exception as e:
        console.print(f"[red]Failed to stop monitoring: {e}[/red]")


@cli.command()
@click.argument('phase_name', required=False)
def start_phase(phase_name: str):
    """Start a development phase."""
    logger = EvaluationLogger()
    
    if not logger.current_session_id:
        console.print("[red]No active session. Start a session first.[/red]")
        return
    
    # Show standard phases if no phase specified
    if not phase_name:
        phases = StandardizedPhases.get_phase_descriptions()
        
        table = Table(title="Standard Development Phases")
        table.add_column("Phase", style="cyan")
        table.add_column("Description", style="white")
        
        for phase, description in phases.items():
            table.add_row(phase, description)
        
        console.print(table)
        phase_name = Prompt.ask("Select phase name")
    
    try:
        import pickle
        import os
        session_file = f'.session_{logger.current_session_id}.pkl'
        
        if os.path.exists(session_file):
            with open(session_file, 'rb') as f:
                session_manager = pickle.load(f)
            
            session_manager.start_phase(phase_name)
            
            # Save updated session manager
            with open(session_file, 'wb') as f:
                pickle.dump(session_manager, f)
        else:
            console.print("[yellow]No monitoring active. Starting phase without timing tracking.[/yellow]")
            logger.log_milestone(f"phase_start_{phase_name}", f"Started phase: {phase_name}")
        
        console.print(f"[green]Started phase: {phase_name}[/green]")
        
    except Exception as e:
        console.print(f"[red]Failed to start phase: {e}[/red]")


@cli.command()
def complete_phase():
    """Complete the current development phase."""
    logger = EvaluationLogger()
    
    if not logger.current_session_id:
        console.print("[red]No active session. Start a session first.[/red]")
        return
    
    try:
        import pickle
        import os
        session_file = f'.session_{logger.current_session_id}.pkl'
        
        if not os.path.exists(session_file):
            console.print("[yellow]No monitoring active[/yellow]")
            return
        
        with open(session_file, 'rb') as f:
            session_manager = pickle.load(f)
        
        completed_phase = session_manager.complete_current_phase()
        
        if completed_phase:
            console.print(f"[green]Completed phase: {completed_phase}[/green]")
        else:
            console.print("[yellow]No active phase to complete[/yellow]")
        
        # Save updated session manager
        with open(session_file, 'wb') as f:
            pickle.dump(session_manager, f)
        
    except Exception as e:
        console.print(f"[red]Failed to complete phase: {e}[/red]")


@cli.command()
@click.option('--prompt', prompt=True, help='AI prompt text')
@click.option('--response', help='AI response text')
@click.option('--type', 'interaction_type', default='code_generation', help='Interaction type')
@click.option('--rating', type=int, help='Quality rating (1-5)')
@click.option('--helpful', type=bool, help='Was interaction helpful?')
@click.option('--tokens', type=int, help='Tokens used')
@click.option('--cost', type=float, help='Cost estimate')
@click.option('--ai-generated', is_flag=True, help='Mark recent code changes as AI-generated')
def log_ai(prompt: str, response: str, interaction_type: str, rating: int, helpful: bool, tokens: int, cost: float, ai_generated: bool):
    """Log an AI interaction with enhanced tracking."""
    logger = EvaluationLogger()
    
    if not logger.current_session_id:
        console.print("[red]No active session. Start a session first.[/red]")
        return
    
    # Log the interaction
    logger.log_ai_interaction(
        prompt_text=prompt,
        response_text=response,
        interaction_type=interaction_type,
        quality_rating=rating,
        was_helpful=helpful,
        tokens_used=tokens,
        cost_estimate=cost
    )
    
    # Mark code as AI-generated if requested
    if ai_generated:
        try:
            import pickle
            import os
            session_file = f'.session_{logger.current_session_id}.pkl'
            
            if os.path.exists(session_file):
                with open(session_file, 'rb') as f:
                    session_manager = pickle.load(f)
                
                file_path = Prompt.ask("File path for AI-generated code", default="")
                if file_path:
                    session_manager.mark_code_as_ai_generated(file_path)
                    console.print(f"[green]Marked code in {file_path} as AI-generated[/green]")
            
        except Exception as e:
            console.print(f"[yellow]Could not mark code as AI-generated: {e}[/yellow]")
    
    console.print("[green]AI interaction logged[/green]")


@cli.command()
def status():
    """Show comprehensive session status."""
    logger = EvaluationLogger()
    
    if not logger.current_session_id:
        console.print("[red]No active session[/red]")
        return
    
    # Show basic session info
    logger.show_current_session()
    
    # Show monitoring status if available
    try:
        import pickle
        import os
        session_file = f'.session_{logger.current_session_id}.pkl'
        
        if os.path.exists(session_file):
            with open(session_file, 'rb') as f:
                session_manager = pickle.load(f)
            
            summary = session_manager.get_session_summary()
            
            # Display monitoring info
            console.print("\n[blue]Monitoring Status:[/blue]")
            monitoring = summary.get('monitoring', {})
            console.print(f"Active: {'✅' if monitoring.get('is_active') else '❌'}")
            console.print(f"File monitoring: {'✅' if monitoring.get('file_monitoring') else '❌'}")
            console.print(f"Timing tracking: {'✅' if monitoring.get('timing_tracking') else '❌'}")
            
            # Display timing info
            if 'timing' in summary:
                timing = summary['timing']
                console.print(f"\n[blue]Timing:[/blue]")
                console.print(f"Elapsed: {timing.get('elapsed_time_formatted', 'Unknown')}")
                console.print(f"Current phase: {timing.get('current_phase', 'None')}")
                console.print(f"Completed phases: {timing.get('completed_phases', 0)}")
    
    except Exception:
        console.print("\n[yellow]No monitoring data available[/yellow]")


# Include original CLI commands
from .cli import list, milestone, log_change, feedback, backup, info

# Include report commands
from ..analysis.cli_reports import reports
cli.add_command(reports)

if __name__ == '__main__':
    cli()