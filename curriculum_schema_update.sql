-- DreamSeedAI Curriculum Classification Schema Update
-- Adds US/Canada curriculum classification fields to existing schema

-- Add curriculum classification columns to questions table
ALTER TABLE questions 
ADD COLUMN IF NOT EXISTS us_curriculum_grade VARCHAR(10),
ADD COLUMN IF NOT EXISTS us_curriculum_subject VARCHAR(50),
ADD COLUMN IF NOT EXISTS us_curriculum_course VARCHAR(100),
ADD COLUMN IF NOT EXISTS us_curriculum_topic VARCHAR(200),
ADD COLUMN IF NOT EXISTS us_curriculum_confidence DECIMAL(3,2),
ADD COLUMN IF NOT EXISTS us_curriculum_difficulty VARCHAR(20),
ADD COLUMN IF NOT EXISTS us_curriculum_alignment DECIMAL(3,2),
ADD COLUMN IF NOT EXISTS canada_curriculum_grade VARCHAR(10),
ADD COLUMN IF NOT EXISTS canada_curriculum_subject VARCHAR(50),
ADD COLUMN IF NOT EXISTS canada_curriculum_course VARCHAR(100),
ADD COLUMN IF NOT EXISTS canada_curriculum_topic VARCHAR(200),
ADD COLUMN IF NOT EXISTS canada_curriculum_confidence DECIMAL(3,2),
ADD COLUMN IF NOT EXISTS canada_curriculum_difficulty VARCHAR(20),
ADD COLUMN IF NOT EXISTS canada_curriculum_alignment DECIMAL(3,2),
ADD COLUMN IF NOT EXISTS curriculum_classification_date TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS curriculum_classification_notes TEXT;

-- Create curriculum standards reference table
CREATE TABLE IF NOT EXISTS curriculum_standards (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    country VARCHAR(20) NOT NULL, -- 'US' or 'Canada'
    subject VARCHAR(50) NOT NULL,
    grade VARCHAR(10) NOT NULL,
    course VARCHAR(100) NOT NULL,
    topic VARCHAR(200) NOT NULL,
    description TEXT,
    difficulty_level VARCHAR(20),
    prerequisites TEXT[],
    learning_objectives TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(country, subject, grade, course, topic)
);

-- Create curriculum mapping table for detailed mappings
CREATE TABLE IF NOT EXISTS curriculum_mappings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question_id UUID REFERENCES questions(id) ON DELETE CASCADE,
    country VARCHAR(20) NOT NULL,
    subject VARCHAR(50) NOT NULL,
    grade VARCHAR(10) NOT NULL,
    course VARCHAR(100) NOT NULL,
    topic VARCHAR(200) NOT NULL,
    confidence_score DECIMAL(3,2) NOT NULL,
    difficulty_level VARCHAR(20) NOT NULL,
    alignment_score DECIMAL(3,2),
    classification_reasoning TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(question_id, country)
);

-- Create curriculum-based question recommendations table
CREATE TABLE IF NOT EXISTS curriculum_recommendations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID REFERENCES students(id) ON DELETE CASCADE,
    country VARCHAR(20) NOT NULL, -- 'US' or 'Canada'
    subject VARCHAR(50) NOT NULL,
    grade VARCHAR(10) NOT NULL,
    course VARCHAR(100),
    topic VARCHAR(200),
    recommended_questions UUID[] NOT NULL,
    recommendation_score DECIMAL(3,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE
);

-- Create curriculum progress tracking table
CREATE TABLE IF NOT EXISTS curriculum_progress (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID REFERENCES students(id) ON DELETE CASCADE,
    country VARCHAR(20) NOT NULL,
    subject VARCHAR(50) NOT NULL,
    grade VARCHAR(10) NOT NULL,
    course VARCHAR(100) NOT NULL,
    topic VARCHAR(200) NOT NULL,
    questions_attempted INTEGER DEFAULT 0,
    questions_correct INTEGER DEFAULT 0,
    mastery_level DECIMAL(3,2) DEFAULT 0.0,
    last_attempted TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(student_id, country, subject, grade, course, topic)
);

