import { z } from 'zod';

// User related schemas
export const UserSchema = z.object({
  id: z.string().uuid(),
  email: z.string().email(),
  firstName: z.string().min(1),
  lastName: z.string().min(1),
  createdAt: z.date(),
  updatedAt: z.date(),
});

export const OnboardingFormSchema = z.object({
  firstName: z.string().min(1, 'First name is required'),
  lastName: z.string().min(1, 'Last name is required'),
  email: z.string().email('Invalid email address'),
  careerGoals: z.array(z.string()).min(1, 'At least one career goal is required'),
  learningPreferences: z.object({
    preferredPace: z.enum(['self-paced', 'structured', 'intensive']),
    learningStyle: z.enum(['visual', 'auditory', 'kinesthetic', 'reading']),
    timeCommitment: z.enum(['1-3 hours/week', '4-7 hours/week', '8+ hours/week']),
  }),
  technicalBackground: z.enum(['beginner', 'intermediate', 'advanced']),
});

// Career related schemas
export const CareerPathSchema = z.object({
  id: z.string().uuid(),
  title: z.string(),
  description: z.string(),
  requiredSkills: z.array(z.string()),
  estimatedDuration: z.string(),
  difficulty: z.enum(['beginner', 'intermediate', 'advanced']),
});

// Learning related schemas
export const LearningModuleSchema = z.object({
  id: z.string().uuid(),
  title: z.string(),
  description: z.string(),
  content: z.string(),
  type: z.enum(['video', 'article', 'exercise', 'quiz']),
  duration: z.number(), // in minutes
  difficulty: z.enum(['beginner', 'intermediate', 'advanced']),
  tags: z.array(z.string()),
});

// Progress related schemas
export const ProgressSchema = z.object({
  id: z.string().uuid(),
  userId: z.string().uuid(),
  moduleId: z.string().uuid(),
  status: z.enum(['not-started', 'in-progress', 'completed']),
  completionPercentage: z.number().min(0).max(100),
  timeSpent: z.number(), // in minutes
  lastAccessed: z.date(),
});

// AI Orchestrator schemas
export const AIRequestSchema = z.object({
  type: z.enum(['career-guidance', 'learning-recommendation', 'content-generation']),
  context: z.record(z.any()),
  userId: z.string().uuid(),
});

export const AIResponseSchema = z.object({
  type: z.string(),
  data: z.any(),
  confidence: z.number().min(0).max(1),
  metadata: z.record(z.any()).optional(),
});

// Type exports
export type User = z.infer<typeof UserSchema>;
export type OnboardingForm = z.infer<typeof OnboardingFormSchema>;
export type CareerPath = z.infer<typeof CareerPathSchema>;
export type LearningModule = z.infer<typeof LearningModuleSchema>;
export type Progress = z.infer<typeof ProgressSchema>;
export type AIRequest = z.infer<typeof AIRequestSchema>;
export type AIResponse = z.infer<typeof AIResponseSchema>;