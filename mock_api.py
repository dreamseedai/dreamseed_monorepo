# mock_api.py
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from uvicorn import run

app = FastAPI()

# CORS 설정 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 도메인에서 접근 허용
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)

SAMPLE = {
    434: {"id":434,"que_id":434,"que_class":"math","que_grade":"G10","que_level":2,
          "que_en_title":"\\( a^2 + b^2 = c^2 \\)",
          "question_en":"$\\frac{1}{x}$ is undefined at x = 0.",
          "solution_en":"Use Pythagorean theorem.",
          "hint_en":"Right triangle.",
          "que_en_resource":"C1=CC=CC=C1",  # 예: SMILES (벤젠)
          "que_status":1,"que_createddate":"2020-01-01","que_modifieddate":"2020-01-02"},
    435: {"id":435,"que_id":435,"que_class":"chem","que_grade":"G11","que_level":3,
          "que_en_title":"$E=mc^2$",
          "question_en":"\\(\\int_0^1 x^2 dx = 1/3\\)",
          "solution_en":"Power rule.",
          "hint_en":"Use \\(x^{n+1}/(n+1)\\).",
          "que_en_resource":"CCO", "que_status":1,
          "que_createddate":"2020-02-01","que_modifieddate":"2020-03-01"},
    11384: {"id":11384,"que_id":11384,"que_class":"chem","que_grade":"G10","que_level":2,
            "que_en_title":"Non-ionic detergents",
            "question_en":"Following type of non-ionic detergents are present in liquid detergents, emulsifying agents and wetting agents. Label the hydrophilic and hydrophobic parts in the molecule. Identify the functional group (s) present in the molecule.<br /><img src=\"/images/editor/11384-31.png\" alt=\"\" />",
            "solution_en":"Functional groups present in the molecule are:<br />(i) Ether, and<br />(ii) primary alcoholic group<br /><br />Non-ionic detergents are molecules that contain both hydrophobic and hydrophilic parts, which allows them to interact with both water and oil-based substances.<br /><img src=\"/images/editor/11384-32.png\" alt=\"\" />",
            "hint_en":"Look at the molecular structure and identify the polar and non-polar regions.",
            "que_en_resource":"",
            "que_status":1,"que_createddate":"2020-01-01","que_modifieddate":"2020-01-02"},
}

@app.get("/api/questions/admin/questions")
def list_questions(page: int = 1, page_size: int = 100, original_id: int | None = None):
    if original_id is not None and original_id in SAMPLE:
        return [SAMPLE[original_id]]
    return list(SAMPLE.values())[:page_size]

@app.get("/api/questions/{qid}")
def item(qid: int):
    return SAMPLE.get(qid, JSONResponse({"detail":"not found"}, 404))

if __name__ == "__main__":
    run(app, host="127.0.0.1", port=8008)