-- Insert US curriculum standards
INSERT INTO curriculum_standards (country, subject, grade, course, topic, description, difficulty_level) VALUES
-- US Mathematics G9
('US', 'Mathematics', 'G9', 'Algebra_I', 'Linear equations and inequalities', 'Solving linear equations and inequalities with one variable', 'beginner'),
('US', 'Mathematics', 'G9', 'Algebra_I', 'Functions and relations', 'Understanding functions, domain, range, and function notation', 'beginner'),
('US', 'Mathematics', 'G9', 'Algebra_I', 'Systems of equations', 'Solving systems of linear equations using various methods', 'intermediate'),
('US', 'Mathematics', 'G9', 'Algebra_I', 'Polynomials and factoring', 'Operations with polynomials and factoring techniques', 'intermediate'),
('US', 'Mathematics', 'G9', 'Algebra_I', 'Quadratic functions', 'Graphing and solving quadratic equations', 'intermediate'),
('US', 'Mathematics', 'G9', 'Algebra_I', 'Exponential functions', 'Understanding exponential growth and decay', 'intermediate'),
('US', 'Mathematics', 'G9', 'Algebra_I', 'Data analysis and statistics', 'Basic statistical measures and data interpretation', 'beginner'),

-- US Mathematics G10
('US', 'Mathematics', 'G10', 'Geometry', 'Points, lines, and planes', 'Basic geometric concepts and postulates', 'beginner'),
('US', 'Mathematics', 'G10', 'Geometry', 'Angles and parallel lines', 'Angle relationships and parallel line properties', 'beginner'),
('US', 'Mathematics', 'G10', 'Geometry', 'Triangles and congruence', 'Triangle properties and congruence theorems', 'intermediate'),
('US', 'Mathematics', 'G10', 'Geometry', 'Quadrilaterals', 'Properties of quadrilaterals and their classifications', 'intermediate'),
('US', 'Mathematics', 'G10', 'Geometry', 'Similarity and proportions', 'Similar figures and proportional relationships', 'intermediate'),
('US', 'Mathematics', 'G10', 'Geometry', 'Right triangles and trigonometry', 'Pythagorean theorem and basic trigonometry', 'intermediate'),
('US', 'Mathematics', 'G10', 'Geometry', 'Circles and arcs', 'Circle properties and arc measurements', 'intermediate'),
('US', 'Mathematics', 'G10', 'Geometry', 'Area and perimeter', 'Calculating area and perimeter of various shapes', 'beginner'),
('US', 'Mathematics', 'G10', 'Geometry', 'Volume and surface area', 'Calculating volume and surface area of 3D shapes', 'intermediate'),

-- US Mathematics G11
('US', 'Mathematics', 'G11', 'Algebra_II', 'Complex numbers', 'Operations with complex numbers and the complex plane', 'advanced'),
('US', 'Mathematics', 'G11', 'Algebra_II', 'Polynomial functions', 'Advanced polynomial operations and graphing', 'advanced'),
('US', 'Mathematics', 'G11', 'Algebra_II', 'Rational functions', 'Operations with rational expressions and functions', 'advanced'),
('US', 'Mathematics', 'G11', 'Algebra_II', 'Exponential and logarithmic functions', 'Properties and applications of exponential and log functions', 'advanced'),
('US', 'Mathematics', 'G11', 'Algebra_II', 'Trigonometric functions', 'Unit circle, trigonometric identities, and graphing', 'advanced'),
('US', 'Mathematics', 'G11', 'Algebra_II', 'Sequences and series', 'Arithmetic and geometric sequences and series', 'intermediate'),
('US', 'Mathematics', 'G11', 'Algebra_II', 'Probability and statistics', 'Advanced probability and statistical analysis', 'intermediate'),
('US', 'Mathematics', 'G11', 'Algebra_II', 'Conic sections', 'Equations and graphs of conic sections', 'expert'),

-- US Mathematics G12
('US', 'Mathematics', 'G12', 'Pre_Calculus', 'Advanced functions', 'Composition and transformation of functions', 'advanced'),
('US', 'Mathematics', 'G12', 'Pre_Calculus', 'Trigonometric identities', 'Proving and applying trigonometric identities', 'expert'),
('US', 'Mathematics', 'G12', 'Pre_Calculus', 'Polar coordinates', 'Graphing and converting between coordinate systems', 'expert'),
('US', 'Mathematics', 'G12', 'Pre_Calculus', 'Vectors', 'Vector operations and applications', 'expert'),
('US', 'Mathematics', 'G12', 'Pre_Calculus', 'Matrices', 'Matrix operations and applications', 'expert'),
('US', 'Mathematics', 'G12', 'Pre_Calculus', 'Limits and continuity', 'Introduction to calculus concepts', 'expert'),
('US', 'Mathematics', 'G12', 'Calculus', 'Derivatives', 'Definition and applications of derivatives', 'expert'),
('US', 'Mathematics', 'G12', 'Calculus', 'Applications of derivatives', 'Optimization and related rates problems', 'expert'),
('US', 'Mathematics', 'G12', 'Calculus', 'Integrals', 'Definite and indefinite integrals', 'expert'),
('US', 'Mathematics', 'G12', 'Calculus', 'Applications of integrals', 'Area, volume, and other applications of integration', 'expert'),
('US', 'Mathematics', 'G12', 'Calculus', 'Differential equations', 'Basic differential equations and solutions', 'expert'),

