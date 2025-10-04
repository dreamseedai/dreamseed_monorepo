
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { MathLive } from 'mathlive';
import { Hint, BookOpen, Clock, Target } from 'lucide-react';

interface QuestionProps {
  question: {
    id: string;
    title: string;
    content: {
      question_en: string;
      question_ko?: string;
      question_zh?: string;
      answer_en?: string;
      solution_en?: string;
      explanation_en?: string;
      hints: Array<{
        id: string;
        hint_text_en: string;
        hint_text_ko?: string;
        hint_text_zh?: string;
        hint_order: number;
      }>;
    };
    metadata: {
      subject: string;
      grade_level: number;
      difficulty_level: string;
      difficulty_score: number;
      topics: string[];
      question_type: string;
    };
    math_content: {
      has_mathml: boolean;
      latex_expressions: string[];
      math_complexity: string;
    };
    adaptive_learning?: {
      prerequisites: string[];
      learning_objectives: string[];
      assessment_criteria: string[];
      min_difficulty: number;
      max_difficulty: number;
      optimal_difficulty: number;
      success_indicators: string[];
    };
    quality_metrics: {
      content_quality_score: number;
      math_accuracy_score: number;
      pedagogical_value_score: number;
      accessibility_score: number;
    };
  };
  onAnswer: (answer: string, timeSpent: number) => void;
  onHint: (hintIndex: number) => void;
  language?: 'en' | 'ko' | 'zh';
}

