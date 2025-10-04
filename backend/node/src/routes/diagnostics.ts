import { Router, Request, Response } from "express";

const router = Router();

// Types matching frontend
interface DiagnosticRequest {
  userId: string;
  context: {
    country: string;
    grade: string;
    goal: string;
  };
  evidence?: {
    quizAnswers?: Array<{ id: string; answer: string }>;
    pastScores?: Record<string, number>;
  };
}

interface DiagnosticResponse {
  userId: string;
  summary: string;
  weaknesses: string[];
  recommendedModules: string[];
  recommendedProblems: Array<{ id: string; title: string }>;
  nextWeekPlan: Array<{ day: string; tasks: string[] }>;
  tokenUsage?: { prompt: number; completion: number; total: number };
}

router.post("/run", (req: Request, res: Response) => {
  try {
    const { userId, context, evidence }: DiagnosticRequest = req.body || {};
    const country = context?.country || "US";
    const grade = context?.grade || "G11";
    const goal = context?.goal || "SAT_1500_PLUS";

    // Demo logic based on goal
    const isSAT = String(goal).includes("SAT");
    const isAP = String(goal).includes("AP");
    const isTOEFL = String(goal).includes("TOEFL") || String(goal).includes("IELTS");

    let weaknesses: string[];
    let recommendedModules: string[];
    let recommendedProblems: Array<{ id: string; title: string }>;

    if (isSAT) {
      weaknesses = ["algebraic_manipulation", "reading_inference", "time_management"];
      recommendedModules = ["Math", "English / ELA", "Exams & Admissions"];
      recommendedProblems = [
        { id: "sat-math-001", title: "Quadratic completion practice" },
        { id: "sat-rw-014", title: "Paired passages: inference & evidence" },
        { id: "sat-math-045", title: "Systems of equations word problems" }
      ];
    } else if (isAP) {
      weaknesses = ["concept_application", "essay_structure", "time_pressure"];
      recommendedModules = ["AP Courses", "Test Prep", "Writing"];
      recommendedProblems = [
        { id: "ap-bio-001", title: "Cell structure and function" },
        { id: "ap-chem-012", title: "Stoichiometry calculations" },
        { id: "ap-lang-008", title: "Rhetorical analysis essay" }
      ];
    } else if (isTOEFL) {
      weaknesses = ["listening_comprehension", "speaking_fluency", "academic_vocabulary"];
      recommendedModules = ["English", "Test Prep", "Speaking"];
      recommendedProblems = [
        { id: "toefl-list-001", title: "Academic lecture comprehension" },
        { id: "toefl-speak-003", title: "Independent speaking practice" },
        { id: "toefl-read-015", title: "Academic reading passages" }
      ];
    } else {
      weaknesses = ["general_preparation", "test_strategy", "time_management"];
      recommendedModules = ["Test Prep", "Study Skills", "Exams & Admissions"];
      recommendedProblems = [
        { id: "gen-prep-001", title: "General test preparation" },
        { id: "gen-strat-002", title: "Test-taking strategies" },
        { id: "gen-time-003", title: "Time management practice" }
      ];
    }

    // Generate next week plan
    const nextWeekPlan = [
      {
        day: "Monday",
        tasks: [
          `30m ${goal} practice session`,
          "Review previous mistakes",
          "Set weekly goals"
        ]
      },
      {
        day: "Wednesday",
        tasks: [
          `Mock ${goal} section practice`,
          "Focus on identified weaknesses",
          "Track progress"
        ]
      },
      {
        day: "Saturday",
        tasks: [
          `Full-length ${goal} practice test`,
          "Post-test analysis and review",
          "Plan next week's focus areas"
        ]
      }
    ];

    // Generate summary
    const summary = `Diagnostic completed for ${country}/${grade} student. Goal: ${goal}. ` +
      `Identified ${weaknesses.length} key areas for improvement. ` +
      `Recommended ${recommendedModules.length} learning modules and ${recommendedProblems.length} practice problems.`;

    const response: DiagnosticResponse = {
      userId: userId || "unknown",
      summary,
      weaknesses,
      recommendedModules,
      recommendedProblems,
      nextWeekPlan,
      tokenUsage: { prompt: 0, completion: 0, total: 0 }
    };

    res.json(response);
  } catch (error) {
    console.error("Diagnostic processing error:", error);
    res.status(500).json({
      error: "Diagnostic processing failed",
      message: error instanceof Error ? error.message : "Unknown error"
    });
  }
});

export default router;


