# UX Layer: Student Interface Components

**Implementation Guide 12 of 14**

This guide covers the student-facing UI components including dashboard, assessment taking interface, AI tutor chatbot, and gamification features.

---

## Table of Contents

1. [Overview](#overview)
2. [Student Dashboard](#student-dashboard)
3. [Assessment Taking Interface](#assessment-taking-interface)
4. [AI Tutor Chatbot](#ai-tutor-chatbot)
5. [Learning Progress Visualization](#learning-progress-visualization)
6. [Gamification Features](#gamification-features)
7. [Responsive Design](#responsive-design)

---

## Overview

### Goals

The student interface aims to:

- **Personalized Learning**: Show tailored content based on student ability and goals
- **Engagement**: Use gamification to motivate continuous learning
- **Clarity**: Present information clearly without overwhelming the student
- **Accessibility**: Ensure all students can use the platform effectively
- **Real-time Feedback**: Provide immediate feedback during practice sessions

### Key User Flows

1. **Login** → **Dashboard** → **View Progress**
2. **Dashboard** → **Start Assessment** → **Take Test** → **View Results**
3. **Dashboard** → **AI Tutor** → **Ask Questions** → **Learn**
4. **Dashboard** → **Reports** → **Review Detailed Analysis**

---

## Student Dashboard

### Component Structure

```typescript
// app/[locale]/(student)/dashboard/page.tsx
import { Suspense } from "react";
import { WelcomeHeader } from "@/components/features/dashboard/WelcomeHeader";
import { RecentScores } from "@/components/features/dashboard/RecentScores";
import { WeaknessAreas } from "@/components/features/dashboard/WeaknessAreas";
import { RecommendedActivities } from "@/components/features/dashboard/RecommendedActivities";
import { GoalProgress } from "@/components/features/dashboard/GoalProgress";
import { QuickActions } from "@/components/features/dashboard/QuickActions";

export default function StudentDashboard() {
  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Welcome Section */}
      <WelcomeHeader />

      {/* Key Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <Suspense fallback={<SkeletonCard />}>
          <RecentScores />
        </Suspense>

        <Suspense fallback={<SkeletonCard />}>
          <WeaknessAreas />
        </Suspense>

        <Suspense fallback={<SkeletonCard />}>
          <GoalProgress />
        </Suspense>
      </div>

      {/* Recommended Activities */}
      <Suspense fallback={<SkeletonCard />}>
        <RecommendedActivities />
      </Suspense>

      {/* Quick Actions */}
      <QuickActions />
    </div>
  );
}
```

### Welcome Header Component

```typescript
// components/features/dashboard/WelcomeHeader.tsx
"use client";

import { useTranslation } from "next-i18next";
import { useAuthStore } from "@/lib/store/authStore";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

export function WelcomeHeader() {
  const { t } = useTranslation("dashboard");
  const user = useAuthStore((state) => state.user);

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return t("greeting.morning");
    if (hour < 18) return t("greeting.afternoon");
    return t("greeting.evening");
  };

  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-4">
        <Avatar className="h-16 w-16">
          <AvatarImage src={user?.avatar} alt={user?.name} />
          <AvatarFallback>{user?.name?.[0]}</AvatarFallback>
        </Avatar>
        <div>
          <h1 className="text-3xl font-bold">
            {getGreeting()}, {user?.name}!
          </h1>
          <p className="text-muted-foreground">{t("readyToLearn")}</p>
        </div>
      </div>

      <div className="text-right">
        <p className="text-sm text-muted-foreground">{t("currentStreak")}</p>
        <p className="text-2xl font-bold text-dreamseed-orange">🔥 7 days</p>
      </div>
    </div>
  );
}
```

### Recent Scores Card

```typescript
// components/features/dashboard/RecentScores.tsx
"use client";

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api/client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TrendingUp, TrendingDown } from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface ScoreData {
  date: string;
  score: number;
  subject: string;
}

export function RecentScores() {
  const { data: scores, isLoading } = useQuery({
    queryKey: ["recent-scores"],
    queryFn: () => apiClient.get<ScoreData[]>("/api/students/me/recent-scores"),
  });

  if (isLoading) return <SkeletonCard />;

  const latestScore = scores?.[0]?.score || 0;
  const previousScore = scores?.[1]?.score || 0;
  const improvement = latestScore - previousScore;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium">Recent Assessment</CardTitle>
        {improvement > 0 ? (
          <TrendingUp className="h-4 w-4 text-green-600" />
        ) : (
          <TrendingDown className="h-4 w-4 text-red-600" />
        )}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{latestScore} points</div>
        <p className="text-xs text-muted-foreground">
          {improvement > 0 ? "+" : ""}
          {improvement} from last test
        </p>

        {/* Mini Chart */}
        <div className="mt-4 h-[80px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={scores}>
              <XAxis dataKey="date" hide />
              <YAxis hide />
              <Tooltip />
              <Line
                type="monotone"
                dataKey="score"
                stroke="#0066CC"
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
```

### Weakness Areas Card

```typescript
// components/features/dashboard/WeaknessAreas.tsx
"use client";

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api/client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { AlertCircle } from "lucide-react";

interface WeaknessArea {
  topic: string;
  accuracy: number;
  questionsAttempted: number;
}

export function WeaknessAreas() {
  const { data: weaknesses, isLoading } = useQuery({
    queryKey: ["weakness-areas"],
    queryFn: () =>
      apiClient.get<WeaknessArea[]>("/api/students/me/weakness-areas"),
  });

  if (isLoading) return <SkeletonCard />;

  const topWeakness = weaknesses?.[0];

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium">Areas to Improve</CardTitle>
        <AlertCircle className="h-4 w-4 text-orange-600" />
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {weaknesses?.slice(0, 3).map((weakness) => (
            <div key={weakness.topic}>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">{weakness.topic}</span>
                <span className="text-sm text-muted-foreground">
                  {weakness.accuracy}%
                </span>
              </div>
              <Progress value={weakness.accuracy} className="h-2" />
              <p className="text-xs text-muted-foreground mt-1">
                {weakness.questionsAttempted} questions attempted
              </p>
            </div>
          ))}
        </div>

        {topWeakness && (
          <p className="text-xs text-muted-foreground mt-4">
            💡 Focus on <strong>{topWeakness.topic}</strong> to boost your
            score!
          </p>
        )}
      </CardContent>
    </Card>
  );
}
```

### Goal Progress Component

```typescript
// components/features/dashboard/GoalProgress.tsx
"use client";

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api/client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Target } from "lucide-react";

interface Goal {
  id: string;
  title: string;
  targetScore: number;
  currentScore: number;
  progress: number;
}

export function GoalProgress() {
  const { data: goal, isLoading } = useQuery({
    queryKey: ["student-goal"],
    queryFn: () => apiClient.get<Goal>("/api/students/me/goal"),
  });

  if (isLoading) return <SkeletonCard />;
  if (!goal) return null;

  const pointsNeeded = goal.targetScore - goal.currentScore;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium">Your Goal</CardTitle>
        <Target className="h-4 w-4 text-dreamseed-blue" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{goal.title}</div>
        <p className="text-xs text-muted-foreground">
          Target: {goal.targetScore} points
        </p>

        <div className="mt-4">
          <Progress value={goal.progress} className="h-3" />
          <div className="flex justify-between mt-2">
            <span className="text-xs text-muted-foreground">
              Current: {goal.currentScore}
            </span>
            <span className="text-xs font-medium">{goal.progress}%</span>
          </div>
        </div>

        {pointsNeeded > 0 && (
          <p className="text-xs text-muted-foreground mt-4">
            📈 <strong>{pointsNeeded} points</strong> to reach your goal!
          </p>
        )}
      </CardContent>
    </Card>
  );
}
```

---

## Assessment Taking Interface

### Assessment Flow

```typescript
// app/[locale]/(student)/assessments/[id]/take/page.tsx
"use client";

import { useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { useAssessmentStore } from "@/lib/store/assessmentStore";
import { useStartAssessment, useSubmitAnswer } from "@/lib/api/assessments";
import { QuestionDisplay } from "@/components/features/assessment/QuestionDisplay";
import { ProgressIndicator } from "@/components/features/assessment/ProgressIndicator";
import { Timer } from "@/components/features/assessment/Timer";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";

export default function TakeAssessmentPage() {
  const params = useParams();
  const router = useRouter();
  const assessmentId = params.id as string;

  const {
    sessionId,
    currentQuestion,
    currentQuestionIndex,
    totalQuestions,
    startAssessment,
    endAssessment,
  } = useAssessmentStore();

  const { mutate: start, isLoading: isStarting } = useStartAssessment();
  const { mutate: submitAnswer } = useSubmitAnswer();

  // Start assessment on mount
  useEffect(() => {
    if (!sessionId) {
      start(assessmentId, {
        onSuccess: (data) => {
          startAssessment(data.sessionId, data.totalQuestions);
        },
      });
    }
  }, [assessmentId, sessionId, start, startAssessment]);

  const handleSubmitAnswer = (response: number) => {
    if (!sessionId || !currentQuestion) return;

    submitAnswer(
      {
        sessionId,
        questionId: currentQuestion.id,
        response,
      },
      {
        onSuccess: (data) => {
          if (data.nextQuestion) {
            useAssessmentStore
              .getState()
              .setCurrentQuestion(data.nextQuestion, currentQuestionIndex + 1);
            useAssessmentStore.getState().updateAbility(data.estimatedAbility);
          } else {
            // Assessment complete
            endAssessment();
            router.push(`/assessments/${assessmentId}/results`);
          }
        },
      }
    );
  };

  if (isStarting || !currentQuestion) {
    return <div>Loading assessment...</div>;
  }

  return (
    <div className="container max-w-4xl mx-auto p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <ProgressIndicator
          current={currentQuestionIndex + 1}
          total={totalQuestions}
        />
        <Timer />
      </div>

      {/* Question */}
      <QuestionDisplay
        question={currentQuestion}
        onSubmit={handleSubmitAnswer}
      />

      {/* Actions */}
      <div className="flex justify-between mt-6">
        <ConfirmDialog
          title="Pause Assessment"
          description="Are you sure you want to pause? Your progress will be saved."
          onConfirm={() => router.push("/dashboard")}
        >
          <button className="px-4 py-2 text-sm border rounded-md">Pause</button>
        </ConfirmDialog>

        <ConfirmDialog
          title="End Assessment Early"
          description="You have answered {currentQuestionIndex}/{totalQuestions} questions. End now?"
          onConfirm={() => {
            endAssessment();
            router.push(`/assessments/${assessmentId}/results`);
          }}
        >
          <button className="px-4 py-2 text-sm border border-red-600 text-red-600 rounded-md">
            End Early
          </button>
        </ConfirmDialog>
      </div>
    </div>
  );
}
```

### Question Display Component

```typescript
// components/features/assessment/QuestionDisplay.tsx
"use client";

import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { MathJax } from "better-react-mathjax";

interface Question {
  id: string;
  content: string;
  options: string[];
  difficulty?: number;
}

interface QuestionDisplayProps {
  question: Question;
  onSubmit: (response: number) => void;
  showDifficulty?: boolean;
}

export function QuestionDisplay({
  question,
  onSubmit,
  showDifficulty = false,
}: QuestionDisplayProps) {
  const [selectedOption, setSelectedOption] = useState<number | null>(null);

  const handleSubmit = () => {
    if (selectedOption !== null) {
      onSubmit(selectedOption);
      setSelectedOption(null); // Reset for next question
    }
  };

  const getDifficultyLabel = (difficulty: number) => {
    if (difficulty < 0.3) return "Easy";
    if (difficulty < 0.7) return "Medium";
    return "Hard";
  };

  return (
    <Card className="w-full">
      <CardContent className="p-6">
        {/* Difficulty Badge (optional) */}
        {showDifficulty && question.difficulty !== undefined && (
          <div className="mb-4">
            <span className="inline-block px-2 py-1 text-xs font-semibold rounded-md bg-blue-100 text-blue-800">
              {getDifficultyLabel(question.difficulty)}
            </span>
          </div>
        )}

        {/* Question Content (with LaTeX support) */}
        <div className="mb-6">
          <h2 className="text-xl font-semibold mb-4">Question</h2>
          <MathJax>
            <div
              className="prose max-w-none"
              dangerouslySetInnerHTML={{ __html: question.content }}
            />
          </MathJax>
        </div>

        {/* Options */}
        <div className="space-y-4">
          <h3 className="text-sm font-medium text-muted-foreground">
            Select your answer:
          </h3>
          <RadioGroup
            value={selectedOption?.toString()}
            onValueChange={(val) => setSelectedOption(parseInt(val))}
          >
            {question.options.map((option, index) => (
              <div
                key={index}
                className={`flex items-center space-x-3 p-4 border rounded-lg cursor-pointer transition-colors hover:bg-accent ${
                  selectedOption === index ? "border-primary bg-accent" : ""
                }`}
                onClick={() => setSelectedOption(index)}
              >
                <RadioGroupItem
                  value={index.toString()}
                  id={`option-${index}`}
                />
                <Label
                  htmlFor={`option-${index}`}
                  className="flex-1 cursor-pointer"
                >
                  <MathJax>
                    <span dangerouslySetInnerHTML={{ __html: option }} />
                  </MathJax>
                </Label>
              </div>
            ))}
          </RadioGroup>
        </div>

        {/* Submit Button */}
        <div className="mt-6">
          <Button
            onClick={handleSubmit}
            disabled={selectedOption === null}
            className="w-full"
            size="lg"
          >
            Submit Answer
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
```

### Progress Indicator

```typescript
// components/features/assessment/ProgressIndicator.tsx
"use client";

import { Progress } from "@/components/ui/progress";

interface ProgressIndicatorProps {
  current: number;
  total: number;
}

export function ProgressIndicator({ current, total }: ProgressIndicatorProps) {
  const percentage = (current / total) * 100;

  return (
    <div className="w-full max-w-md">
      <div className="flex justify-between items-center mb-2">
        <span className="text-sm font-medium">
          Question {current} of {total}
        </span>
        <span className="text-sm text-muted-foreground">
          {Math.round(percentage)}%
        </span>
      </div>
      <Progress value={percentage} className="h-2" />
    </div>
  );
}
```

### Timer Component

```typescript
// components/features/assessment/Timer.tsx
"use client";

import { useEffect, useState } from "react";
import { useAssessmentStore } from "@/lib/store/assessmentStore";
import { Clock } from "lucide-react";

export function Timer() {
  const timeRemaining = useAssessmentStore((state) => state.timeRemaining);
  const updateTimeRemaining = useAssessmentStore(
    (state) => state.updateTimeRemaining
  );

  const [seconds, setSeconds] = useState(timeRemaining || 0);

  useEffect(() => {
    if (seconds <= 0) return;

    const interval = setInterval(() => {
      setSeconds((prev) => {
        const newTime = prev - 1;
        updateTimeRemaining(newTime);
        return newTime;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [seconds, updateTimeRemaining]);

  const formatTime = (totalSeconds: number) => {
    const minutes = Math.floor(totalSeconds / 60);
    const secs = totalSeconds % 60;
    return `${minutes}:${secs.toString().padStart(2, "0")}`;
  };

  const isLowTime = seconds < 300; // Less than 5 minutes

  return (
    <div
      className={`flex items-center gap-2 px-4 py-2 rounded-md ${
        isLowTime ? "bg-red-100 text-red-700" : "bg-muted"
      }`}
    >
      <Clock className="h-4 w-4" />
      <span className="font-mono font-semibold">{formatTime(seconds)}</span>
    </div>
  );
}
```

---

## AI Tutor Chatbot

### Floating Chat Button

```typescript
// components/features/tutor/FloatingChatButton.tsx
"use client";

import { useState } from "react";
import { MessageCircle, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ChatInterface } from "./ChatInterface";
import { motion, AnimatePresence } from "framer-motion";

export function FloatingChatButton() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      {/* Floating Button */}
      <motion.div
        className="fixed bottom-6 right-6 z-50"
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ delay: 1, type: "spring", stiffness: 260, damping: 20 }}
      >
        <Button
          size="lg"
          className="rounded-full h-14 w-14 shadow-lg"
          onClick={() => setIsOpen(!isOpen)}
        >
          {isOpen ? (
            <X className="h-6 w-6" />
          ) : (
            <MessageCircle className="h-6 w-6" />
          )}
        </Button>
      </motion.div>

      {/* Chat Panel */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            className="fixed bottom-24 right-6 z-40 w-96 h-[600px] shadow-2xl rounded-lg overflow-hidden"
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            transition={{ type: "spring", stiffness: 300, damping: 30 }}
          >
            <ChatInterface onClose={() => setIsOpen(false)} />
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
```

### Chat Interface

```typescript
// components/features/tutor/ChatInterface.tsx
"use client";

import { useState, useRef, useEffect } from "react";
import { useMutation } from "@tanstack/react-query";
import { apiClient } from "@/lib/api/client";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { MessageBubble } from "./MessageBubble";
import { SuggestedQuestions } from "./SuggestedQuestions";
import { Send, Loader2 } from "lucide-react";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

interface ChatInterfaceProps {
  onClose: () => void;
}

export function ChatInterface({ onClose }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      role: "assistant",
      content: "Hi! I'm your AI tutor. How can I help you today?",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { mutate: sendMessage, isLoading } = useMutation({
    mutationFn: (message: string) =>
      apiClient.post<{ response: string }>("/api/tutor/chat", {
        message,
        history: messages,
      }),
    onSuccess: (data) => {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          role: "assistant",
          content: data.response,
          timestamp: new Date(),
        },
      ]);
    },
  });

  const handleSend = () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    sendMessage(input);
    setInput("");
  };

  const handleSuggestedQuestion = (question: string) => {
    setInput(question);
  };

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <Card className="h-full flex flex-col bg-background">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b">
        <div className="flex items-center gap-2">
          <div className="h-2 w-2 bg-green-500 rounded-full animate-pulse" />
          <h3 className="font-semibold">AI Tutor</h3>
        </div>
        <button
          onClick={onClose}
          className="text-muted-foreground hover:text-foreground"
        >
          ✕
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}

        {isLoading && (
          <div className="flex items-center gap-2 text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span className="text-sm">AI is thinking...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Questions (only show at start) */}
      {messages.length <= 2 && (
        <div className="px-4 pb-2">
          <SuggestedQuestions onSelect={handleSuggestedQuestion} />
        </div>
      )}

      {/* Input */}
      <div className="p-4 border-t">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex gap-2"
        >
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask me anything..."
            disabled={isLoading}
          />
          <Button
            type="submit"
            size="icon"
            disabled={!input.trim() || isLoading}
          >
            <Send className="h-4 w-4" />
          </Button>
        </form>
      </div>
    </Card>
  );
}
```

### Message Bubble

```typescript
// components/features/tutor/MessageBubble.tsx
"use client";

import { MathJax } from "better-react-mathjax";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { ThumbsUp, ThumbsDown } from "lucide-react";
import { useState } from "react";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

export function MessageBubble({ message }: { message: Message }) {
  const [feedback, setFeedback] = useState<"up" | "down" | null>(null);

  const handleFeedback = (type: "up" | "down") => {
    setFeedback(type);
    // TODO: Send feedback to API
  };

  const isUser = message.role === "user";

  return (
    <div className={`flex gap-3 ${isUser ? "flex-row-reverse" : ""}`}>
      {/* Avatar */}
      {!isUser && (
        <Avatar className="h-8 w-8">
          <AvatarImage src="/ai-tutor-avatar.png" />
          <AvatarFallback>AI</AvatarFallback>
        </Avatar>
      )}

      {/* Message Content */}
      <div className={`flex-1 ${isUser ? "flex justify-end" : ""}`}>
        <div
          className={`inline-block max-w-[80%] p-3 rounded-lg ${
            isUser ? "bg-primary text-primary-foreground" : "bg-muted"
          }`}
        >
          <MathJax>
            <div
              className="prose prose-sm max-w-none"
              dangerouslySetInnerHTML={{ __html: message.content }}
            />
          </MathJax>
        </div>

        {/* Feedback (assistant messages only) */}
        {!isUser && (
          <div className="flex items-center gap-2 mt-1 ml-1">
            <button
              onClick={() => handleFeedback("up")}
              className={`p-1 rounded hover:bg-accent ${
                feedback === "up" ? "text-green-600" : "text-muted-foreground"
              }`}
            >
              <ThumbsUp className="h-3 w-3" />
            </button>
            <button
              onClick={() => handleFeedback("down")}
              className={`p-1 rounded hover:bg-accent ${
                feedback === "down" ? "text-red-600" : "text-muted-foreground"
              }`}
            >
              <ThumbsDown className="h-3 w-3" />
            </button>
          </div>
        )}

        {/* Timestamp */}
        <span className="text-xs text-muted-foreground ml-1 mt-1 block">
          {message.timestamp.toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </span>
      </div>
    </div>
  );
}
```

### Suggested Questions

```typescript
// components/features/tutor/SuggestedQuestions.tsx
"use client";

import { Button } from "@/components/ui/button";

const SUGGESTIONS = [
  "Explain this problem step by step",
  "Give me a hint for this question",
  "What topics should I focus on?",
  "How can I improve my score?",
];

interface SuggestedQuestionsProps {
  onSelect: (question: string) => void;
}

export function SuggestedQuestions({ onSelect }: SuggestedQuestionsProps) {
  return (
    <div className="space-y-2">
      <p className="text-xs text-muted-foreground">Suggested questions:</p>
      <div className="flex flex-wrap gap-2">
        {SUGGESTIONS.map((suggestion) => (
          <Button
            key={suggestion}
            variant="outline"
            size="sm"
            onClick={() => onSelect(suggestion)}
            className="text-xs"
          >
            {suggestion}
          </Button>
        ))}
      </div>
    </div>
  );
}
```

---

## Learning Progress Visualization

### Progress Chart Component

```typescript
// components/features/dashboard/ProgressChart.tsx
"use client";

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api/client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

interface ProgressData {
  date: string;
  math: number;
  science: number;
  english: number;
}

export function ProgressChart() {
  const { data: progressData, isLoading } = useQuery({
    queryKey: ["progress-chart"],
    queryFn: () => apiClient.get<ProgressData[]>("/api/students/me/progress"),
  });

  if (isLoading) return <div>Loading chart...</div>;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Learning Progress (Last 30 Days)</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={progressData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line
              type="monotone"
              dataKey="math"
              stroke="#0066CC"
              strokeWidth={2}
            />
            <Line
              type="monotone"
              dataKey="science"
              stroke="#00CC66"
              strokeWidth={2}
            />
            <Line
              type="monotone"
              dataKey="english"
              stroke="#FF9933"
              strokeWidth={2}
            />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
```

---

## Gamification Features

### Achievements Component

```typescript
// components/features/gamification/Achievements.tsx
"use client";

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api/client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Trophy, Star, Zap } from "lucide-react";

interface Achievement {
  id: string;
  title: string;
  description: string;
  icon: string;
  unlockedAt?: Date;
  progress?: number;
}

export function Achievements() {
  const { data: achievements, isLoading } = useQuery({
    queryKey: ["achievements"],
    queryFn: () =>
      apiClient.get<Achievement[]>("/api/students/me/achievements"),
  });

  if (isLoading) return <div>Loading...</div>;

  const getIcon = (iconName: string) => {
    switch (iconName) {
      case "trophy":
        return <Trophy className="h-8 w-8 text-yellow-500" />;
      case "star":
        return <Star className="h-8 w-8 text-blue-500" />;
      case "zap":
        return <Zap className="h-8 w-8 text-orange-500" />;
      default:
        return <Trophy className="h-8 w-8" />;
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Achievements</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {achievements?.map((achievement) => (
            <div
              key={achievement.id}
              className={`p-4 rounded-lg border-2 ${
                achievement.unlockedAt
                  ? "border-yellow-500 bg-yellow-50"
                  : "border-muted bg-muted/20"
              }`}
            >
              <div className="flex flex-col items-center text-center gap-2">
                {getIcon(achievement.icon)}
                <h4 className="font-semibold text-sm">{achievement.title}</h4>
                <p className="text-xs text-muted-foreground">
                  {achievement.description}
                </p>
                {achievement.unlockedAt ? (
                  <Badge variant="secondary">Unlocked!</Badge>
                ) : (
                  achievement.progress !== undefined && (
                    <span className="text-xs">
                      {achievement.progress}% complete
                    </span>
                  )
                )}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
```

### Leaderboard Component

```typescript
// components/features/gamification/Leaderboard.tsx
"use client";

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api/client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Medal } from "lucide-react";

interface LeaderboardEntry {
  rank: number;
  userId: string;
  name: string;
  avatar?: string;
  score: number;
  isCurrentUser: boolean;
}

export function Leaderboard() {
  const { data: leaderboard, isLoading } = useQuery({
    queryKey: ["leaderboard"],
    queryFn: () => apiClient.get<LeaderboardEntry[]>("/api/leaderboard"),
  });

  if (isLoading) return <div>Loading...</div>;

  const getMedalColor = (rank: number) => {
    if (rank === 1) return "text-yellow-500";
    if (rank === 2) return "text-gray-400";
    if (rank === 3) return "text-orange-600";
    return "";
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Class Leaderboard</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {leaderboard?.slice(0, 10).map((entry) => (
            <div
              key={entry.userId}
              className={`flex items-center justify-between p-3 rounded-lg ${
                entry.isCurrentUser
                  ? "bg-primary/10 border border-primary"
                  : "hover:bg-muted"
              }`}
            >
              <div className="flex items-center gap-3">
                <div className="w-8 text-center">
                  {entry.rank <= 3 ? (
                    <Medal className={`h-5 w-5 ${getMedalColor(entry.rank)}`} />
                  ) : (
                    <span className="font-semibold text-muted-foreground">
                      #{entry.rank}
                    </span>
                  )}
                </div>
                <Avatar className="h-8 w-8">
                  <AvatarImage src={entry.avatar} />
                  <AvatarFallback>{entry.name[0]}</AvatarFallback>
                </Avatar>
                <span className="font-medium">{entry.name}</span>
                {entry.isCurrentUser && (
                  <span className="text-xs text-primary font-semibold">
                    (You)
                  </span>
                )}
              </div>
              <span className="font-bold">{entry.score} pts</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
```

---

## Responsive Design

### Mobile-First Approach

```typescript
// Example: Responsive Dashboard Layout
export default function ResponsiveDashboard() {
  return (
    <div className="container mx-auto p-4 sm:p-6">
      {/* Single column on mobile, 2 on tablet, 3 on desktop */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
        <RecentScores />
        <WeaknessAreas />
        <GoalProgress />
      </div>

      {/* Stack vertically on mobile */}
      <div className="mt-6 space-y-4 md:space-y-6">
        <RecommendedActivities />
        <ProgressChart />
      </div>
    </div>
  );
}
```

### Breakpoints (Tailwind)

```typescript
// Tailwind breakpoints used:
// sm: 640px  (tablet portrait)
// md: 768px  (tablet landscape)
// lg: 1024px (desktop)
// xl: 1280px (large desktop)
// 2xl: 1536px (extra large)

// Example usage:
<div className="text-sm md:text-base lg:text-lg">
  Responsive text size
</div>

<div className="hidden md:block">
  Hidden on mobile, visible on tablet+
</div>
```

---

## Best Practices

### 1. Student Engagement

- **Immediate Feedback**: Show instant results in practice mode
- **Progress Visualization**: Use charts and progress bars
- **Gamification**: Badges, achievements, leaderboards
- **Positive Reinforcement**: Celebrate improvements

### 2. Accessibility

- **Keyboard Navigation**: All interactive elements accessible via keyboard
- **Screen Reader Support**: Proper ARIA labels
- **Color Contrast**: WCAG AA compliance (4.5:1 minimum)
- **Font Size**: Adjustable text size (base 16px)

### 3. Performance

- **Lazy Loading**: Load heavy components on demand
- **Code Splitting**: Separate bundles for different routes
- **Image Optimization**: Use Next.js Image component
- **Caching**: Cache API responses with React Query

### 4. User Experience

- **Loading States**: Show skeletons while loading
- **Error Handling**: User-friendly error messages
- **Confirmation Dialogs**: Confirm destructive actions
- **Auto-save**: Save progress automatically

---

## Next Steps

Continue to:

- **[Guide 13: Teacher & Admin Console](./13-ux-teacher-admin-console.md)** - R Shiny implementation
- **[Guide 14: Accessibility & Performance](./14-ux-accessibility-performance.md)** - WCAG compliance and optimization

---

**Last Updated**: November 9, 2025  
**Version**: 1.0  
**Author**: DreamSeedAI Development Team
