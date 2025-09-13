import React, { useState } from 'react';
import { Button, Input, Card } from '@dreamseed/shared-ui';
import { OnboardingFormSchema } from '@dreamseed/shared-types';
import type { OnboardingForm } from '@dreamseed/shared-types';

interface OnboardingFormProps {
  onSubmit: (data: OnboardingForm) => void;
}

export const OnboardingFormComponent: React.FC<OnboardingFormProps> = ({ onSubmit }) => {
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    careerGoals: [] as string[],
    learningPreferences: {
      preferredPace: 'self-paced' as const,
      learningStyle: 'visual' as const,
      timeCommitment: '4-7 hours/week' as const
    },
    technicalBackground: 'beginner' as const
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [currentGoal, setCurrentGoal] = useState('');

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const handlePreferenceChange = (field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      learningPreferences: {
        ...prev.learningPreferences,
        [field]: value
      }
    }));
  };

  const addCareerGoal = () => {
    if (currentGoal.trim()) {
      setFormData(prev => ({
        ...prev,
        careerGoals: [...prev.careerGoals, currentGoal.trim()]
      }));
      setCurrentGoal('');
    }
  };

  const removeCareerGoal = (index: number) => {
    setFormData(prev => ({
      ...prev,
      careerGoals: prev.careerGoals.filter((_, i) => i !== index)
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      const validatedData = OnboardingFormSchema.parse(formData);
      onSubmit(validatedData);
    } catch (error: any) {
      const validationErrors: Record<string, string> = {};
      if (error.errors) {
        error.errors.forEach((err: any) => {
          const path = err.path.join('.');
          validationErrors[path] = err.message;
        });
      }
      setErrors(validationErrors);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6">
      <Card title="Welcome to DreamSeed Portal">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Personal Information */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                First Name
              </label>
              <Input
                type="text"
                value={formData.firstName}
                onChange={(e) => handleInputChange('firstName', e.target.value)}
                placeholder="Enter your first name"
                error={errors.firstName}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Last Name
              </label>
              <Input
                type="text"
                value={formData.lastName}
                onChange={(e) => handleInputChange('lastName', e.target.value)}
                placeholder="Enter your last name"
                error={errors.lastName}
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Email Address
            </label>
            <Input
              type="email"
              value={formData.email}
              onChange={(e) => handleInputChange('email', e.target.value)}
              placeholder="Enter your email address"
              error={errors.email}
            />
          </div>

          {/* Career Goals */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Career Goals
            </label>
            <div className="flex gap-2 mb-2">
              <Input
                type="text"
                value={currentGoal}
                onChange={(e) => setCurrentGoal(e.target.value)}
                placeholder="Add a career goal"
                className="flex-1"
              />
              <Button type="button" onClick={addCareerGoal}>
                Add
              </Button>
            </div>
            {formData.careerGoals.length > 0 && (
              <div className="space-y-2">
                {formData.careerGoals.map((goal, index) => (
                  <div key={index} className="flex items-center justify-between bg-gray-50 p-2 rounded">
                    <span>{goal}</span>
                    <button
                      type="button"
                      onClick={() => removeCareerGoal(index)}
                      className="text-red-600 hover:text-red-800"
                    >
                      Remove
                    </button>
                  </div>
                ))}
              </div>
            )}
            {errors.careerGoals && (
              <p className="mt-1 text-sm text-red-600">{errors.careerGoals}</p>
            )}
          </div>

          {/* Learning Preferences */}
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">Learning Preferences</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Preferred Pace
                </label>
                <select
                  value={formData.learningPreferences.preferredPace}
                  onChange={(e) => handlePreferenceChange('preferredPace', e.target.value)}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="self-paced">Self-paced</option>
                  <option value="structured">Structured</option>
                  <option value="intensive">Intensive</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Learning Style
                </label>
                <select
                  value={formData.learningPreferences.learningStyle}
                  onChange={(e) => handlePreferenceChange('learningStyle', e.target.value)}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="visual">Visual</option>
                  <option value="auditory">Auditory</option>
                  <option value="kinesthetic">Kinesthetic</option>
                  <option value="reading">Reading</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Time Commitment
                </label>
                <select
                  value={formData.learningPreferences.timeCommitment}
                  onChange={(e) => handlePreferenceChange('timeCommitment', e.target.value)}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="1-3 hours/week">1-3 hours/week</option>
                  <option value="4-7 hours/week">4-7 hours/week</option>
                  <option value="8+ hours/week">8+ hours/week</option>
                </select>
              </div>
            </div>
          </div>

          {/* Technical Background */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Technical Background
            </label>
            <select
              value={formData.technicalBackground}
              onChange={(e) => handleInputChange('technicalBackground', e.target.value)}
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="beginner">Beginner</option>
              <option value="intermediate">Intermediate</option>
              <option value="advanced">Advanced</option>
            </select>
          </div>

          <div className="flex justify-end">
            <Button type="submit" size="lg">
              Complete Onboarding
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
};