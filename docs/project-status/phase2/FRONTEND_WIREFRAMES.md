# Frontend Wireframes - Aptitude Assessment UI/UX

**Version:** 1.0  
**Date:** November 24, 2025  
**Framework:** Next.js 14 (App Router)  
**UI Library:** shadcn/ui + Tailwind CSS  
**Charts:** Recharts / Chart.js  

---

## 🎨 Design Principles

### User Experience Goals

1. **Simplicity:** Clear instructions, one question at a time
2. **Progress Transparency:** Always show completion percentage
3. **Mobile-First:** Responsive design (320px - 1920px)
4. **Accessibility:** ARIA labels, keyboard navigation, screen reader support
5. **Speed:** < 3s page load, instant question transitions

---

### Color Scheme (Aligned with DreamSeed Brand)

```css
:root {
  --primary: #2563eb;        /* Blue - STEM */
  --secondary: #7c3aed;      /* Purple - Humanities */
  --accent: #f59e0b;         /* Orange - Arts */
  --success: #10b981;        /* Green - Practical */
  --background: #ffffff;
  --foreground: #0f172a;
  --muted: #f1f5f9;
  --border: #e2e8f0;
}
```

---

## 📱 Page 1: Landing Page

### Route: `/aptitude`

```
┌────────────────────────────────────────────────────────────┐
│  [Logo] DreamSeed AI                    [Profile] [Logout] │
├────────────────────────────────────────────────────────────┤
│                                                            │
│                    🎯 적성/진로 검사                         │
│                                                            │
│         당신에게 가장 적합한 전공과 진로를 찾아보세요          │
│                                                            │
│  ┌────────────────────────────────────────────────────┐   │
│  │                                                    │   │
│  │  📊 검사 구성                                       │   │
│  │                                                    │   │
│  │  • 총 40문항 (4개 영역)                            │   │
│  │  • 소요 시간: 약 8-12분                            │   │
│  │  • 언제든지 중단 가능 (자동 저장)                   │   │
│  │                                                    │   │
│  │  ✅ 측정 영역                                       │   │
│  │                                                    │   │
│  │  🔬 STEM (과학/공학/수학)                          │   │
│  │  📚 인문/언어 (문학/사회/철학)                      │   │
│  │  🎨 예술/창의 (디자인/예술/창작)                    │   │
│  │  🔧 실무/실용 (간호/실습/현장)                      │   │
│  │                                                    │   │
│  │  💡 결과 제공                                       │   │
│  │                                                    │   │
│  │  • 당신의 강점 차원 분석                            │   │
│  │  • 추천 전공 Top 5                                 │   │
│  │  • 관련 직업 및 진로 경로                           │   │
│  │  • 학업 능력과 결합한 맞춤 추천                     │   │
│  │                                                    │   │
│  └────────────────────────────────────────────────────┘   │
│                                                            │
│              [ 검사 시작하기 ] (Primary Button)             │
│                                                            │
│              [ 이전 결과 보기 ] (Secondary Link)            │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**Component Structure:**
```tsx
// app/aptitude/page.tsx
export default function AptitudeLanding() {
  return (
    <div className="container max-w-4xl mx-auto py-12">
      <h1 className="text-4xl font-bold text-center mb-4">
        적성/진로 검사
      </h1>
      <p className="text-lg text-muted-foreground text-center mb-12">
        당신에게 가장 적합한 전공과 진로를 찾아보세요
      </p>
      
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>📊 검사 구성</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2">
            <li>• 총 40문항 (4개 영역)</li>
            <li>• 소요 시간: 약 8-12분</li>
            <li>• 언제든지 중단 가능 (자동 저장)</li>
          </ul>
        </CardContent>
      </Card>
      
      <div className="flex justify-center gap-4">
        <Button size="lg" onClick={startSurvey}>
          검사 시작하기
        </Button>
        <Button variant="outline" size="lg" asChild>
          <Link href="/aptitude/history">이전 결과 보기</Link>
        </Button>
      </div>
    </div>
  );
}
```

---

## 📝 Page 2: Question Flow

### Route: `/aptitude/survey/[sessionId]`

```
┌────────────────────────────────────────────────────────────┐
│  [← 돌아가기]              Question 12 / 40      [00:04:23] │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Progress: ██████████░░░░░░░░░░░░░░░░░░░░░░  30%          │
│                                                            │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Q12. 누군가의 감정/의도를 파악하는 데 능숙한 편이다.        │
│                                                            │
│  ┌────────────────────────────────────────────────────┐   │
│  │                                                    │   │
│  │  ( ) 전혀 그렇지 않다                               │   │
│  │                                                    │   │
│  │  ( ) 그렇지 않다                                    │   │
│  │                                                    │   │
│  │  ( ) 보통이다                                       │   │
│  │                                                    │   │
│  │  ( ) 그렇다                                         │   │
│  │                                                    │   │
│  │  (•) 매우 그렇다  ✓ (Selected)                      │   │
│  │                                                    │   │
│  └────────────────────────────────────────────────────┘   │
│                                                            │
│  Tip: 정답은 없습니다. 솔직하게 응답해주세요.               │
│                                                            │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  [◀ 이전]                                    [다음 ▶]      │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**Mobile View (< 768px):**
```
┌──────────────────────────┐
│  [←]  Q12/40  [00:04:23] │
├──────────────────────────┤
│                          │
│  ████░░░░░░░░░░  30%     │
│                          │
│  Q12. 누군가의 감정/      │
│  의도를 파악하는 데       │
│  능숙한 편이다.           │
│                          │
│  ┌──────────────────┐    │
│  │                  │    │
│  │  ( ) 전혀 아니다  │    │
│  │  ( ) 아니다       │    │
│  │  ( ) 보통이다     │    │
│  │  ( ) 그렇다       │    │
│  │  (•) 매우 그렇다  │    │
│  │                  │    │
│  └──────────────────┘    │
│                          │
│  [◀ 이전]    [다음 ▶]    │
│                          │
└──────────────────────────┘
```

