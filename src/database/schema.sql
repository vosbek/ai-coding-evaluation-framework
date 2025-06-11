-- AI Coding Assistant Evaluation Framework Database Schema
-- SQLite schema for storing test sessions, metrics, and analysis data

-- Test sessions represent individual evaluation runs
CREATE TABLE test_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_name VARCHAR(255) NOT NULL,
    tool_name VARCHAR(100) NOT NULL, -- 'cursor', 'github_copilot', etc.
    test_case_type VARCHAR(50) NOT NULL, -- 'bug_fix', 'new_feature', 'refactoring'
    developer_id VARCHAR(100),
    start_time DATETIME NOT NULL,
    end_time DATETIME,
    status VARCHAR(20) DEFAULT 'in_progress', -- 'in_progress', 'completed', 'failed'
    environment_info TEXT, -- JSON blob with environment details
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Test cases define the scenarios being evaluated
CREATE TABLE test_cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL, -- 'bug_fix', 'new_feature', 'refactoring'
    description TEXT NOT NULL,
    requirements TEXT NOT NULL, -- Detailed requirements/acceptance criteria
    standardized_prompts TEXT, -- JSON array of prompts to use
    success_criteria TEXT, -- JSON array of success criteria
    estimated_duration_minutes INTEGER,
    difficulty_level VARCHAR(20), -- 'easy', 'medium', 'hard'
    golden_repo_path VARCHAR(500),
    baseline_branch VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- AI interactions track each prompt/response cycle
CREATE TABLE ai_interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    interaction_sequence INTEGER NOT NULL, -- Order within session
    timestamp DATETIME NOT NULL,
    prompt_text TEXT NOT NULL,
    response_text TEXT,
    interaction_type VARCHAR(50), -- 'code_generation', 'explanation', 'debug', 'refactor'
    quality_rating INTEGER CHECK (quality_rating >= 1 AND quality_rating <= 5),
    was_helpful BOOLEAN,
    tokens_used INTEGER,
    cost_estimate DECIMAL(10,4),
    developer_notes TEXT,
    FOREIGN KEY (session_id) REFERENCES test_sessions(id)
);

-- Code changes track file modifications during testing
CREATE TABLE code_changes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    file_path VARCHAR(1000) NOT NULL,
    change_type VARCHAR(20) NOT NULL, -- 'create', 'modify', 'delete', 'rename'
    timestamp DATETIME NOT NULL,
    lines_added INTEGER DEFAULT 0,
    lines_deleted INTEGER DEFAULT 0,
    lines_modified INTEGER DEFAULT 0,
    git_commit_hash VARCHAR(40),
    diff_content TEXT, -- Store the actual diff
    ai_generated BOOLEAN DEFAULT FALSE, -- Was this change AI-suggested?
    FOREIGN KEY (session_id) REFERENCES test_sessions(id)
);

-- Quality metrics capture before/after code quality measurements
CREATE TABLE quality_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    measurement_point VARCHAR(20) NOT NULL, -- 'baseline', 'completion'
    timestamp DATETIME NOT NULL,
    
    -- Code complexity metrics
    cyclomatic_complexity DECIMAL(10,2),
    lines_of_code INTEGER,
    test_coverage_percentage DECIMAL(5,2),
    
    -- Quality scores (from tools like SonarQube)
    maintainability_rating VARCHAR(5),
    reliability_rating VARCHAR(5),
    security_rating VARCHAR(5),
    technical_debt_minutes INTEGER,
    code_smells INTEGER,
    bugs INTEGER,
    vulnerabilities INTEGER,
    
    -- Build and test results
    build_success BOOLEAN,
    tests_passed INTEGER,
    tests_failed INTEGER,
    build_time_seconds INTEGER,
    
    -- Additional metrics as JSON
    additional_metrics TEXT, -- JSON blob for extensibility
    
    FOREIGN KEY (session_id) REFERENCES test_sessions(id)
);

-- Build results track compilation and test execution
CREATE TABLE build_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    timestamp DATETIME NOT NULL,
    build_type VARCHAR(20) NOT NULL, -- 'compile', 'test', 'package'
    success BOOLEAN NOT NULL,
    duration_seconds INTEGER,
    output_log TEXT,
    error_log TEXT,
    warnings_count INTEGER DEFAULT 0,
    errors_count INTEGER DEFAULT 0,
    FOREIGN KEY (session_id) REFERENCES test_sessions(id)
);