-- US Physics G9
('US', 'Physics', 'G9', 'Physical_Science', 'Motion and forces', 'Basic concepts of motion, velocity, and forces', 'beginner'),
('US', 'Physics', 'G9', 'Physical_Science', 'Energy and work', 'Energy conservation and work-energy theorem', 'beginner'),
('US', 'Physics', 'G9', 'Physical_Science', 'Waves and sound', 'Wave properties and sound waves', 'beginner'),
('US', 'Physics', 'G9', 'Physical_Science', 'Light and optics', 'Basic optics and light behavior', 'beginner'),
('US', 'Physics', 'G9', 'Physical_Science', 'Electricity basics', 'Basic electrical concepts and circuits', 'beginner'),
('US', 'Physics', 'G9', 'Physical_Science', 'Magnetism basics', 'Basic magnetic concepts and applications', 'beginner'),

-- US Physics G10
('US', 'Physics', 'G10', 'Physics_I', 'Kinematics', 'Motion in one and two dimensions', 'intermediate'),
('US', 'Physics', 'G10', 'Physics_I', 'Dynamics', 'Newton''s laws and force analysis', 'intermediate'),
('US', 'Physics', 'G10', 'Physics_I', 'Energy and momentum', 'Conservation laws and energy transfer', 'intermediate'),
('US', 'Physics', 'G10', 'Physics_I', 'Rotational motion', 'Angular motion and rotational dynamics', 'advanced'),
('US', 'Physics', 'G10', 'Physics_I', 'Simple harmonic motion', 'Oscillatory motion and pendulums', 'intermediate'),
('US', 'Physics', 'G10', 'Physics_I', 'Fluid mechanics', 'Pressure, buoyancy, and fluid flow', 'advanced'),

-- US Physics G11
('US', 'Physics', 'G11', 'Physics_II', 'Electric fields and forces', 'Electric field theory and applications', 'advanced'),
('US', 'Physics', 'G11', 'Physics_II', 'Magnetic fields and forces', 'Magnetic field theory and applications', 'advanced'),
('US', 'Physics', 'G11', 'Physics_II', 'Electromagnetic induction', 'Faraday''s law and electromagnetic induction', 'expert'),
('US', 'Physics', 'G11', 'Physics_II', 'AC circuits', 'Alternating current circuits and analysis', 'expert'),
('US', 'Physics', 'G11', 'Physics_II', 'Wave properties', 'Advanced wave theory and interference', 'advanced'),
('US', 'Physics', 'G11', 'Physics_II', 'Optics and interference', 'Light interference and diffraction', 'expert'),

-- US Physics G12
('US', 'Physics', 'G12', 'AP_Physics', 'Advanced mechanics', 'Advanced mechanical systems and analysis', 'expert'),
('US', 'Physics', 'G12', 'AP_Physics', 'Thermodynamics', 'Heat, temperature, and thermodynamic laws', 'expert'),
('US', 'Physics', 'G12', 'AP_Physics', 'Electromagnetic fields', 'Advanced electromagnetic field theory', 'expert'),
('US', 'Physics', 'G12', 'AP_Physics', 'Quantum mechanics', 'Introduction to quantum mechanical principles', 'expert'),
('US', 'Physics', 'G12', 'AP_Physics', 'Special relativity', 'Einstein''s theory of special relativity', 'expert'),
('US', 'Physics', 'G12', 'AP_Physics', 'Nuclear physics', 'Nuclear reactions and radioactivity', 'expert'),

-- Canada Mathematics G9
('Canada', 'Mathematics', 'G9', 'Mathematics_9', 'Number sense and operations', 'Rational numbers and operations', 'beginner'),
('Canada', 'Mathematics', 'G9', 'Mathematics_9', 'Algebra and patterns', 'Linear relationships and patterns', 'beginner'),
('Canada', 'Mathematics', 'G9', 'Mathematics_9', 'Geometry and measurement', 'Geometric properties and measurements', 'beginner'),
('Canada', 'Mathematics', 'G9', 'Mathematics_9', 'Data management and probability', 'Data collection and basic probability', 'beginner'),
('Canada', 'Mathematics', 'G9', 'Mathematics_9', 'Financial literacy', 'Basic financial mathematics', 'beginner'),