**Component Structure:**
```tsx
// app/aptitude/survey/[sessionId]/page.tsx
export default function SurveyQuestion({ params }) {
  const { sessionId } = params;
  const [currentQuestion, setCurrentQuestion] = useState(1);
  const [response, setResponse] = useState<number | null>(null);
  
  const question = QUESTIONS[currentQuestion - 1];
  
  const handleNext = async () => {
    // Save response
    await submitResponse(sessionId, currentQuestion, response);
    
    // Move to next question or results page
    if (currentQuestion < 40) {
      setCurrentQuestion(currentQuestion + 1);
      setResponse(null);
    } else {
      router.push(`/aptitude/results/${sessionId}`);
    }
  };
  
  return (
    <div className="container max-w-3xl mx-auto py-8">
      {/* Progress Bar */}
      <div className="mb-8">
        <div className="flex justify-between text-sm mb-2">
          <span>Question {currentQuestion} / 40</span>
          <Timer startTime={startTime} />
        </div>
        <Progress value={(currentQuestion / 40) * 100} />
      </div>
      
      {/* Question Text */}
      <Card className="mb-8">
        <CardContent className="pt-6">
          <h2 className="text-xl font-semibold mb-6">
            Q{currentQuestion}. {question.text}
          </h2>
          
          {/* Likert Options */}
          <RadioGroup value={response?.toString()} onValueChange={(v) => setResponse(parseInt(v))}>
            <div className="space-y-3">
              {LIKERT_OPTIONS.map((option) => (
                <div key={option.value} className="flex items-center space-x-3 p-3 border rounded-lg hover:bg-muted cursor-pointer">
                  <RadioGroupItem value={option.value.toString()} id={`opt-${option.value}`} />
                  <Label htmlFor={`opt-${option.value}`} className="flex-1 cursor-pointer">
                    {option.label}
                  </Label>
                </div>
              ))}
            </div>
          </RadioGroup>
          
          <p className="text-sm text-muted-foreground mt-4">
            💡 Tip: 정답은 없습니다. 솔직하게 응답해주세요.
          </p>
        </CardContent>
      </Card>
      
      {/* Navigation */}
      <div className="flex justify-between">
        <Button variant="outline" onClick={handlePrevious} disabled={currentQuestion === 1}>
          ◀ 이전
        </Button>
        <Button onClick={handleNext} disabled={response === null}>
          {currentQuestion === 40 ? "결과 보기" : "다음 ▶"}
        </Button>
      </div>
    </div>
  );
}
```

