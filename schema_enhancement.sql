-- DreamSeedAI Enhanced Schema for Personalized Educational Platform
-- Extending existing schema to support multilingual content and advanced personalization

-- 1. Extend users_profile table with educational preferences
ALTER TABLE users_profile 
ADD COLUMN IF NOT EXISTS preferred_subjects TEXT[], -- Array of subjects: ['math', 'biology', 'physics']
ADD COLUMN IF NOT EXISTS difficulty_preference INTEGER DEFAULT 2, -- 1-5 scale
ADD COLUMN IF NOT EXISTS learning_style VARCHAR(32), -- 'visual', 'auditory', 'kinesthetic', 'reading'
ADD COLUMN IF NOT EXISTS study_goals TEXT[], -- ['sat_prep', 'ap_courses', 'college_readiness', 'general_improvement']
ADD COLUMN IF NOT EXISTS time_zone VARCHAR(64),
ADD COLUMN IF NOT EXISTS notification_preferences JSONB DEFAULT '{"email": true, "push": false, "weekly_progress": true}',
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- 2. Create enhanced questions table with multilingual support
CREATE TABLE IF NOT EXISTS questions_enhanced (
    id SERIAL PRIMARY KEY,
    -- Original question data
    que_id INTEGER, -- Reference to original mpcstudy question ID
    que_class CHAR(1), -- M=Math, B=Biology, P=Physics
    que_grade CHAR(3), -- G07, G08, G09, G10, G11, G12
    que_level INTEGER DEFAULT 1, -- Difficulty level 1-5
    que_category1 INTEGER DEFAULT 0,
    que_category2 INTEGER DEFAULT 0,
    que_category3 INTEGER DEFAULT 0,
    que_answertype INTEGER DEFAULT 0, -- 0=multiple choice, 1=short answer
    que_en_answerm CHAR(1), -- Correct answer for multiple choice
    
    -- English content (original)
    que_en_title TEXT,
    que_en_desc TEXT,
    que_en_hint TEXT,
    que_en_solution TEXT,
    que_en_answers TEXT,
    que_en_example TEXT,
    que_en_resource TEXT,
    
    -- Korean content (future)
    que_ko_title TEXT,
    que_ko_desc TEXT,
    que_ko_hint TEXT,
    que_ko_solution TEXT,
    que_ko_answers TEXT,
    que_ko_example TEXT,
    que_ko_resource TEXT,
    
    -- Chinese content (future)
    que_zh_title TEXT,
    que_zh_desc TEXT,
    que_zh_hint TEXT,
    que_zh_solution TEXT,
    que_zh_answers TEXT,
    que_zh_example TEXT,
    que_zh_resource TEXT,
    
    -- Enhanced features
    que_difficulty_tags TEXT[], -- ['algebra', 'geometry', 'trigonometry']
    que_learning_objectives TEXT[], -- Educational goals this question addresses
    que_prerequisites TEXT[], -- Required knowledge to attempt this question
    que_estimated_time INTEGER, -- Estimated time in minutes
    que_mathml_content TEXT, -- Original MathML for conversion
    que_tiptap_content JSONB, -- Converted TipTap + MathLive content
    
    -- Metadata
    que_status INTEGER DEFAULT 1,
    que_createddate VARCHAR(14),
    que_modifieddate VARCHAR(14),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Create user performance tracking table
CREATE TABLE IF NOT EXISTS user_performance (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    question_id INTEGER NOT NULL REFERENCES questions_enhanced(id) ON DELETE CASCADE,
    
    -- Performance metrics
    attempt_count INTEGER DEFAULT 1,
    is_correct BOOLEAN,
    time_spent INTEGER, -- Time in seconds
    hints_used INTEGER DEFAULT 0,
    difficulty_rating INTEGER, -- User's rating of question difficulty (1-5)
    
    -- Learning analytics
    confidence_level INTEGER, -- User's confidence in answer (1-5)
    learning_gain DECIMAL(3,2), -- Calculated learning improvement
    mastery_level DECIMAL(3,2), -- Mastery score for this topic
    
    -- Metadata
    attempt_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    user_agent TEXT,
    session_id VARCHAR(64),
    
    UNIQUE(user_id, question_id, attempt_date)
);

-- 4. Create adaptive learning recommendations table
CREATE TABLE IF NOT EXISTS learning_recommendations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Recommendation data
    recommended_questions INTEGER[] DEFAULT '{}', -- Array of question IDs
    recommended_subjects TEXT[] DEFAULT '{}',
    difficulty_adjustment INTEGER DEFAULT 0, -- -2 to +2 adjustment
    learning_path JSONB, -- Structured learning progression
    
    -- Recommendation metadata
    algorithm_version VARCHAR(16) DEFAULT 'v1.0',
    confidence_score DECIMAL(3,2), -- Algorithm confidence in recommendations
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() + INTERVAL '7 days'),
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    user_feedback INTEGER -- User rating of recommendations (1-5)
);

