# PDF Lambda - Exam Result Renderer

## Purpose
Generate branded PDF reports for exam results with score breakdown and topic analysis.

## Components

### 1. `exam_renderer.py` (NEW)
Main PDF rendering logic for exam results:
- **Function**: `render_exam_pdf(result_data, tutor_brand, logo_url, page_format, korean_font_path) -> bytes`
- **Input**: Exam result JSON from `/api/seedtest/exams/{session_id}/result`
- **Output**: PDF bytes (reportlab-generated)
- **Features**:
  - Branded header with tutor/school name
  - Student info (session ID, user ID, date)
  - Score summary (scaled score, correct/total, percentile)
  - Topic breakdown table (accuracy per topic)
  - Recommendations list
  - A4/Letter format support
  - Korean font support (optional)

### 2. `lambda_function.py` (EXISTING)
Generic PDF Lambda for chart-based reports (keep for backward compatibility)

### 3. `test_pdf_gen.py` (NEW)
Local test script for PDF generation validation

## API Integration

### Endpoint: `GET /api/seedtest/exams/{session_id}/result/pdf`
**Status**: ✅ Implemented (was 501 stub)

**Query Parameters**:
- `brand` (optional): Tutor/school brand name (default: "DreamSeed")
- `format` (optional): Page format - "A4" or "Letter" (default: "A4")

**Response**:
- **Success (200)**: `application/pdf` stream with inline disposition
- **Not Found (404)**: Result not found for session
- **Bad Request (400)**: Exam not completed yet
- **Server Error (500)**: PDF generation failed

**Example**:
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8002/api/seedtest/exams/abc123/result/pdf?brand=MySchool&format=A4" \
  --output exam_result.pdf
```

## Dependencies

### Python Packages (requirements.txt)
- `reportlab` - PDF generation
- `Pillow` - Image processing (for logo support in future)

### Lambda Layer (if deployed to AWS)
Requires custom layer with:
- reportlab
- Pillow
- Optional: Korean TrueType font (NotoSansCJK)

## Development

### Local Testing
```bash
# Install dependencies
pip install -r requirements.txt

# Run test script
python test_pdf_gen.py

# Output: test_exam_result.pdf, test_exam_result_letter.pdf
```

### Docker Build (for Lambda)
```bash
cd infra/pdf_lambda
docker build -t exam-pdf-renderer .
```

## V1 Status

| Feature | Status | Notes |
|---------|--------|-------|
| PDF rendering | ✅ Complete | reportlab-based, 191 lines |
| API endpoint | ✅ Complete | Replaced 501 stub |
| Local test | ✅ Complete | test_pdf_gen.py |
| Brand customization | ✅ Complete | Query param `brand` |
| A4/Letter format | ✅ Complete | Query param `format` |
| Korean font | 🟡 Optional | Requires TTF file in Lambda layer |
| Logo support | ❌ V2 | logo_url parameter exists but not implemented |
| Lambda deployment | 🟡 Pending | Needs Layer + SAM template update |

## Next Steps (Post-V1)

1. **Logo Integration** (V2)
   - Download logo from URL
   - Embed in PDF header
   - Cache logos in S3

2. **Advanced Charts** (V2)
   - Topic performance radar chart
   - Time-on-task histogram
   - Difficulty vs accuracy scatter plot

3. **Multi-page Reports** (V2)
   - Question-by-question breakdown
   - Answer key (if teacher requests)
   - Historical performance comparison

4. **Lambda Optimization** (V2)
   - Pre-warm Lambda to reduce cold starts
   - S3 caching of generated PDFs (keyed by session_id + brand)
   - CloudFront CDN for presigned URLs

## TTFP Impact

**Critical Path Blocker Resolved**: ✅
- Before: 501 stub → no PDF generation → tutors cannot get first PDF
- After: Working PDF renderer → tutors can download branded exam results
- **Impact**: Direct enabler for "First PDF in ≤60분" milestone

**Estimated Time Saved**:
- Without PDF: TTFP = ∞ (impossible to complete)
- With PDF: TTFP = 15-45 minutes (depending on onboarding flow)

---

*Last Updated*: 2025-10-31  
*Version*: 1.0 (V1 Complete)  
*Lines of Code*: 191 (exam_renderer.py) + 59 (endpoint update) = 250 lines total
