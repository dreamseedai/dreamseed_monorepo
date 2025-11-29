// portal_front/src/config/portalApps.ts

export type PortalAppConfig = {
  id: "student" | "teacher" | "tutor" | "parent";
  label: string;
  description: string;
  path: string;      // 포털 내 경로
  iframeSrc: string; // 실제 앱 URL
  roles: string[];   // 접근 가능한 user.role (백엔드 User.role 값 기준)
};

const STUDENT_APP_URL =
  process.env.NEXT_PUBLIC_STUDENT_APP_URL ?? "http://localhost:3001";
const TEACHER_APP_URL =
  process.env.NEXT_PUBLIC_TEACHER_APP_URL ?? "http://localhost:3002";
const TUTOR_APP_URL =
  process.env.NEXT_PUBLIC_TUTOR_APP_URL ?? "http://localhost:3003";
const PARENT_APP_URL =
  process.env.NEXT_PUBLIC_PARENT_APP_URL ?? "http://localhost:3004";

export const PORTAL_APPS: PortalAppConfig[] = [
  {
    id: "student",
    label: "Student Portal",
    description: "학생용 학습 대시보드 및 시험",
    path: "/portal/student",
    iframeSrc: STUDENT_APP_URL,
    roles: ["student"],
  },
  {
    id: "teacher",
    label: "Teacher Portal",
    description: "학교 선생님용 학급 관리 및 리포트 코멘트",
    path: "/portal/teacher",
    iframeSrc: TEACHER_APP_URL,
    roles: ["teacher"], // 학교/학원 튜터 구분은 백엔드 org_type으로 처리
  },
  {
    id: "tutor",
    label: "Tutor Portal",
    description: "학원/과외 선생님용 우선순위 리스트 및 코멘트",
    path: "/portal/tutor",
    iframeSrc: TUTOR_APP_URL,
    roles: ["teacher"], // 동일 role이지만, 실제 API에서 org_type으로 필터링
  },
  {
    id: "parent",
    label: "Parent Portal",
    description: "학부모용 자녀 리포트 PDF 다운로드",
    path: "/portal/parent",
    iframeSrc: PARENT_APP_URL,
    roles: ["parent"],
  },
];