-- 5. Create content translation tracking table
CREATE TABLE IF NOT EXISTS content_translations (
    id SERIAL PRIMARY KEY,
    question_id INTEGER NOT NULL REFERENCES questions_enhanced(id) ON DELETE CASCADE,
    
    -- Translation details
    target_language VARCHAR(8) NOT NULL, -- 'ko', 'zh', 'es', etc.
    translation_type VARCHAR(16) NOT NULL, -- 'title', 'description', 'solution', etc.
    field_name VARCHAR(32) NOT NULL, -- 'que_ko_title', 'que_zh_desc', etc.
    
    -- Translation content
    original_text TEXT,
    translated_text TEXT,
    translation_confidence DECIMAL(3,2), -- AI confidence score
    
    -- Translation metadata
    translator_type VARCHAR(16) DEFAULT 'ai', -- 'ai', 'human', 'hybrid'
    translator_model VARCHAR(64), -- 'gpt-4', 'google-translate', etc.
    translation_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Quality control
    is_reviewed BOOLEAN DEFAULT FALSE,
    reviewer_id INTEGER REFERENCES users(id),
    review_date TIMESTAMP WITH TIME ZONE,
    quality_score INTEGER, -- 1-5 quality rating
    
    UNIQUE(question_id, target_language, field_name)
);

-- 6. Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_questions_enhanced_grade_level ON questions_enhanced(que_grade, que_level);
CREATE INDEX IF NOT EXISTS idx_questions_enhanced_subject ON questions_enhanced(que_class);
CREATE INDEX IF NOT EXISTS idx_questions_enhanced_categories ON questions_enhanced(que_category1, que_category2, que_category3);
CREATE INDEX IF NOT EXISTS idx_questions_enhanced_difficulty_tags ON questions_enhanced USING GIN(que_difficulty_tags);

CREATE INDEX IF NOT EXISTS idx_user_performance_user_question ON user_performance(user_id, question_id);
CREATE INDEX IF NOT EXISTS idx_user_performance_date ON user_performance(attempt_date);
CREATE INDEX IF NOT EXISTS idx_user_performance_correctness ON user_performance(is_correct);

CREATE INDEX IF NOT EXISTS idx_learning_recommendations_user ON learning_recommendations(user_id);
CREATE INDEX IF NOT EXISTS idx_learning_recommendations_active ON learning_recommendations(is_active, expires_at);

CREATE INDEX IF NOT EXISTS idx_content_translations_question ON content_translations(question_id);
CREATE INDEX IF NOT EXISTS idx_content_translations_language ON content_translations(target_language);

-- 7. Create triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_profile_updated_at 
    BEFORE UPDATE ON users_profile 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_questions_enhanced_updated_at 
    BEFORE UPDATE ON questions_enhanced 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 8. Create views for common queries
CREATE OR REPLACE VIEW user_learning_analytics AS
SELECT 
    u.id as user_id,
    u.email,
    up.grade_code,
    up.preferred_subjects,
    up.country,
    COUNT(DISTINCT up2.question_id) as total_questions_attempted,
    COUNT(DISTINCT CASE WHEN up2.is_correct = true THEN up2.question_id END) as correct_answers,
    ROUND(
        COUNT(DISTINCT CASE WHEN up2.is_correct = true THEN up2.question_id END)::DECIMAL / 
        NULLIF(COUNT(DISTINCT up2.question_id), 0) * 100, 2
    ) as accuracy_percentage,
    AVG(up2.time_spent) as avg_time_per_question,
    AVG(up2.mastery_level) as avg_mastery_level
FROM users u
LEFT JOIN users_profile up ON u.id = up.user_id
LEFT JOIN user_performance up2 ON u.id = up2.user_id
GROUP BY u.id, u.email, up.grade_code, up.preferred_subjects, up.country;

-- 9. Insert sample data for testing
INSERT INTO questions_enhanced (
    que_class, que_grade, que_level, que_en_title, que_en_desc, 
    que_en_solution, que_difficulty_tags, que_estimated_time
) VALUES 
('M', 'G08', 2, 'Triangle Angles', 'Find the missing angle in triangle ABC where angle A = 60° and angle B = 45°', 
 'Angle C = 180° - 60° - 45° = 75°', ARRAY['geometry', 'triangles'], 3),
('B', 'G10', 3, 'Cell Structure', 'Identify the organelle responsible for protein synthesis', 
 'The ribosome is responsible for protein synthesis', ARRAY['cell_biology', 'organelles'], 2),
('M', 'G11', 4, 'Quadratic Functions', 'Find the vertex of the parabola y = 2x² - 8x + 5', 
 'Vertex = (2, -3) using the formula x = -b/2a', ARRAY['algebra', 'quadratics'], 5);

-- 10. Create function for personalized question recommendations
CREATE OR REPLACE FUNCTION get_personalized_questions(
    p_user_id INTEGER,
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    question_id INTEGER,
    title TEXT,
    description TEXT,
    difficulty_level INTEGER,
    estimated_time INTEGER,
    subject CHAR(1),
    grade CHAR(3),
    relevance_score DECIMAL(3,2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        qe.id,
        qe.que_en_title,
        qe.que_en_desc,
        qe.que_level,
        qe.que_estimated_time,
        qe.que_class,
        qe.que_grade,
        -- Calculate relevance score based on user preferences and performance
        CASE 
            WHEN up.preferred_subjects @> ARRAY[qe.que_class::TEXT] THEN 0.8
            ELSE 0.4
        END +
        CASE 
            WHEN qe.que_level BETWEEN (up.difficulty_preference - 1) AND (up.difficulty_preference + 1) THEN 0.2
            ELSE 0.0
        END as relevance_score
    FROM questions_enhanced qe
    CROSS JOIN users_profile up
    WHERE up.user_id = p_user_id
    AND qe.que_status = 1
    AND qe.que_en_title IS NOT NULL
    ORDER BY relevance_score DESC, qe.que_level ASC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;
