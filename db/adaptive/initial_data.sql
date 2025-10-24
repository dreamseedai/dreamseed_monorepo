-- Organizations
INSERT INTO organizations (name, type, region)
VALUES ('Global Platform', 'Platform', 'N/A');

-- Topics
INSERT INTO topics (name, parent_topic_id) VALUES
('Mathematics', NULL),
('Probability and Statistics', 1),
('Algebra', 1);

-- Users
INSERT INTO users (email, password_hash, name, role, organization_id) VALUES
('teacher1@example.com', 'hashed_pw_123', 'Teacher One', 'teacher', 1),
('student1@example.com', 'hashed_pw_456', 'Student One', 'student', 1);

-- Exams
INSERT INTO exams (title, subject, description, max_questions, time_limit, created_by) VALUES
('Math Adaptive Test 2025', 'Mathematics', 'Adaptive math test example', 20, 60, 1);

-- Questions
INSERT INTO questions (content, solution_explanation, topic_id, difficulty, discrimination, guessing, org_id, created_by) VALUES
('If a fair coin is flipped twice, what is the probability of getting two heads?', 'There are 4 possible outcomes...', 2, 0.5, 1.0, 0.25, NULL, 1),
('Solve for x: 2x + 3 = 7', 'Isolate x: 2x = 4, so x = 2.', 3, -0.5, 0.8, 0.25, NULL, 1);

-- Choices for question 1
INSERT INTO choices (question_id, content, is_correct) VALUES
(1, '0.25', TRUE), (1, '0.5', FALSE), (1, '0.75', FALSE), (1, '0', FALSE);

-- Choices for question 2
INSERT INTO choices (question_id, content, is_correct) VALUES
(2, '2', TRUE), (2, '4', FALSE), (2, '1', FALSE), (2, '0', FALSE);