-- Canada Mathematics G10
('Canada', 'Mathematics', 'G10', 'Mathematics_10', 'Linear relations', 'Linear functions and equations', 'intermediate'),
('Canada', 'Mathematics', 'G10', 'Mathematics_10', 'Quadratic relations', 'Quadratic functions and equations', 'intermediate'),
('Canada', 'Mathematics', 'G10', 'Mathematics_10', 'Trigonometry', 'Right triangle trigonometry', 'intermediate'),
('Canada', 'Mathematics', 'G10', 'Mathematics_10', 'Analytic geometry', 'Coordinate geometry and distance', 'intermediate'),
('Canada', 'Mathematics', 'G10', 'Mathematics_10', 'Data management', 'Statistical analysis and probability', 'intermediate'),

-- Canada Mathematics G11
('Canada', 'Mathematics', 'G11', 'Functions_11', 'Quadratic functions', 'Advanced quadratic function analysis', 'advanced'),
('Canada', 'Mathematics', 'G11', 'Functions_11', 'Exponential functions', 'Exponential growth and decay models', 'advanced'),
('Canada', 'Mathematics', 'G11', 'Functions_11', 'Trigonometric functions', 'Unit circle and trigonometric functions', 'advanced'),
('Canada', 'Mathematics', 'G11', 'Functions_11', 'Discrete functions', 'Sequences, series, and discrete mathematics', 'advanced'),
('Canada', 'Mathematics', 'G11', 'Functions_11', 'Financial applications', 'Compound interest and financial modeling', 'intermediate'),

-- Canada Mathematics G12
('Canada', 'Mathematics', 'G12', 'Advanced_Functions', 'Polynomial functions', 'Advanced polynomial analysis', 'expert'),
('Canada', 'Mathematics', 'G12', 'Advanced_Functions', 'Exponential and logarithmic functions', 'Advanced exponential and logarithmic analysis', 'expert'),
('Canada', 'Mathematics', 'G12', 'Advanced_Functions', 'Trigonometric functions', 'Advanced trigonometric analysis', 'expert'),
('Canada', 'Mathematics', 'G12', 'Advanced_Functions', 'Combinations of functions', 'Function composition and transformations', 'expert'),
('Canada', 'Mathematics', 'G12', 'Calculus_and_Vectors', 'Limits and continuity', 'Introduction to limits and continuity', 'expert'),
('Canada', 'Mathematics', 'G12', 'Calculus_and_Vectors', 'Derivatives', 'Derivative definition and applications', 'expert'),
('Canada', 'Mathematics', 'G12', 'Calculus_and_Vectors', 'Applications of derivatives', 'Optimization and curve sketching', 'expert'),
('Canada', 'Mathematics', 'G12', 'Calculus_and_Vectors', 'Integrals', 'Definite and indefinite integrals', 'expert'),
('Canada', 'Mathematics', 'G12', 'Calculus_and_Vectors', 'Vectors in two and three dimensions', 'Vector operations and applications', 'expert'),
('Canada', 'Mathematics', 'G12', 'Data_Management', 'Probability', 'Advanced probability theory', 'advanced'),
('Canada', 'Mathematics', 'G12', 'Data_Management', 'Statistics', 'Statistical inference and analysis', 'advanced'),
('Canada', 'Mathematics', 'G12', 'Data_Management', 'Distributions', 'Probability distributions', 'advanced'),
('Canada', 'Mathematics', 'G12', 'Data_Management', 'Hypothesis testing', 'Statistical hypothesis testing', 'expert'),
('Canada', 'Mathematics', 'G12', 'Data_Management', 'Regression analysis', 'Linear and non-linear regression', 'expert');

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_questions_us_curriculum ON questions(us_curriculum_grade, us_curriculum_subject, us_curriculum_course);
CREATE INDEX IF NOT EXISTS idx_questions_canada_curriculum ON questions(canada_curriculum_grade, canada_curriculum_subject, canada_curriculum_course);
CREATE INDEX IF NOT EXISTS idx_questions_curriculum_confidence ON questions(us_curriculum_confidence, canada_curriculum_confidence);

CREATE INDEX IF NOT EXISTS idx_curriculum_mappings_question ON curriculum_mappings(question_id);
CREATE INDEX IF NOT EXISTS idx_curriculum_mappings_country ON curriculum_mappings(country, subject, grade);
CREATE INDEX IF NOT EXISTS idx_curriculum_recommendations_student ON curriculum_recommendations(student_id, country);
CREATE INDEX IF NOT EXISTS idx_curriculum_progress_student ON curriculum_progress(student_id, country, subject);

