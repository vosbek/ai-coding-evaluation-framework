"""
Core logging application for manual milestone and interaction tracking.
"""

import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

from sqlalchemy.orm import Session
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.panel import Panel

from ..database.database import get_db, db_manager
from ..database.models import (
    TestSession, AIInteraction, DevelopmentMilestone, 
    DeveloperFeedback, CodeChange, SystemEvent
)


class EvaluationLogger:
    """Main logging interface for AI coding assistant evaluation."""
    
    def __init__(self):
        self.console = Console()
        self.current_session: Optional[TestSession] = None
        self.current_session_id: Optional[int] = None
        
    def start_session(
        self, 
        session_name: str,
        tool_name: str,
        test_case_type: str,
        developer_id: str = None,
        environment_info: Dict[str, Any] = None
    ) -> int:
        """Start a new evaluation session."""
        with next(get_db()) as db:
            session = TestSession(
                session_name=session_name,
                tool_name=tool_name,
                test_case_type=test_case_type,
                developer_id=developer_id,
                start_time=datetime.now(),
                environment_info=json.dumps(environment_info) if environment_info else None,
                status='in_progress'
            )
            
            db.add(session)
            db.commit()
            db.refresh(session)
            
            self.current_session = session
            self.current_session_id = session.id
            
            self.console.print(Panel(
                f"[green]Session Started[/green]\n"
                f"ID: {session.id}\n"
                f"Name: {session_name}\n"
                f"Tool: {tool_name}\n"
                f"Test Type: {test_case_type}",
                title="Evaluation Session"
            ))
            
            return session.id
    
    def end_session(self, notes: str = None) -> None:
        """End the current evaluation session."""
        if not self.current_session_id:
            self.console.print("[red]No active session to end[/red]")
            return
            
        with next(get_db()) as db:
            session = db.query(TestSession).filter(TestSession.id == self.current_session_id).first()
            if session:
                session.end_time = datetime.now()
                session.status = 'completed'
                if notes:
                    session.notes = notes
                db.commit()
                
                duration = (session.end_time - session.start_time).total_seconds() / 60
                self.console.print(Panel(
                    f"[green]Session Completed[/green]\n"
                    f"Duration: {duration:.1f} minutes\n"
                    f"Notes: {notes or 'None'}",
                    title="Session Complete"
                ))
        
        self.current_session = None
        self.current_session_id = None
    
    def log_ai_interaction(
        self,
        prompt_text: str,
        response_text: str = None,
        interaction_type: str = 'code_generation',
        quality_rating: int = None,
        was_helpful: bool = None,
        tokens_used: int = None,
        cost_estimate: float = None,
        developer_notes: str = None
    ) -> None:
        """Log an AI interaction."""
        if not self.current_session_id:
            self.console.print("[red]No active session. Start a session first.[/red]")
            return
        
        with next(get_db()) as db:
            # Get next sequence number
            max_seq = db.query(AIInteraction.interaction_sequence).filter(
                AIInteraction.session_id == self.current_session_id
            ).order_by(AIInteraction.interaction_sequence.desc()).first()
            
            next_seq = (max_seq[0] + 1) if max_seq else 1
            
            interaction = AIInteraction(
                session_id=self.current_session_id,
                interaction_sequence=next_seq,
                timestamp=datetime.now(),
                prompt_text=prompt_text,
                response_text=response_text,
                interaction_type=interaction_type,
                quality_rating=quality_rating,
                was_helpful=was_helpful,
                tokens_used=tokens_used,
                cost_estimate=cost_estimate,
                developer_notes=developer_notes
            )
            
            db.add(interaction)
            db.commit()
            
            self.console.print(f"[blue]AI Interaction #{next_seq} logged[/blue]")
    
    def log_milestone(
        self,
        milestone_name: str,
        description: str = None,
        developer_notes: str = None
    ) -> None:
        """Log a development milestone."""
        if not self.current_session_id:
            self.console.print("[red]No active session. Start a session first.[/red]")
            return
        
        with next(get_db()) as db:
            # Calculate elapsed time
            session = db.query(TestSession).filter(TestSession.id == self.current_session_id).first()
            elapsed_minutes = (datetime.now() - session.start_time).total_seconds() / 60
            
            milestone = DevelopmentMilestone(
                session_id=self.current_session_id,
                milestone_name=milestone_name,
                timestamp=datetime.now(),
                description=description,
                time_elapsed_minutes=int(elapsed_minutes),
                developer_notes=developer_notes
            )
            
            db.add(milestone)
            db.commit()
            
            self.console.print(f"[yellow]Milestone '{milestone_name}' logged at {elapsed_minutes:.1f} minutes[/yellow]")
    
    def log_code_change(
        self,
        file_path: str,
        change_type: str,
        lines_added: int = 0,
        lines_deleted: int = 0,
        lines_modified: int = 0,
        git_commit_hash: str = None,
        diff_content: str = None,
        ai_generated: bool = False
    ) -> None:
        """Log a code change."""
        if not self.current_session_id:
            self.console.print("[red]No active session. Start a session first.[/red]")
            return
        
        with next(get_db()) as db:
            change = CodeChange(
                session_id=self.current_session_id,
                file_path=file_path,
                change_type=change_type,
                timestamp=datetime.now(),
                lines_added=lines_added,
                lines_deleted=lines_deleted,
                lines_modified=lines_modified,
                git_commit_hash=git_commit_hash,
                diff_content=diff_content,
                ai_generated=ai_generated
            )
            
            db.add(change)
            db.commit()
            
            self.console.print(f"[cyan]Code change logged: {change_type} {file_path}[/cyan]")
    
    def log_developer_feedback(
        self,
        ease_of_use_rating: int,
        code_quality_rating: int,
        productivity_rating: int,
        learning_curve_rating: int,
        overall_satisfaction: int,
        would_recommend: bool,
        likes: str = None,
        dislikes: str = None,
        suggestions: str = None,
        additional_comments: str = None
    ) -> None:
        """Log developer feedback for the current session."""
        if not self.current_session_id:
            self.console.print("[red]No active session. Start a session first.[/red]")
            return
        
        with next(get_db()) as db:
            feedback = DeveloperFeedback(
                session_id=self.current_session_id,
                timestamp=datetime.now(),
                ease_of_use_rating=ease_of_use_rating,
                code_quality_rating=code_quality_rating,
                productivity_rating=productivity_rating,
                learning_curve_rating=learning_curve_rating,
                overall_satisfaction=overall_satisfaction,
                would_recommend=would_recommend,
                likes=likes,
                dislikes=dislikes,
                suggestions=suggestions,
                additional_comments=additional_comments
            )
            
            db.add(feedback)
            db.commit()
            
            self.console.print("[green]Developer feedback logged[/green]")
    
    def show_current_session(self) -> None:
        """Display information about the current session."""
        if not self.current_session_id:
            self.console.print("[red]No active session[/red]")
            return
        
        with next(get_db()) as db:
            session = db.query(TestSession).filter(TestSession.id == self.current_session_id).first()
            
            if not session:
                self.console.print("[red]Session not found[/red]")
                return
            
            # Get session statistics
            interactions_count = db.query(AIInteraction).filter(
                AIInteraction.session_id == self.current_session_id
            ).count()
            
            milestones_count = db.query(DevelopmentMilestone).filter(
                DevelopmentMilestone.session_id == self.current_session_id
            ).count()
            
            changes_count = db.query(CodeChange).filter(
                CodeChange.session_id == self.current_session_id
            ).count()
            
            # Calculate duration
            end_time = session.end_time or datetime.now()
            duration = (end_time - session.start_time).total_seconds() / 60
            
            table = Table(title=f"Session #{session.id}: {session.session_name}")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="magenta")
            
            table.add_row("Tool", session.tool_name)
            table.add_row("Test Case Type", session.test_case_type)
            table.add_row("Developer", session.developer_id or "Not specified")
            table.add_row("Status", session.status)
            table.add_row("Duration", f"{duration:.1f} minutes")
            table.add_row("AI Interactions", str(interactions_count))
            table.add_row("Milestones", str(milestones_count))
            table.add_row("Code Changes", str(changes_count))
            
            self.console.print(table)
    
    def list_sessions(self, limit: int = 10) -> None:
        """List recent evaluation sessions."""
        with next(get_db()) as db:
            sessions = db.query(TestSession).order_by(
                TestSession.created_at.desc()
            ).limit(limit).all()
            
            if not sessions:
                self.console.print("[yellow]No sessions found[/yellow]")
                return
            
            table = Table(title="Recent Evaluation Sessions")
            table.add_column("ID", justify="right", style="cyan")
            table.add_column("Name", style="green")
            table.add_column("Tool", style="blue")
            table.add_column("Type", style="yellow")
            table.add_column("Status", style="magenta")
            table.add_column("Start Time", style="dim")
            
            for session in sessions:
                table.add_row(
                    str(session.id),
                    session.session_name,
                    session.tool_name,
                    session.test_case_type,
                    session.status,
                    session.start_time.strftime("%Y-%m-%d %H:%M")
                )
            
            self.console.print(table)


