"""
Command-line interface for the AI Coding Assistant Evaluation Framework.
"""

import click
from rich.console import Console
from rich.prompt import Prompt, Confirm

from ..database.database import init_database, db_manager
from .logger import EvaluationLogger, interactive_start_session, interactive_log_interaction


console = Console()
logger = EvaluationLogger()


@click.group()
@click.version_option()
def cli():
    """AI Coding Assistant Evaluation Framework - Logging Interface"""
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
def start():
    """Start a new evaluation session interactively."""
    interactive_start_session(logger)


@cli.command()
@click.option('--name', prompt=True, help='Session name')
@click.option('--tool', prompt=True, help='AI tool name (cursor, github_copilot, etc.)')
@click.option('--type', 'test_type', prompt=True, help='Test case type (bug_fix, new_feature, refactoring)')
@click.option('--developer', help='Developer ID')
def start_session(name: str, tool: str, test_type: str, developer: str):
    """Start a new evaluation session with parameters."""
    session_id = logger.start_session(
        session_name=name,
        tool_name=tool,
        test_case_type=test_type,
        developer_id=developer
    )
    console.print(f"[green]Started session {session_id}[/green]")


@cli.command()
@click.option('--notes', help='Session completion notes')
def end():
    """End the current evaluation session."""
    if not logger.current_session_id:
        console.print("[red]No active session to end[/red]")
        return
    
    if not notes:
        notes = Prompt.ask("Session completion notes (optional)", default="")
    
    logger.end_session(notes if notes else None)


@cli.command()
def status():
    """Show current session status."""
    logger.show_current_session()


@cli.command()
@click.option('--limit', default=10, help='Number of sessions to show')
def list():
    """List recent evaluation sessions."""
    logger.list_sessions(limit=limit)


@cli.command()
def log_interaction():
    """Log an AI interaction interactively."""
    interactive_log_interaction(logger)


@cli.command()
@click.option('--prompt', prompt=True, help='AI prompt text')
@click.option('--response', help='AI response text')
@click.option('--type', 'interaction_type', default='code_generation', help='Interaction type')
@click.option('--rating', type=int, help='Quality rating (1-5)')
@click.option('--helpful', type=bool, help='Was interaction helpful?')
@click.option('--notes', help='Developer notes')
def log_ai(prompt: str, response: str, interaction_type: str, rating: int, helpful: bool, notes: str):
    """Log an AI interaction with parameters."""
    logger.log_ai_interaction(
        prompt_text=prompt,
        response_text=response,
        interaction_type=interaction_type,
        quality_rating=rating,
        was_helpful=helpful,
        developer_notes=notes
    )


@cli.command()
@click.option('--name', prompt=True, help='Milestone name')
@click.option('--description', help='Milestone description')
@click.option('--notes', help='Developer notes')
def milestone(name: str, description: str, notes: str):
    """Log a development milestone."""
    logger.log_milestone(
        milestone_name=name,
        description=description,
        developer_notes=notes
    )


@cli.command()
@click.option('--file', prompt=True, help='File path')
@click.option('--type', 'change_type', prompt=True, help='Change type (create, modify, delete, rename)')
@click.option('--added', type=int, default=0, help='Lines added')
@click.option('--deleted', type=int, default=0, help='Lines deleted')
@click.option('--modified', type=int, default=0, help='Lines modified')
@click.option('--ai-generated/--manual', default=False, help='Was this change AI-generated?')
def log_change(file: str, change_type: str, added: int, deleted: int, modified: int, ai_generated: bool):
    """Log a code change."""
    logger.log_code_change(
        file_path=file,
        change_type=change_type,
        lines_added=added,
        lines_deleted=deleted,
        lines_modified=modified,
        ai_generated=ai_generated
    )


@cli.command()
def feedback():
    """Log developer feedback for the current session."""
    if not logger.current_session_id:
        console.print("[red]No active session. Start a session first.[/red]")
        return
    
    console.print("[blue]Developer Feedback Form[/blue]")
    console.print("Please rate each aspect from 1 (poor) to 5 (excellent)")
    
    ease_of_use = int(Prompt.ask("Ease of use rating", choices=["1", "2", "3", "4", "5"]))
    code_quality = int(Prompt.ask("Code quality rating", choices=["1", "2", "3", "4", "5"]))
    productivity = int(Prompt.ask("Productivity rating", choices=["1", "2", "3", "4", "5"]))
    learning_curve = int(Prompt.ask("Learning curve rating", choices=["1", "2", "3", "4", "5"]))
    overall = int(Prompt.ask("Overall satisfaction", choices=["1", "2", "3", "4", "5"]))
    
    would_recommend = Confirm.ask("Would you recommend this tool?")
    
    likes = Prompt.ask("What did you like? (optional)", default="")
    dislikes = Prompt.ask("What didn't you like? (optional)", default="")
    suggestions = Prompt.ask("Suggestions for improvement? (optional)", default="")
    comments = Prompt.ask("Additional comments? (optional)", default="")
    
    logger.log_developer_feedback(
        ease_of_use_rating=ease_of_use,
        code_quality_rating=code_quality,
        productivity_rating=productivity,
        learning_curve_rating=learning_curve,
        overall_satisfaction=overall,
        would_recommend=would_recommend,
        likes=likes if likes else None,
        dislikes=dislikes if dislikes else None,
        suggestions=suggestions if suggestions else None,
        additional_comments=comments if comments else None
    )


@cli.command()
def backup():
    """Create a database backup."""
    try:
        backup_path = db_manager.backup_database()
        console.print(f"[green]Database backed up to: {backup_path}[/green]")
    except Exception as e:
        console.print(f"[red]Backup failed: {e}[/red]")


@cli.command()
def info():
    """Show database information."""
    try:
        info = db_manager.get_database_info()
        console.print(f"[blue]Database: {info['database_path']}[/blue]")
        console.print(f"[blue]Total tables: {info['total_tables']}[/blue]")
        
        for table, count in info['tables'].items():
            console.print(f"  {table}: {count} rows")
    except Exception as e:
        console.print(f"[red]Failed to get database info: {e}[/red]")


if __name__ == '__main__':
    cli()