/**
 * useDashboard.ts
 * 
 * React Query hooks for dashboard data fetching
 * 
 * Usage:
 *   const { data, isLoading, error } = useTeacherClassExams(classId);
 */

"use client";

import { useQuery } from "@tanstack/react-query";
import {
  getTeacherClassExams,
  getTeacherStudentExams,
  getParentChildExams,
  getClassStatistics,
} from "../api/dashboard";

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Teacher Hooks
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

export const useTeacherClassExams = (classId?: string) =>
  useQuery({
    queryKey: ["teacher-class-exams", classId],
    queryFn: () => {
      if (!classId) throw new Error("classId is required");
      return getTeacherClassExams(classId);
    },
    enabled: !!classId,
  });

export const useTeacherStudentExams = (studentId?: string) =>
  useQuery({
    queryKey: ["teacher-student-exams", studentId],
    queryFn: () => {
      if (!studentId) throw new Error("studentId is required");
      return getTeacherStudentExams(studentId);
    },
    enabled: !!studentId,
  });

export const useClassStatistics = (classId?: string) =>
  useQuery({
    queryKey: ["class-statistics", classId],
    queryFn: () => {
      if (!classId) throw new Error("classId is required");
      return getClassStatistics(classId);
    },
    enabled: !!classId,
  });

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Parent Hooks
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

export const useParentChildExams = (studentId?: string) =>
  useQuery({
    queryKey: ["parent-child-exams", studentId],
    queryFn: () => {
      if (!studentId) throw new Error("studentId is required");
      return getParentChildExams(studentId);
    },
    enabled: !!studentId,
  });
