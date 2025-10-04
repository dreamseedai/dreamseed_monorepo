-- DreamSeedAI Database Schema
-- Enhanced schema for migrated mpcstudy.com data with adaptive learning support

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Questions table with enhanced metadata
CREATE TABLE questions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    original_id INTEGER UNIQUE, -- Original mpcstudy.com ID
    title VARCHAR(500) NOT NULL,
    
    -- Content (multilingual support)
    question_en TEXT NOT NULL,
    question_ko TEXT,
    question_zh TEXT,
    answer_en TEXT,
    answer_ko TEXT,
    answer_zh TEXT,
    solution_en TEXT,
    solution_ko TEXT,
    solution_zh TEXT,
    explanation_en TEXT,
    explanation_ko TEXT,
    explanation_zh TEXT,
    
    -- Metadata
    subject VARCHAR(50) NOT NULL, -- mathematics, physics, chemistry, biology
    category VARCHAR(50) NOT NULL, -- STEM, Humanities, etc.
    grade_level INTEGER NOT NULL, -- 6-13
    grade_code VARCHAR(10) NOT NULL, -- G6, G7, ..., G12, SAT, AP, UNI
    education_level VARCHAR(50) NOT NULL, -- middle_school, high_school, university
    
    -- Difficulty and adaptive learning
    difficulty_level VARCHAR(20) NOT NULL, -- beginner, intermediate, advanced, expert
    difficulty_score INTEGER NOT NULL, -- 1-10
    adaptive_factor DECIMAL(3,2) NOT NULL, -- 0.8-1.5
    
    -- Topics and classification
    topics TEXT[] NOT NULL, -- Array of topic strings
    question_type VARCHAR(50) NOT NULL, -- multiple_choice, problem_solving, proof, explanation
    
    -- Math content
    has_mathml BOOLEAN DEFAULT FALSE,
    latex_expressions TEXT[], -- Array of LaTeX expressions
    math_complexity VARCHAR(10), -- low, medium, high
    
    -- Quality metrics
    content_quality_score DECIMAL(3,2) DEFAULT 0.0,
    math_accuracy_score DECIMAL(3,2) DEFAULT 0.0,
    pedagogical_value_score DECIMAL(3,2) DEFAULT 0.0,
    accessibility_score DECIMAL(3,2) DEFAULT 0.0,
    
    -- Translation status
    translation_status_en VARCHAR(20) DEFAULT 'complete',
    translation_status_ko VARCHAR(20) DEFAULT 'pending',
    translation_status_zh VARCHAR(20) DEFAULT 'pending',
    
    -- Source and versioning
    source VARCHAR(100) DEFAULT 'mpcstudy.com',
    version VARCHAR(10) DEFAULT '1.0',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Hints table (separate for better normalization)
