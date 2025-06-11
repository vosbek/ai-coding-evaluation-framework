"""
Core metrics calculation engine for AI coding assistant evaluation.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from collections import defaultdict
import statistics

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from ..database.database import get_db
from ..database.models import (
    TestSession, AIInteraction, CodeChange, QualityMetric,
    DevelopmentMilestone, DeveloperFeedback, BuildResult
)


@dataclass
class SessionMetrics:
    """Comprehensive metrics for a single evaluation session."""
    session_id: int
    session_name: str
    tool_name: str
    test_case_type: str
    developer_id: str
    
    # Timing metrics
    total_duration_minutes: float
    start_time: datetime
    end_time: datetime
    
    # Code metrics
    total_code_changes: int
    files_created: int
    files_modified: int
    files_deleted: int
    lines_added: int
    lines_deleted: int
    lines_modified: int
    
    # AI interaction metrics
    total_ai_interactions: int
    ai_interactions_per_hour: float
    average_quality_rating: float
    helpful_interactions_percentage: float
    total_tokens_used: int
    total_cost_estimate: float
    
    # Development phase metrics
    total_phases: int
    phase_durations: Dict[str, float]  # phase_name -> duration_minutes
    phase_ai_usage: Dict[str, int]     # phase_name -> interaction_count
    
    # Productivity metrics
    lines_per_minute: float
    files_per_hour: float
    commits_per_hour: float
    ai_assistance_ratio: float  # AI interactions / total actions
    
    # Quality metrics
    build_success_rate: float
    test_pass_rate: float
    code_quality_score: float
    
    # Developer feedback
    satisfaction_rating: Optional[float]
    ease_of_use_rating: Optional[float]
    productivity_rating: Optional[float]
    would_recommend: Optional[bool]


@dataclass
class ComparisonMetrics:
    """Comparative analysis between two tools."""
    tool_a_name: str
    tool_b_name: str
    test_case_type: str
    
    # Performance comparison
    speed_improvement_percentage: float  # Positive means tool_a is faster
    productivity_improvement_percentage: float
    code_quality_improvement_percentage: float
    
    # AI usage comparison
    ai_interaction_difference: float
    token_usage_difference: float
    cost_difference: float
    
    # Developer preference
    satisfaction_difference: float
    preference_winner: str  # tool_a, tool_b, or tie
    
    # Statistical significance
    sample_size_a: int
    sample_size_b: int
    confidence_level: float


class MetricsCalculator:
    """Calculates comprehensive metrics for evaluation sessions."""
    
    def __init__(self):
        pass
    
    def calculate_session_metrics(self, session_id: int) -> Optional[SessionMetrics]:
        """Calculate comprehensive metrics for a single session."""
        try:
            with next(get_db()) as db:
                # Get session info
                session = db.query(TestSession).filter(TestSession.id == session_id).first()
                if not session:
                    return None
                
                # Calculate timing metrics
                timing_metrics = self._calculate_timing_metrics(db, session)
                
                # Calculate code metrics
                code_metrics = self._calculate_code_metrics(db, session_id)
                
                # Calculate AI metrics
                ai_metrics = self._calculate_ai_metrics(db, session_id)
                
                # Calculate phase metrics
                phase_metrics = self._calculate_phase_metrics(db, session_id)
                
                # Calculate productivity metrics
                productivity_metrics = self._calculate_productivity_metrics(
                    timing_metrics, code_metrics, ai_metrics
                )
                
                # Calculate quality metrics
                quality_metrics = self._calculate_quality_metrics(db, session_id)
                
                # Get developer feedback
                feedback_metrics = self._calculate_feedback_metrics(db, session_id)
                
                return SessionMetrics(
                    session_id=session_id,
                    session_name=session.session_name,
                    tool_name=session.tool_name,
                    test_case_type=session.test_case_type,
                    developer_id=session.developer_id or "unknown",
                    
                    # Timing
                    total_duration_minutes=timing_metrics['duration_minutes'],
                    start_time=session.start_time,
                    end_time=session.end_time or datetime.now(),
                    
                    # Code
                    total_code_changes=code_metrics['total_changes'],
                    files_created=code_metrics['files_created'],
                    files_modified=code_metrics['files_modified'],
                    files_deleted=code_metrics['files_deleted'],
                    lines_added=code_metrics['lines_added'],
                    lines_deleted=code_metrics['lines_deleted'],
                    lines_modified=code_metrics['lines_modified'],
                    
                    # AI
                    total_ai_interactions=ai_metrics['total_interactions'],
                    ai_interactions_per_hour=ai_metrics['interactions_per_hour'],
                    average_quality_rating=ai_metrics['avg_quality_rating'],
                    helpful_interactions_percentage=ai_metrics['helpful_percentage'],
                    total_tokens_used=ai_metrics['total_tokens'],
                    total_cost_estimate=ai_metrics['total_cost'],
                    
                    # Phases
                    total_phases=phase_metrics['total_phases'],
                    phase_durations=phase_metrics['phase_durations'],
                    phase_ai_usage=phase_metrics['phase_ai_usage'],
                    
                    # Productivity
                    lines_per_minute=productivity_metrics['lines_per_minute'],
                    files_per_hour=productivity_metrics['files_per_hour'],
                    commits_per_hour=productivity_metrics['commits_per_hour'],
                    ai_assistance_ratio=productivity_metrics['ai_assistance_ratio'],
                    
                    # Quality
                    build_success_rate=quality_metrics['build_success_rate'],
                    test_pass_rate=quality_metrics['test_pass_rate'],
                    code_quality_score=quality_metrics['code_quality_score'],
                    
                    # Feedback
                    satisfaction_rating=feedback_metrics.get('satisfaction_rating'),
                    ease_of_use_rating=feedback_metrics.get('ease_of_use_rating'),
                    productivity_rating=feedback_metrics.get('productivity_rating'),
                    would_recommend=feedback_metrics.get('would_recommend')
                )
                
        except Exception as e:
            print(f"Error calculating session metrics: {e}")
            return None
    
    def _calculate_timing_metrics(self, db: Session, session: TestSession) -> Dict[str, float]:
        """Calculate timing-related metrics."""
        end_time = session.end_time or datetime.now()
        duration = (end_time - session.start_time).total_seconds() / 60  # minutes
        
        return {
            'duration_minutes': duration,
            'duration_hours': duration / 60
        }
    
    def _calculate_code_metrics(self, db: Session, session_id: int) -> Dict[str, int]:
        """Calculate code change metrics."""
        changes = db.query(CodeChange).filter(CodeChange.session_id == session_id).all()
        
        metrics = {
            'total_changes': len(changes),
            'files_created': len([c for c in changes if c.change_type == 'create']),
            'files_modified': len([c for c in changes if c.change_type == 'modify']),
            'files_deleted': len([c for c in changes if c.change_type == 'delete']),
            'lines_added': sum(c.lines_added or 0 for c in changes),
            'lines_deleted': sum(c.lines_deleted or 0 for c in changes),
            'lines_modified': sum(c.lines_modified or 0 for c in changes),
            'unique_files': len(set(c.file_path for c in changes)),
            'ai_generated_changes': len([c for c in changes if c.ai_generated])
        }
        
        return metrics
    
    def _calculate_ai_metrics(self, db: Session, session_id: int) -> Dict[str, float]:
        """Calculate AI interaction metrics."""
        interactions = db.query(AIInteraction).filter(
            AIInteraction.session_id == session_id
        ).all()
        
        if not interactions:
            return {
                'total_interactions': 0,
                'interactions_per_hour': 0,
                'avg_quality_rating': 0,
                'helpful_percentage': 0,
                'total_tokens': 0,
                'total_cost': 0
            }
        
        # Get session duration for rate calculations
        session = db.query(TestSession).filter(TestSession.id == session_id).first()
        duration_hours = self._calculate_timing_metrics(db, session)['duration_hours']
        
        # Calculate metrics
        quality_ratings = [i.quality_rating for i in interactions if i.quality_rating]
        helpful_count = len([i for i in interactions if i.was_helpful is True])
        total_tokens = sum(i.tokens_used or 0 for i in interactions)
        total_cost = sum(float(i.cost_estimate or 0) for i in interactions)
        
        return {
            'total_interactions': len(interactions),
            'interactions_per_hour': len(interactions) / duration_hours if duration_hours > 0 else 0,
            'avg_quality_rating': statistics.mean(quality_ratings) if quality_ratings else 0,
            'helpful_percentage': (helpful_count / len(interactions)) * 100 if interactions else 0,
            'total_tokens': total_tokens,
            'total_cost': total_cost
        }
    
    def _calculate_phase_metrics(self, db: Session, session_id: int) -> Dict[str, Any]:
        """Calculate development phase metrics."""
        milestones = db.query(DevelopmentMilestone).filter(
            DevelopmentMilestone.session_id == session_id
        ).order_by(DevelopmentMilestone.timestamp).all()
        
        phase_durations = {}
        phase_ai_usage = defaultdict(int)
        
        # Calculate phase durations from milestones
        phase_starts = {}
        for milestone in milestones:
            if milestone.milestone_name.startswith('phase_start_'):
                phase_name = milestone.milestone_name.replace('phase_start_', '')
                phase_starts[phase_name] = milestone.timestamp
            elif milestone.milestone_name.startswith('phase_complete_'):
                phase_name = milestone.milestone_name.replace('phase_complete_', '')
                if phase_name in phase_starts:
                    duration = (milestone.timestamp - phase_starts[phase_name]).total_seconds() / 60
                    phase_durations[phase_name] = duration
        
        # Calculate AI usage per phase
        for phase_name, start_time in phase_starts.items():
            # Find end time (either completion or next phase start)
            end_time = None
            for milestone in milestones:
                if milestone.milestone_name == f'phase_complete_{phase_name}':
                    end_time = milestone.timestamp
                    break
            
            if end_time:
                ai_count = db.query(AIInteraction).filter(
                    AIInteraction.session_id == session_id,
                    AIInteraction.timestamp >= start_time,
                    AIInteraction.timestamp <= end_time
                ).count()
                phase_ai_usage[phase_name] = ai_count
        
        return {
            'total_phases': len(phase_durations),
            'phase_durations': phase_durations,
            'phase_ai_usage': dict(phase_ai_usage)
        }
    
    def _calculate_productivity_metrics(self, timing: Dict, code: Dict, ai: Dict) -> Dict[str, float]:
        """Calculate productivity metrics."""
        duration_minutes = timing['duration_minutes']
        duration_hours = timing['duration_hours']
        
        total_actions = code['total_changes'] + ai['total_interactions']
        
        return {
            'lines_per_minute': code['lines_added'] / duration_minutes if duration_minutes > 0 else 0,
            'files_per_hour': code['unique_files'] / duration_hours if duration_hours > 0 else 0,
            'commits_per_hour': 0,  # Would need git commit data
            'ai_assistance_ratio': ai['total_interactions'] / total_actions if total_actions > 0 else 0
        }
    
    def _calculate_quality_metrics(self, db: Session, session_id: int) -> Dict[str, float]:
        """Calculate code quality metrics."""
        # Get build results
        builds = db.query(BuildResult).filter(BuildResult.session_id == session_id).all()
        
        if not builds:
            return {
                'build_success_rate': 0,
                'test_pass_rate': 0,
                'code_quality_score': 0
            }
        
        successful_builds = len([b for b in builds if b.success])
        build_success_rate = (successful_builds / len(builds)) * 100
        
        # Get quality metrics
        quality_metrics = db.query(QualityMetric).filter(
            QualityMetric.session_id == session_id
        ).all()
        
        # Calculate test pass rate
        test_builds = [b for b in builds if b.build_type == 'test']
        test_pass_rate = 0
        if test_builds:
            passed_tests = sum(b.tests_passed or 0 for b in test_builds)
            total_tests = sum((b.tests_passed or 0) + (b.tests_failed or 0) for b in test_builds)
            test_pass_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        # Calculate overall code quality score (simplified)
        code_quality_score = (build_success_rate + test_pass_rate) / 2
        
        return {
            'build_success_rate': build_success_rate,
            'test_pass_rate': test_pass_rate,
            'code_quality_score': code_quality_score
        }
    
    def _calculate_feedback_metrics(self, db: Session, session_id: int) -> Dict[str, Any]:
        """Calculate developer feedback metrics."""
        feedback = db.query(DeveloperFeedback).filter(
            DeveloperFeedback.session_id == session_id
        ).first()
        
        if not feedback:
            return {}
        
        return {
            'satisfaction_rating': feedback.overall_satisfaction,
            'ease_of_use_rating': feedback.ease_of_use_rating,
            'productivity_rating': feedback.productivity_rating,
            'would_recommend': feedback.would_recommend
        }
    
    def calculate_tool_comparison(self, tool_a: str, tool_b: str, test_case_type: str = None) -> Optional[ComparisonMetrics]:
        """Calculate comparative metrics between two AI tools."""
        try:
            with next(get_db()) as db:
                # Get sessions for both tools
                query_a = db.query(TestSession).filter(TestSession.tool_name == tool_a)
                query_b = db.query(TestSession).filter(TestSession.tool_name == tool_b)
                
                if test_case_type:
                    query_a = query_a.filter(TestSession.test_case_type == test_case_type)
                    query_b = query_b.filter(TestSession.test_case_type == test_case_type)
                
                sessions_a = query_a.filter(TestSession.status == 'completed').all()
                sessions_b = query_b.filter(TestSession.status == 'completed').all()
                
                if not sessions_a or not sessions_b:
                    return None
                
                # Calculate metrics for each tool
                metrics_a = [self.calculate_session_metrics(s.id) for s in sessions_a]
                metrics_b = [self.calculate_session_metrics(s.id) for s in sessions_b]
                
                # Filter out None results
                metrics_a = [m for m in metrics_a if m]
                metrics_b = [m for m in metrics_b if m]
                
                if not metrics_a or not metrics_b:
                    return None
                
                # Calculate averages
                avg_duration_a = statistics.mean([m.total_duration_minutes for m in metrics_a])
                avg_duration_b = statistics.mean([m.total_duration_minutes for m in metrics_b])
                
                avg_productivity_a = statistics.mean([m.lines_per_minute for m in metrics_a])
                avg_productivity_b = statistics.mean([m.lines_per_minute for m in metrics_b])
                
                avg_quality_a = statistics.mean([m.code_quality_score for m in metrics_a])
                avg_quality_b = statistics.mean([m.code_quality_score for m in metrics_b])
                
                avg_satisfaction_a = statistics.mean([m.satisfaction_rating for m in metrics_a if m.satisfaction_rating])
                avg_satisfaction_b = statistics.mean([m.satisfaction_rating for m in metrics_b if m.satisfaction_rating])
                
                # Calculate comparisons (positive = tool_a is better)
                speed_improvement = ((avg_duration_b - avg_duration_a) / avg_duration_b) * 100 if avg_duration_b > 0 else 0
                productivity_improvement = ((avg_productivity_a - avg_productivity_b) / avg_productivity_b) * 100 if avg_productivity_b > 0 else 0
                quality_improvement = ((avg_quality_a - avg_quality_b) / avg_quality_b) * 100 if avg_quality_b > 0 else 0
                satisfaction_difference = avg_satisfaction_a - avg_satisfaction_b
                
                # Determine preference winner
                preference_winner = "tie"
                if satisfaction_difference > 0.5:
                    preference_winner = tool_a
                elif satisfaction_difference < -0.5:
                    preference_winner = tool_b
                
                return ComparisonMetrics(
                    tool_a_name=tool_a,
                    tool_b_name=tool_b,
                    test_case_type=test_case_type or "all",
                    speed_improvement_percentage=speed_improvement,
                    productivity_improvement_percentage=productivity_improvement,
                    code_quality_improvement_percentage=quality_improvement,
                    ai_interaction_difference=0,  # TODO: Implement
                    token_usage_difference=0,     # TODO: Implement
                    cost_difference=0,            # TODO: Implement
                    satisfaction_difference=satisfaction_difference,
                    preference_winner=preference_winner,
                    sample_size_a=len(metrics_a),
                    sample_size_b=len(metrics_b),
                    confidence_level=0.95         # TODO: Calculate actual confidence
                )
                
        except Exception as e:
            print(f"Error calculating tool comparison: {e}")
            return None
    
    def get_session_summary_stats(self, tool_name: str = None, test_case_type: str = None) -> Dict[str, Any]:
        """Get summary statistics across multiple sessions."""
        try:
            with next(get_db()) as db:
                query = db.query(TestSession).filter(TestSession.status == 'completed')
                
                if tool_name:
                    query = query.filter(TestSession.tool_name == tool_name)
                if test_case_type:
                    query = query.filter(TestSession.test_case_type == test_case_type)
                
                sessions = query.all()
                
                if not sessions:
                    return {}
                
                # Calculate metrics for all sessions
                all_metrics = []
                for session in sessions:
                    metrics = self.calculate_session_metrics(session.id)
                    if metrics:
                        all_metrics.append(metrics)
                
                if not all_metrics:
                    return {}
                
                # Calculate summary statistics
                durations = [m.total_duration_minutes for m in all_metrics]
                productivities = [m.lines_per_minute for m in all_metrics]
                qualities = [m.code_quality_score for m in all_metrics]
                satisfactions = [m.satisfaction_rating for m in all_metrics if m.satisfaction_rating]
                
                return {
                    'total_sessions': len(all_metrics),
                    'duration': {
                        'mean': statistics.mean(durations),
                        'median': statistics.median(durations),
                        'min': min(durations),
                        'max': max(durations),
                        'std_dev': statistics.stdev(durations) if len(durations) > 1 else 0
                    },
                    'productivity': {
                        'mean': statistics.mean(productivities),
                        'median': statistics.median(productivities),
                        'min': min(productivities),
                        'max': max(productivities)
                    },
                    'quality': {
                        'mean': statistics.mean(qualities),
                        'median': statistics.median(qualities),
                        'min': min(qualities),
                        'max': max(qualities)
                    },
                    'satisfaction': {
                        'mean': statistics.mean(satisfactions) if satisfactions else 0,
                        'count': len(satisfactions)
                    }
                }
                
        except Exception as e:
            print(f"Error calculating summary stats: {e}")
            return {}