export const EnhancedQuestionComponent: React.FC<QuestionProps> = ({
  question,
  onAnswer,
  onHint,
  language = 'en'
}) => {
  const [studentAnswer, setStudentAnswer] = useState('');
  const [timeSpent, setTimeSpent] = useState(0);
  const [hintsUsed, setHintsUsed] = useState<number[]>([]);
  const [showSolution, setShowSolution] = useState(false);
  const [showExplanation, setShowExplanation] = useState(false);
  const [startTime] = useState(Date.now());

  useEffect(() => {
    const timer = setInterval(() => {
      setTimeSpent(Math.floor((Date.now() - startTime) / 1000));
    }, 1000);

    return () => clearInterval(timer);
  }, [startTime]);

  const getContent = (field: string) => {
    const content = question.content as any;
    return content[`${field}_${language}`] || content[`${field}_en`] || '';
  };

  const getDifficultyColor = (level: string) => {
    switch (level) {
      case 'beginner': return 'bg-green-100 text-green-800';
      case 'intermediate': return 'bg-yellow-100 text-yellow-800';
      case 'advanced': return 'bg-orange-100 text-orange-800';
      case 'expert': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getQualityColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const handleHintClick = (hintIndex: number) => {
    if (!hintsUsed.includes(hintIndex)) {
      setHintsUsed([...hintsUsed, hintIndex]);
      onHint(hintIndex);
    }
  };

  const handleSubmitAnswer = () => {
    onAnswer(studentAnswer, timeSpent);
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      {/* Question Header */}
      <Card>
        <CardHeader>
          <div className="flex justify-between items-start">
            <div>
              <CardTitle className="text-2xl font-bold">
                {question.title}
              </CardTitle>
              <div className="flex gap-2 mt-2">
                <Badge className={getDifficultyColor(question.metadata.difficulty_level)}>
                  {question.metadata.difficulty_level}
                </Badge>
                <Badge variant="outline">
                  Grade {question.metadata.grade_level}
                </Badge>
                <Badge variant="outline">
                  {question.metadata.subject}
                </Badge>
              </div>
            </div>
            <div className="text-right">
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <Clock className="w-4 h-4" />
                {Math.floor(timeSpent / 60)}:{(timeSpent % 60).toString().padStart(2, '0')}
              </div>
            </div>
          </div>
        </CardHeader>
        
        <CardContent>
          {/* Question Content */}
          <div className="prose max-w-none mb-6">
            <div 
              className="text-lg leading-relaxed"
              dangerouslySetInnerHTML={{ __html: getContent('question') }}
            />
          </div>

          {/* Math Content */}
          {question.math_content.has_mathml && (
            <div className="mb-6 p-4 bg-gray-50 rounded-lg">
              <h4 className="font-semibold mb-2">Mathematical Expressions:</h4>
              {question.math_content.latex_expressions.map((latex, index) => (
                <div key={index} className="mb-2">
                  <MathLive
                    readOnly
                    value={latex}
                    className="math-expression"
                  />
                </div>
              ))}
            </div>
          )}

          {/* Answer Input */}
          <div className="mb-6">
            <label className="block text-sm font-medium mb-2">
              Your Answer:
            </label>
            <textarea
              value={studentAnswer}
              onChange={(e) => setStudentAnswer(e.target.value)}
              className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows={4}
              placeholder="Enter your answer here..."
            />
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3 mb-6">
            <Button onClick={handleSubmitAnswer} className="bg-blue-600 hover:bg-blue-700">
              Submit Answer
            </Button>
            <Button 
              variant="outline" 
              onClick={() => setShowSolution(!showSolution)}
            >
              <BookOpen className="w-4 h-4 mr-2" />
              {showSolution ? 'Hide' : 'Show'} Solution
            </Button>
          </div>

          {/* Hints */}
          {question.content.hints.length > 0 && (
            <div className="mb-6">
              <h4 className="font-semibold mb-3 flex items-center">
                <Hint className="w-5 h-5 mr-2" />
                Hints ({hintsUsed.length}/{question.content.hints.length})
              </h4>
              <div className="space-y-2">
                {question.content.hints.map((hint, index) => (
                  <div key={hint.id} className="flex items-start gap-3">
                    <Button
                      size="sm"
                      variant={hintsUsed.includes(index) ? "default" : "outline"}
                      onClick={() => handleHintClick(index)}
                      disabled={hintsUsed.includes(index)}
                      className="mt-1"
                    >
                      Hint {index + 1}
                    </Button>
                    {hintsUsed.includes(index) && (
                      <div className="flex-1 p-3 bg-blue-50 rounded-lg">
                        <div dangerouslySetInnerHTML={{ 
                          __html: hint[`hint_text_${language}`] || hint.hint_text_en 
                        }} />
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Solution */}
          {showSolution && getContent('solution') && (
            <div className="mb-6 p-4 bg-green-50 rounded-lg">
              <h4 className="font-semibold mb-2 text-green-800">Solution:</h4>
              <div 
                className="prose max-w-none text-green-700"
                dangerouslySetInnerHTML={{ __html: getContent('solution') }}
              />
            </div>
          )}

          {/* Explanation */}
          {showExplanation && getContent('explanation') && (
            <div className="mb-6 p-4 bg-purple-50 rounded-lg">
              <h4 className="font-semibold mb-2 text-purple-800">Explanation:</h4>
              <div 
                className="prose max-w-none text-purple-700"
                dangerouslySetInnerHTML={{ __html: getContent('explanation') }}
              />
            </div>
          )}
        </CardContent>
      </Card>

      {/* Adaptive Learning Info */}
      {question.adaptive_learning && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Target className="w-5 h-5 mr-2" />
              Learning Objectives
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {question.adaptive_learning.learning_objectives.length > 0 && (
                <div>
                  <h5 className="font-semibold mb-2">What you'll learn:</h5>
                  <ul className="list-disc list-inside space-y-1">
                    {question.adaptive_learning.learning_objectives.map((objective, index) => (
                      <li key={index} className="text-sm">{objective}</li>
                    ))}
                  </ul>
                </div>
              )}
              
              {question.adaptive_learning.prerequisites.length > 0 && (
                <div>
                  <h5 className="font-semibold mb-2">Prerequisites:</h5>
                  <div className="flex flex-wrap gap-2">
                    {question.adaptive_learning.prerequisites.map((prereq, index) => (
                      <Badge key={index} variant="secondary">{prereq}</Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Quality Metrics */}
      <Card>
        <CardHeader>
          <CardTitle>Content Quality</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span>Content Quality</span>
                <span className={getQualityColor(question.quality_metrics.content_quality_score)}>
                  {(question.quality_metrics.content_quality_score * 100).toFixed(0)}%
                </span>
              </div>
              <Progress value={question.quality_metrics.content_quality_score * 100} />
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span>Math Accuracy</span>
                <span className={getQualityColor(question.quality_metrics.math_accuracy_score)}>
                  {(question.quality_metrics.math_accuracy_score * 100).toFixed(0)}%
                </span>
              </div>
              <Progress value={question.quality_metrics.math_accuracy_score * 100} />
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span>Pedagogical Value</span>
                <span className={getQualityColor(question.quality_metrics.pedagogical_value_score)}>
                  {(question.quality_metrics.pedagogical_value_score * 100).toFixed(0)}%
                </span>
              </div>
              <Progress value={question.quality_metrics.pedagogical_value_score * 100} />
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span>Accessibility</span>
                <span className={getQualityColor(question.quality_metrics.accessibility_score)}>
                  {(question.quality_metrics.accessibility_score * 100).toFixed(0)}%
                </span>
              </div>
              <Progress value={question.quality_metrics.accessibility_score * 100} />
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