# Interactive CLI functions
def interactive_start_session(logger: EvaluationLogger) -> None:
    """Interactive session start."""
    console = Console()
    
    session_name = Prompt.ask("Session name")
    tool_name = Prompt.ask("AI tool", choices=["cursor", "github_copilot", "other"])
    if tool_name == "other":
        tool_name = Prompt.ask("Enter tool name")
    
    test_case_type = Prompt.ask("Test case type", choices=["bug_fix", "new_feature", "refactoring", "other"])
    if test_case_type == "other":
        test_case_type = Prompt.ask("Enter test case type")
    
    developer_id = Prompt.ask("Developer ID (optional)", default="")
    
    env_info = {}
    if Confirm.ask("Add environment information?"):
        env_info["ide"] = Prompt.ask("IDE/Editor", default="")
        env_info["os"] = Prompt.ask("Operating System", default="")
        env_info["repo_url"] = Prompt.ask("Repository URL", default="")
    
    session_id = logger.start_session(
        session_name=session_name,
        tool_name=tool_name,
        test_case_type=test_case_type,
        developer_id=developer_id if developer_id else None,
        environment_info=env_info if env_info else None
    )
    
    return session_id


def interactive_log_interaction(logger: EvaluationLogger) -> None:
    """Interactive AI interaction logging."""
    if not logger.current_session_id:
        logger.console.print("[red]No active session. Start a session first.[/red]")
        return
    
    prompt_text = Prompt.ask("AI Prompt")
    response_text = Prompt.ask("AI Response (optional)", default="")
    
    interaction_type = Prompt.ask(
        "Interaction type", 
        choices=["code_generation", "explanation", "debug", "refactor", "other"],
        default="code_generation"
    )
    
    if Confirm.ask("Rate the interaction quality?"):
        quality_rating = int(Prompt.ask("Quality rating (1-5)", choices=["1", "2", "3", "4", "5"]))
        was_helpful = Confirm.ask("Was this interaction helpful?")
    else:
        quality_rating = None
        was_helpful = None
    
    developer_notes = Prompt.ask("Developer notes (optional)", default="")
    
    logger.log_ai_interaction(
        prompt_text=prompt_text,
        response_text=response_text if response_text else None,
        interaction_type=interaction_type,
        quality_rating=quality_rating,
        was_helpful=was_helpful,
        developer_notes=developer_notes if developer_notes else None
    )