CREATE TABLE question_hints (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question_id UUID REFERENCES questions(id) ON DELETE CASCADE,
    hint_text_en TEXT NOT NULL,
    hint_text_ko TEXT,
    hint_text_zh TEXT,
    hint_order INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Adaptive learning metadata table
CREATE TABLE adaptive_learning_metadata (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question_id UUID REFERENCES questions(id) ON DELETE CASCADE,
    
    -- Prerequisites
    prerequisites TEXT[], -- Array of prerequisite topics
    
    -- Learning objectives
    learning_objectives TEXT[], -- Array of learning objectives
    
    -- Assessment criteria
    assessment_criteria TEXT[], -- Array of assessment criteria
    
    -- Adaptive difficulty range
    min_difficulty INTEGER NOT NULL,
    max_difficulty INTEGER NOT NULL,
    optimal_difficulty INTEGER NOT NULL,
    
    -- Success indicators
    success_indicators TEXT[], -- Array of success indicators
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Students table for adaptive learning
CREATE TABLE students (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    grade_level INTEGER,
    preferred_subjects TEXT[],
    
    -- Learning preferences
    learning_style VARCHAR(50), -- visual, auditory, kinesthetic, reading
    difficulty_preference VARCHAR(20), -- beginner, intermediate, advanced
    
    -- Adaptive learning state
    current_difficulty_level DECIMAL(3,2) DEFAULT 1.0,
    learning_progress JSONB DEFAULT '{}',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Student learning sessions
CREATE TABLE learning_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID REFERENCES students(id) ON DELETE CASCADE,
    session_type VARCHAR(50) NOT NULL, -- practice, test, review
    subject VARCHAR(50) NOT NULL,
    grade_level INTEGER,
    
    -- Session metadata
    total_questions INTEGER DEFAULT 0,
    correct_answers INTEGER DEFAULT 0,
    session_score DECIMAL(5,2),
    duration_minutes INTEGER,
    
    -- Adaptive learning data
    initial_difficulty DECIMAL(3,2),
    final_difficulty DECIMAL(3,2),
    difficulty_adjustments JSONB DEFAULT '[]',
    
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Individual question attempts
CREATE TABLE question_attempts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES learning_sessions(id) ON DELETE CASCADE,
    question_id UUID REFERENCES questions(id) ON DELETE CASCADE,
    student_id UUID REFERENCES students(id) ON DELETE CASCADE,
    
    -- Attempt data
    student_answer TEXT,
    is_correct BOOLEAN,
    time_spent_seconds INTEGER,
    attempts_count INTEGER DEFAULT 1,
    
    -- Adaptive learning feedback
    difficulty_at_attempt DECIMAL(3,2),
    hints_used INTEGER DEFAULT 0,
    learning_objectives_met TEXT[],
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Student progress tracking
CREATE TABLE student_progress (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID REFERENCES students(id) ON DELETE CASCADE,
    subject VARCHAR(50) NOT NULL,
    topic VARCHAR(100) NOT NULL,
    
    -- Progress metrics
    mastery_level DECIMAL(3,2) DEFAULT 0.0, -- 0.0 to 1.0
    questions_attempted INTEGER DEFAULT 0,
    questions_correct INTEGER DEFAULT 0,
    average_time_seconds INTEGER,
    
    -- Adaptive learning state
    current_difficulty DECIMAL(3,2) DEFAULT 1.0,
    learning_velocity DECIMAL(5,2) DEFAULT 0.0, -- questions per minute
    
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(student_id, subject, topic)
);

-- Indexes for performance
CREATE INDEX idx_questions_subject_grade ON questions(subject, grade_level);
CREATE INDEX idx_questions_difficulty ON questions(difficulty_level, difficulty_score);
CREATE INDEX idx_questions_topics ON questions USING GIN(topics);
CREATE INDEX idx_questions_mathml ON questions(has_mathml) WHERE has_mathml = TRUE;
CREATE INDEX idx_questions_quality ON questions(content_quality_score, math_accuracy_score);

CREATE INDEX idx_learning_sessions_student ON learning_sessions(student_id, started_at);
CREATE INDEX idx_question_attempts_session ON question_attempts(session_id, created_at);
CREATE INDEX idx_question_attempts_question ON question_attempts(question_id, is_correct);
CREATE INDEX idx_student_progress_student ON student_progress(student_id, subject);

-- Full-text search indexes
CREATE INDEX idx_questions_search_en ON questions USING GIN(to_tsvector('english', question_en || ' ' || COALESCE(answer_en, '') || ' ' || COALESCE(solution_en, '')));
CREATE INDEX idx_questions_search_ko ON questions USING GIN(to_tsvector('korean', question_ko || ' ' || COALESCE(answer_ko, '') || ' ' || COALESCE(solution_ko, '')));

-- Triggers for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_questions_updated_at BEFORE UPDATE ON questions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_students_updated_at BEFORE UPDATE ON students
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Views for common queries
CREATE VIEW question_summary AS
SELECT 
    q.id,
    q.original_id,
    q.title,
    q.subject,
    q.grade_level,
    q.difficulty_level,
    q.difficulty_score,
    q.topics,
    q.question_type,
    q.has_mathml,
    q.math_complexity,
    q.content_quality_score,
    q.translation_status_ko,
    q.translation_status_zh,
    q.created_at
FROM questions q;

CREATE VIEW student_performance AS
SELECT 
    s.id as student_id,
    s.name,
    s.grade_level,
    sp.subject,
    sp.topic,
    sp.mastery_level,
    sp.questions_attempted,
    sp.questions_correct,
    CASE 
        WHEN sp.questions_attempted > 0 
        THEN (sp.questions_correct::DECIMAL / sp.questions_attempted) * 100 
        ELSE 0 
    END as accuracy_percentage,
    sp.current_difficulty,
    sp.learning_velocity,
    sp.last_updated
FROM students s
JOIN student_progress sp ON s.id = sp.student_id;

-- Functions for adaptive learning
CREATE OR REPLACE FUNCTION calculate_difficulty_adjustment(
    p_student_id UUID,
    p_question_id UUID,
    p_is_correct BOOLEAN,
    p_time_spent INTEGER
) RETURNS DECIMAL(3,2) AS $$
DECLARE
    v_current_difficulty DECIMAL(3,2);
    v_adjustment DECIMAL(3,2) := 0.0;
    v_adaptive_factor DECIMAL(3,2);
BEGIN
    -- Get current difficulty and adaptive factor
    SELECT q.adaptive_factor INTO v_adaptive_factor
    FROM questions q WHERE q.id = p_question_id;
    
    SELECT sp.current_difficulty INTO v_current_difficulty
    FROM student_progress sp
    WHERE sp.student_id = p_student_id
    AND sp.subject = (SELECT subject FROM questions WHERE id = p_question_id)
    LIMIT 1;
    
    -- Calculate adjustment based on performance
    IF p_is_correct THEN
        -- Increase difficulty if answered correctly and quickly
        IF p_time_spent < 60 THEN -- Less than 1 minute
            v_adjustment := 0.1 * v_adaptive_factor;
        ELSE
            v_adjustment := 0.05 * v_adaptive_factor;
        END IF;
    ELSE
        -- Decrease difficulty if answered incorrectly
        v_adjustment := -0.1 * v_adaptive_factor;
    END IF;
    
    -- Ensure difficulty stays within bounds
    v_current_difficulty := GREATEST(0.5, LEAST(2.0, v_current_difficulty + v_adjustment));
    
    RETURN v_current_difficulty;
END;
$$ LANGUAGE plpgsql;

-- Function to get personalized questions
CREATE OR REPLACE FUNCTION get_personalized_questions(
    p_student_id UUID,
    p_subject VARCHAR(50),
    p_limit INTEGER DEFAULT 10
) RETURNS TABLE(
    question_id UUID,
    title VARCHAR(500),
    difficulty_score INTEGER,
    topics TEXT[],
    question_type VARCHAR(50)
) AS $$
DECLARE
    v_student_grade INTEGER;
    v_current_difficulty DECIMAL(3,2);
BEGIN
    -- Get student's grade and current difficulty
    SELECT s.grade_level, sp.current_difficulty
    INTO v_student_grade, v_current_difficulty
    FROM students s
    LEFT JOIN student_progress sp ON s.id = sp.student_id
    WHERE s.id = p_student_id AND sp.subject = p_subject
    LIMIT 1;
    
    -- Return personalized questions
    RETURN QUERY
    SELECT 
        q.id,
        q.title,
        q.difficulty_score,
        q.topics,
        q.question_type
    FROM questions q
    WHERE q.subject = p_subject
    AND q.grade_level = COALESCE(v_student_grade, 10)
    AND q.difficulty_score BETWEEN 
        GREATEST(1, FLOOR(v_current_difficulty) - 1) AND 
        LEAST(10, CEIL(v_current_difficulty) + 1)
    AND q.content_quality_score >= 0.7
    ORDER BY 
        ABS(q.difficulty_score - v_current_difficulty),
        q.content_quality_score DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;