-- Developer feedback captures subjective assessments
CREATE TABLE developer_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    timestamp DATETIME NOT NULL,
    
    -- Subjective ratings (1-5 scale)
    ease_of_use_rating INTEGER CHECK (ease_of_use_rating >= 1 AND ease_of_use_rating <= 5),
    code_quality_rating INTEGER CHECK (code_quality_rating >= 1 AND code_quality_rating <= 5),
    productivity_rating INTEGER CHECK (productivity_rating >= 1 AND productivity_rating <= 5),
    learning_curve_rating INTEGER CHECK (learning_curve_rating >= 1 AND learning_curve_rating <= 5),
    
    -- Overall assessment
    would_recommend BOOLEAN,
    overall_satisfaction INTEGER CHECK (overall_satisfaction >= 1 AND overall_satisfaction <= 5),
    
    -- Free-form feedback
    likes TEXT,
    dislikes TEXT,
    suggestions TEXT,
    additional_comments TEXT,
    
    FOREIGN KEY (session_id) REFERENCES test_sessions(id)
);

-- Milestones track key points during development
CREATE TABLE development_milestones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    milestone_name VARCHAR(100) NOT NULL, -- 'requirements_understood', 'initial_implementation', 'testing_phase', 'bug_fixes', 'complete'
    timestamp DATETIME NOT NULL,
    description TEXT,
    time_elapsed_minutes INTEGER, -- Time since session start
    developer_notes TEXT,
    FOREIGN KEY (session_id) REFERENCES test_sessions(id)
);

-- System events for automated monitoring
CREATE TABLE system_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER,
    event_type VARCHAR(50) NOT NULL, -- 'file_change', 'screen_recording_start', 'build_trigger'
    timestamp DATETIME NOT NULL,
    event_data TEXT, -- JSON blob with event details
    source VARCHAR(50) -- 'file_watcher', 'screen_recorder', 'manual'
);

-- Create indexes for common queries
CREATE INDEX idx_test_sessions_tool_type ON test_sessions(tool_name, test_case_type);
CREATE INDEX idx_test_sessions_status ON test_sessions(status);
CREATE INDEX idx_ai_interactions_session ON ai_interactions(session_id);
CREATE INDEX idx_code_changes_session ON code_changes(session_id);
CREATE INDEX idx_quality_metrics_session ON quality_metrics(session_id);
CREATE INDEX idx_build_results_session ON build_results(session_id);
CREATE INDEX idx_milestones_session ON development_milestones(session_id);
CREATE INDEX idx_system_events_session ON system_events(session_id);

-- Views for common analysis queries
CREATE VIEW session_summary AS
SELECT 
    ts.id,
    ts.session_name,
    ts.tool_name,
    ts.test_case_type,
    ts.start_time,
    ts.end_time,
    ROUND((julianday(ts.end_time) - julianday(ts.start_time)) * 24 * 60, 2) as duration_minutes,
    COUNT(DISTINCT ai.id) as ai_interactions_count,
    COUNT(DISTINCT cc.id) as code_changes_count,
    AVG(df.overall_satisfaction) as avg_satisfaction,
    ts.status
FROM test_sessions ts
LEFT JOIN ai_interactions ai ON ts.id = ai.session_id
LEFT JOIN code_changes cc ON ts.id = cc.session_id
LEFT JOIN developer_feedback df ON ts.id = df.session_id
GROUP BY ts.id, ts.session_name, ts.tool_name, ts.test_case_type, ts.start_time, ts.end_time, ts.status;

CREATE VIEW tool_comparison AS
SELECT 
    tool_name,
    test_case_type,
    COUNT(*) as sessions_count,
    AVG(duration_minutes) as avg_duration_minutes,
    AVG(ai_interactions_count) as avg_ai_interactions,
    AVG(code_changes_count) as avg_code_changes,
    AVG(avg_satisfaction) as avg_satisfaction_rating
FROM session_summary 
WHERE status = 'completed'
GROUP BY tool_name, test_case_type;