-- Create views for curriculum-based queries
CREATE OR REPLACE VIEW curriculum_question_summary AS
SELECT 
    q.id,
    q.title,
    q.us_curriculum_grade,
    q.us_curriculum_subject,
    q.us_curriculum_course,
    q.us_curriculum_topic,
    q.us_curriculum_confidence,
    q.canada_curriculum_grade,
    q.canada_curriculum_subject,
    q.canada_curriculum_course,
    q.canada_curriculum_topic,
    q.canada_curriculum_confidence,
    q.difficulty_level,
    q.content_quality_score
FROM questions q
WHERE q.us_curriculum_grade IS NOT NULL OR q.canada_curriculum_grade IS NOT NULL;

-- Create function to get curriculum-aligned questions
CREATE OR REPLACE FUNCTION get_curriculum_questions(
    p_country VARCHAR(20),
    p_subject VARCHAR(50),
    p_grade VARCHAR(10),
    p_course VARCHAR(100) DEFAULT NULL,
    p_topic VARCHAR(200) DEFAULT NULL,
    p_limit INTEGER DEFAULT 20
) RETURNS TABLE(
    question_id UUID,
    title VARCHAR(500),
    confidence DECIMAL(3,2),
    difficulty_level VARCHAR(20),
    content_quality_score DECIMAL(3,2)
) AS $$
BEGIN
    IF p_country = 'US' THEN
        RETURN QUERY
        SELECT 
            q.id,
            q.title,
            q.us_curriculum_confidence,
            q.difficulty_level,
            q.content_quality_score
        FROM questions q
        WHERE q.us_curriculum_grade = p_grade
        AND q.us_curriculum_subject = p_subject
        AND (p_course IS NULL OR q.us_curriculum_course = p_course)
        AND (p_topic IS NULL OR q.us_curriculum_topic = p_topic)
        AND q.us_curriculum_confidence >= 0.7
        ORDER BY q.us_curriculum_confidence DESC, q.content_quality_score DESC
        LIMIT p_limit;
    ELSE
        RETURN QUERY
        SELECT 
            q.id,
            q.title,
            q.canada_curriculum_confidence,
            q.difficulty_level,
            q.content_quality_score
        FROM questions q
        WHERE q.canada_curriculum_grade = p_grade
        AND q.canada_curriculum_subject = p_subject
        AND (p_course IS NULL OR q.canada_curriculum_course = p_course)
        AND (p_topic IS NULL OR q.canada_curriculum_topic = p_topic)
        AND q.canada_curriculum_confidence >= 0.7
        ORDER BY q.canada_curriculum_confidence DESC, q.content_quality_score DESC
        LIMIT p_limit;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Create function to update curriculum progress
CREATE OR REPLACE FUNCTION update_curriculum_progress(
    p_student_id UUID,
    p_country VARCHAR(20),
    p_subject VARCHAR(50),
    p_grade VARCHAR(10),
    p_course VARCHAR(100),
    p_topic VARCHAR(200),
    p_is_correct BOOLEAN
) RETURNS VOID AS $$
BEGIN
    INSERT INTO curriculum_progress (
        student_id, country, subject, grade, course, topic,
        questions_attempted, questions_correct, last_attempted
    ) VALUES (
        p_student_id, p_country, p_subject, p_grade, p_course, p_topic,
        1, CASE WHEN p_is_correct THEN 1 ELSE 0 END, NOW()
    )
    ON CONFLICT (student_id, country, subject, grade, course, topic)
    DO UPDATE SET
        questions_attempted = curriculum_progress.questions_attempted + 1,
        questions_correct = curriculum_progress.questions_correct + CASE WHEN p_is_correct THEN 1 ELSE 0 END,
        mastery_level = (curriculum_progress.questions_correct + CASE WHEN p_is_correct THEN 1 ELSE 0 END)::DECIMAL / (curriculum_progress.questions_attempted + 1),
        last_attempted = NOW(),
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql;

-- Add trigger for curriculum classification date
CREATE OR REPLACE FUNCTION update_curriculum_classification_date()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.us_curriculum_grade IS NOT NULL OR NEW.canada_curriculum_grade IS NOT NULL THEN
        NEW.curriculum_classification_date = NOW();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_curriculum_classification_date_trigger
    BEFORE UPDATE ON questions
    FOR EACH ROW
    EXECUTE FUNCTION update_curriculum_classification_date();