---

## 📊 Page 3: Results Page

### Route: `/aptitude/results/[sessionId]`

```
┌────────────────────────────────────────────────────────────┐
│  [Logo] DreamSeed AI                    [Profile] [Logout] │
├────────────────────────────────────────────────────────────┤
│                                                            │
│                🎉 적성 검사 완료!                            │
│                                                            │
│               당신의 적성 프로파일입니다                     │
│                                                            │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  📊 차원별 점수                                              │
│                                                            │
│  ┌────────────────────────────────────────────────────┐   │
│  │                   Radar Chart                      │   │
│  │                                                    │   │
│  │             STEM (0.70)                            │   │
│  │                /\                                  │   │
│  │               /  \                                 │   │
│  │              /    \                                │   │
│  │   Practical /______\ Humanities                    │   │
│  │    (0.50)             (-0.15)                      │   │
│  │              \      /                              │   │
│  │               \    /                               │   │
│  │                \  /                                │   │
│  │                 \/                                 │   │
│  │            Artistic (-0.25)                        │   │
│  │                                                    │   │
│  └────────────────────────────────────────────────────┘   │
│                                                            │
│  🎯 주요 강점                                                │
│                                                            │
│  ┌────────────────────────────────────────────────────┐   │
│  │  🔬 STEM (과학/공학) - 85th percentile              │   │
│  │  ────────────────────────────────────────          │   │
│  │  당신은 논리적 사고와 수리적 문제 해결에 강점이      │   │
│  │  있습니다. 이공계 분야에서 뛰어난 성과를 낼         │   │
│  │  가능성이 높습니다.                                 │   │
│  └────────────────────────────────────────────────────┘   │
│                                                            │
│  🏆 추천 전공 Top 5                                         │
│                                                            │
│  ┌────────────────────────────────────────────────────┐   │
│  │  1. 💻 컴퓨터 공학 / 소프트웨어 공학                 │   │
│  │     Fit Score: 78%  [████████████████░░]           │   │
│  │                                                    │   │
│  │     ✓ Strong STEM orientation (0.7)               │   │
│  │     ✓ Exceptional math ability (θ=1.2, top 12%)   │   │
│  │     ✓ Above-average science ability                │   │
│  │                                                    │   │
│  │     관련 직업:                                      │   │
│  │     • Software Engineer                           │   │
│  │     • Data Scientist                              │   │
│  │     • AI Researcher                               │   │
│  │                                                    │   │
│  │     [ 더 알아보기 ]                                 │   │
│  │                                                    │   │
│  ├────────────────────────────────────────────────────┤   │
│  │  2. ⚙️ 공학 (기계/전기/화학)                         │   │
│  │     Fit Score: 74%  [███████████████░░░]          │   │
│  │     (Collapsed - Click to expand)                 │   │
│  │                                                    │   │
│  ├────────────────────────────────────────────────────┤   │
│  │  3. 🔬 물리/수학                                    │   │
│  │     Fit Score: 69%  [█████████████░░░░░]          │   │
│  │     (Collapsed)                                   │   │
│  │                                                    │   │
│  ├────────────────────────────────────────────────────┤   │
│  │  4. 💼 경영학                                       │   │
│  │     Fit Score: 52%  [██████████░░░░░░░░]          │   │
│  │                                                    │   │
│  ├────────────────────────────────────────────────────┤   │
│  │  5. 🏛️ 건축학                                       │   │
│  │     Fit Score: 48%  [█████████░░░░░░░░░]          │   │
│  │                                                    │   │
│  └────────────────────────────────────────────────────┘   │
│                                                            │
│  💡 다음 단계                                                │
│                                                            │
│  ┌────────────────────────────────────────────────────┐   │
│  │  • 코딩/프로그래밍 입문 과정 수강 추천               │   │
│  │  • 컴퓨터 과학 동아리 활동 권장                      │   │
│  │  • 이공계 선배 멘토링 신청                           │   │
│  │  • 대학 전공 체험 프로그램 참여                      │   │
│  └────────────────────────────────────────────────────┘   │
│                                                            │
│  [ 📥 결과 PDF 다운로드 ]  [ 🔄 다시 검사하기 ]             │
│  [ 📊 대시보드로 돌아가기 ]                                 │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**Component Structure:**
```tsx
// app/aptitude/results/[sessionId]/page.tsx
export default async function ResultsPage({ params }) {
  const { sessionId } = params;
  const results = await getAptitudeResults(sessionId);
  
  return (
    <div className="container max-w-5xl mx-auto py-12">
      {/* Header */}
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold mb-2">🎉 적성 검사 완료!</h1>
        <p className="text-muted-foreground">당신의 적성 프로파일입니다</p>
      </div>
      
      {/* Radar Chart */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>📊 차원별 점수</CardTitle>
        </CardHeader>
        <CardContent>
          <RadarChart data={results.dimension_scores} />
        </CardContent>
      </Card>
      
      {/* Dominant Dimension */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>🎯 주요 강점</CardTitle>
        </CardHeader>
        <CardContent>
          <DominantDimensionCard dimension={results.dominant_dimension} />
        </CardContent>
      </Card>
      
      {/* Recommendations */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>🏆 추천 전공 Top 5</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {results.recommendations.map((rec, idx) => (
            <RecommendationCard key={idx} rank={idx + 1} recommendation={rec} />
          ))}
        </CardContent>
      </Card>
      
      {/* Next Steps */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>💡 다음 단계</CardTitle>
        </CardHeader>
        <CardContent>
          <NextStepsChecklist recommendations={results.recommendations} />
        </CardContent>
      </Card>
      
      {/* Actions */}
      <div className="flex justify-center gap-4">
        <Button variant="outline" onClick={downloadPDF}>
          📥 결과 PDF 다운로드
        </Button>
        <Button variant="outline" asChild>
          <Link href="/aptitude">🔄 다시 검사하기</Link>
        </Button>
        <Button asChild>
          <Link href="/dashboard">📊 대시보드로 돌아가기</Link>
        </Button>
      </div>
    </div>
  );
}
```

---

## 🎨 Key Components

### RadarChart Component

```tsx
// components/aptitude/RadarChart.tsx
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, ResponsiveContainer } from 'recharts';

export function AptitudeRadarChart({ data }: { data: Record<string, number> }) {
  const chartData = [
    { dimension: 'STEM', score: (data.STEM + 1) * 50 },  // Convert [-1,1] to [0,100]
    { dimension: 'Humanities', score: (data.Humanities + 1) * 50 },
    { dimension: 'Artistic', score: (data.Artistic + 1) * 50 },
    { dimension: 'Practical', score: (data.Practical + 1) * 50 },
  ];
  
  return (
    <ResponsiveContainer width="100%" height={400}>
      <RadarChart data={chartData}>
        <PolarGrid />
        <PolarAngleAxis dataKey="dimension" />
        <Radar
          name="Your Profile"
          dataKey="score"
          stroke="#2563eb"
          fill="#2563eb"
          fillOpacity={0.6}
        />
      </RadarChart>
    </ResponsiveContainer>
  );
}
```

---

### RecommendationCard Component

```tsx
// components/aptitude/RecommendationCard.tsx
export function RecommendationCard({ rank, recommendation }) {
  const [expanded, setExpanded] = useState(rank === 1);
  
  return (
    <div className="border rounded-lg p-4">
      <div className="flex items-start justify-between cursor-pointer" onClick={() => setExpanded(!expanded)}>
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-2xl font-bold">#{rank}</span>
            <h3 className="text-xl font-semibold">{recommendation.major}</h3>
          </div>
          
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Fit Score:</span>
            <Progress value={recommendation.fit_score * 100} className="flex-1" />
            <span className="font-semibold">{Math.round(recommendation.fit_score * 100)}%</span>
          </div>
        </div>
        
        <ChevronDown className={`transition-transform ${expanded ? 'rotate-180' : ''}`} />
      </div>
      
      {expanded && (
        <div className="mt-4 space-y-3">
          {/* Reasons */}
          <div>
            <h4 className="font-semibold mb-2">왜 추천하나요?</h4>
            <ul className="space-y-1">
              {recommendation.reasons.map((reason, i) => (
                <li key={i} className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-green-500 mt-0.5" />
                  <span className="text-sm">{reason}</span>
                </li>
              ))}
            </ul>
          </div>
          
          {/* Careers */}
          <div>
            <h4 className="font-semibold mb-2">관련 직업</h4>
            <div className="flex flex-wrap gap-2">
              {recommendation.careers.map((career, i) => (
                <Badge key={i} variant="secondary">{career}</Badge>
              ))}
            </div>
          </div>
          
          <Button variant="outline" size="sm">더 알아보기</Button>
        </div>
      )}
    </div>
  );
}
```

---

## 📊 Page 4: Profile Dashboard Integration

### Route: `/dashboard` (Updated)

```
┌────────────────────────────────────────────────────────────┐
│  DreamSeed AI Dashboard                 [Profile] [Logout] │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Welcome back, 김철수!                                      │
│                                                            │
│  ┌───────────────────┐  ┌───────────────────┐             │
│  │ 📚 Academic Tests │  │ 🎯 Aptitude Test  │             │
│  ├───────────────────┤  ├───────────────────┤             │
│  │                   │  │                   │             │
│  │ Math:    θ = 1.2  │  │ Last: 2025-11-20  │             │
│  │ English: θ = -0.3 │  │                   │             │
│  │ Science: θ = 0.5  │  │ 🔬 STEM: 0.70     │             │
│  │                   │  │ 📚 Hum:  -0.15    │             │
│  │ [Take Test]       │  │ 🎨 Art:  -0.25    │             │
│  │                   │  │ 🔧 Prac: 0.50     │             │
│  │                   │  │                   │             │
│  │                   │  │ [Retake Test]     │             │
│  └───────────────────┘  └───────────────────┘             │
│                                                            │
│  ┌────────────────────────────────────────────────────┐   │
│  │ 🏆 Your Recommended Majors (Combined Insights)     │   │
│  ├────────────────────────────────────────────────────┤   │
│  │                                                    │   │
│  │  1. 💻 Computer Science (78% fit)                 │   │
│  │     Strong STEM + High Math Ability               │   │
│  │                                                    │   │
│  │  2. ⚙️ Engineering (74% fit)                       │   │
│  │  3. 🔬 Physics/Math (69% fit)                      │   │
│  │                                                    │   │
│  │  [ View Full Analysis ]                           │   │
│  └────────────────────────────────────────────────────┘   │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## 📄 Related Documents

- [PHASE2_APTITUDE_ASSESSMENT.md](./PHASE2_APTITUDE_ASSESSMENT.md) - Complete backend spec
- [LIKERT_QUESTIONS_40.md](./LIKERT_QUESTIONS_40.md) - Question bank
- [COMBINED_RECOMMENDATION_MODEL.md](./COMBINED_RECOMMENDATION_MODEL.md) - Recommendation logic
- [PHASE1_FRONTEND_STRUCTURE.md](../phase1/PHASE1_FRONTEND_STRUCTURE.md) - Overall frontend architecture

---

**Status:** 📋 **DESIGN COMPLETE**  
**Next Step:** Implement UI components in Next.js  

---

**End of Frontend Wireframes**
