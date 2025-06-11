"""
SQLAlchemy models for the AI Coding Assistant Evaluation Framework.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, 
    ForeignKey, Numeric, CheckConstraint, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class TestSession(Base):
    """Represents individual evaluation runs with AI tools."""
    __tablename__ = 'test_sessions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_name = Column(String(255), nullable=False)
    tool_name = Column(String(100), nullable=False)  # 'cursor', 'github_copilot', etc.
    test_case_type = Column(String(50), nullable=False)  # 'bug_fix', 'new_feature', 'refactoring'
    developer_id = Column(String(100))
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    status = Column(String(20), default='in_progress')  # 'in_progress', 'completed', 'failed'
    environment_info = Column(Text)  # JSON blob with environment details
    notes = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    ai_interactions = relationship("AIInteraction", back_populates="session")
    code_changes = relationship("CodeChange", back_populates="session")
    quality_metrics = relationship("QualityMetric", back_populates="session")
    build_results = relationship("BuildResult", back_populates="session")
    developer_feedback = relationship("DeveloperFeedback", back_populates="session")
    milestones = relationship("DevelopmentMilestone", back_populates="session")
    
    # Indexes
    __table_args__ = (
        Index('idx_test_sessions_tool_type', 'tool_name', 'test_case_type'),
        Index('idx_test_sessions_status', 'status'),
    )


class TestCase(Base):
    """Defines the scenarios being evaluated."""
    __tablename__ = 'test_cases'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)  # 'bug_fix', 'new_feature', 'refactoring'
    description = Column(Text, nullable=False)
    requirements = Column(Text, nullable=False)  # Detailed requirements/acceptance criteria
    standardized_prompts = Column(Text)  # JSON array of prompts to use
    success_criteria = Column(Text)  # JSON array of success criteria
    estimated_duration_minutes = Column(Integer)
    difficulty_level = Column(String(20))  # 'easy', 'medium', 'hard'
    golden_repo_path = Column(String(500))
    baseline_branch = Column(String(100))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class AIInteraction(Base):
    """Tracks each prompt/response cycle during testing."""
    __tablename__ = 'ai_interactions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey('test_sessions.id'), nullable=False)
    interaction_sequence = Column(Integer, nullable=False)  # Order within session
    timestamp = Column(DateTime, nullable=False)
    prompt_text = Column(Text, nullable=False)
    response_text = Column(Text)
    interaction_type = Column(String(50))  # 'code_generation', 'explanation', 'debug', 'refactor'
    quality_rating = Column(Integer, CheckConstraint('quality_rating >= 1 AND quality_rating <= 5'))
    was_helpful = Column(Boolean)
    tokens_used = Column(Integer)
    cost_estimate = Column(Numeric(10, 4))
    developer_notes = Column(Text)
    
    # Relationships
    session = relationship("TestSession", back_populates="ai_interactions")
    
    # Indexes
    __table_args__ = (
        Index('idx_ai_interactions_session', 'session_id'),
    )


class CodeChange(Base):
    """Tracks file modifications during testing."""
    __tablename__ = 'code_changes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey('test_sessions.id'), nullable=False)
    file_path = Column(String(1000), nullable=False)
    change_type = Column(String(20), nullable=False)  # 'create', 'modify', 'delete', 'rename'
    timestamp = Column(DateTime, nullable=False)
    lines_added = Column(Integer, default=0)
    lines_deleted = Column(Integer, default=0)
    lines_modified = Column(Integer, default=0)
    git_commit_hash = Column(String(40))
    diff_content = Column(Text)  # Store the actual diff
    ai_generated = Column(Boolean, default=False)  # Was this change AI-suggested?
    
    # Relationships
    session = relationship("TestSession", back_populates="code_changes")
    
    # Indexes
    __table_args__ = (
        Index('idx_code_changes_session', 'session_id'),
    )


class QualityMetric(Base):
    """Captures before/after code quality measurements."""
    __tablename__ = 'quality_metrics'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey('test_sessions.id'), nullable=False)
    measurement_point = Column(String(20), nullable=False)  # 'baseline', 'completion'
    timestamp = Column(DateTime, nullable=False)
    
    # Code complexity metrics
    cyclomatic_complexity = Column(Numeric(10, 2))
    lines_of_code = Column(Integer)
    test_coverage_percentage = Column(Numeric(5, 2))
    
    # Quality scores (from tools like SonarQube)
    maintainability_rating = Column(String(5))
    reliability_rating = Column(String(5))
    security_rating = Column(String(5))
    technical_debt_minutes = Column(Integer)
    code_smells = Column(Integer)
    bugs = Column(Integer)
    vulnerabilities = Column(Integer)
    
    # Build and test results
    build_success = Column(Boolean)
    tests_passed = Column(Integer)
    tests_failed = Column(Integer)
    build_time_seconds = Column(Integer)
    
    # Additional metrics as JSON
    additional_metrics = Column(Text)  # JSON blob for extensibility
    
    # Relationships
    session = relationship("TestSession", back_populates="quality_metrics")
    
    # Indexes
    __table_args__ = (
        Index('idx_quality_metrics_session', 'session_id'),
    )


class BuildResult(Base):
    """Tracks compilation and test execution."""
    __tablename__ = 'build_results'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey('test_sessions.id'), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    build_type = Column(String(20), nullable=False)  # 'compile', 'test', 'package'
    success = Column(Boolean, nullable=False)
    duration_seconds = Column(Integer)
    output_log = Column(Text)
    error_log = Column(Text)
    warnings_count = Column(Integer, default=0)
    errors_count = Column(Integer, default=0)
    
    # Relationships
    session = relationship("TestSession", back_populates="build_results")
    
    # Indexes
    __table_args__ = (
        Index('idx_build_results_session', 'session_id'),
    )


class DeveloperFeedback(Base):
    """Captures subjective assessments from developers."""
    __tablename__ = 'developer_feedback'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey('test_sessions.id'), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    
    # Subjective ratings (1-5 scale)
    ease_of_use_rating = Column(Integer, CheckConstraint('ease_of_use_rating >= 1 AND ease_of_use_rating <= 5'))
    code_quality_rating = Column(Integer, CheckConstraint('code_quality_rating >= 1 AND code_quality_rating <= 5'))
    productivity_rating = Column(Integer, CheckConstraint('productivity_rating >= 1 AND productivity_rating <= 5'))
    learning_curve_rating = Column(Integer, CheckConstraint('learning_curve_rating >= 1 AND learning_curve_rating <= 5'))
    
    # Overall assessment
    would_recommend = Column(Boolean)
    overall_satisfaction = Column(Integer, CheckConstraint('overall_satisfaction >= 1 AND overall_satisfaction <= 5'))
    
    # Free-form feedback
    likes = Column(Text)
    dislikes = Column(Text)
    suggestions = Column(Text)
    additional_comments = Column(Text)
    
    # Relationships
    session = relationship("TestSession", back_populates="developer_feedback")


class DevelopmentMilestone(Base):
    """Tracks key points during development."""
    __tablename__ = 'development_milestones'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey('test_sessions.id'), nullable=False)
    milestone_name = Column(String(100), nullable=False)  # 'requirements_understood', 'initial_implementation', etc.
    timestamp = Column(DateTime, nullable=False)
    description = Column(Text)
    time_elapsed_minutes = Column(Integer)  # Time since session start
    developer_notes = Column(Text)
    
    # Relationships
    session = relationship("TestSession", back_populates="milestones")
    
    # Indexes
    __table_args__ = (
        Index('idx_milestones_session', 'session_id'),
    )


class SystemEvent(Base):
    """System events for automated monitoring."""
    __tablename__ = 'system_events'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey('test_sessions.id'))
    event_type = Column(String(50), nullable=False)  # 'file_change', 'screen_recording_start', 'build_trigger'
    timestamp = Column(DateTime, nullable=False)
    event_data = Column(Text)  # JSON blob with event details
    source = Column(String(50))  # 'file_watcher', 'screen_recorder', 'manual'
    
    # Indexes
    __table_args__ = (
        Index('idx_system_events_session', 'session_id'),
    )