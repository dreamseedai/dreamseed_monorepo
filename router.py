from fastapi import FastAPI, Request
import httpx, re
import time
import json
from datetime import datetime

app = FastAPI()
OPENAI = "/v1/chat/completions"

BACKENDS = {
    "general": ("http://127.0.0.1:8000", "mistralai/Mistral-7B-Instruct-v0.3"),
    "code":    ("http://127.0.0.1:8001", "Qwen/Qwen2.5-Coder-7B-Instruct"),
    "fast":    ("http://127.0.0.1:8002", "microsoft/Phi-3-mini-4k-instruct"),
}

def pick_model(prompt: str) -> tuple[str, str]:
    # DreamSeedAI 특화: 코드/SQL/프로그래밍 키워드 → code
    if re.search(r"```|class |def |function |SELECT |import |코드|프로그래밍", prompt, re.I):
        return "code", "code_kw"
    # 짧고 빠른 응답 필요 → fast
    if len(prompt) < 120 or re.search(r"빠른|신속|짧게", prompt):
        return "fast", "fast_len" if len(prompt) < 120 else "fast_kw"
    # 기본 가이드/지식 → general
    return "general", "general_kw"

@app.post("/v1/chat/completions")
async def chat(req: Request):
    start_time = time.time()
    body = await req.json()
    user_msgs = [m.get("content","") for m in body.get("messages",[]) if m.get("role")=="user"]
    prompt = " ".join(user_msgs)
    lane, hint = pick_model(prompt)
    base, model = BACKENDS.get(lane, BACKENDS["general"])
    body["model"] = model
    
    # 토큰 수 계산 (간단한 추정)
    tokens_in = int(len(prompt.split()) * 1.3)  # 대략적인 토큰 수
    hint_with_len = f"{hint}|len={len(prompt)}"
    
    # 백엔드 다운 시 자동 폴백 (강화된 타임아웃/재시도)
    timeout = httpx.Timeout(connect=10, read=90, write=90, pool=10)
    error_flag = 0
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(base + OPENAI, json=body,
                                  headers={"Authorization": req.headers.get("authorization","")})
            r.raise_for_status()
            response_data = r.json()
            
            # 응답 토큰 수 계산
            response_text = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
            tokens_out = int(len(response_text.split()) * 1.3)
            
            # 로그 기록 (라우팅 품질 로깅)
            latency_ms = int((time.time() - start_time) * 1000)
            log_entry = f"ts={datetime.now().isoformat()} lane={lane} model=\"{model}\" latency_ms={latency_ms} tokens_in={tokens_in} tokens_out={tokens_out} err={error_flag} hint=\"{hint_with_len}\""
            
            with open("/tmp/router.log", "a") as f:
                f.write(log_entry + "\n")
            
            return response_data
    except Exception as e:
        print(f"백엔드 {lane} 실패, 폴백 시도: {e}")
        error_flag = 1
        # 일반 → 빠른, 코드 → 일반 순으로 폴백
        alt_lane = {"general": "fast", "code": "general", "fast": "general"}[lane]
        base, model = BACKENDS[alt_lane]
        body["model"] = model
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                r = await client.post(base + OPENAI, json=body,
                                      headers={"Authorization": req.headers.get("authorization","")})
                r.raise_for_status()
                response_data = r.json()
                
                # 응답 토큰 수 계산
                response_text = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
                tokens_out = int(len(response_text.split()) * 1.3)
                
                # 로그 기록 (폴백)
                latency_ms = int((time.time() - start_time) * 1000)
                log_entry = f"ts={datetime.now().isoformat()} lane={alt_lane} model=\"{model}\" latency_ms={latency_ms} tokens_in={tokens_in} tokens_out={tokens_out} err={error_flag} hint=\"{hint_with_len}\""
                
                with open("/tmp/router.log", "a") as f:
                    f.write(log_entry + "\n")
                
                return response_data
        except Exception as e2:
            print(f"폴백 백엔드 {alt_lane}도 실패: {e2}")
            error_flag = 1
            # 최종 폴백: general로 강제 전환
            if alt_lane != "general":
                base, model = BACKENDS["general"]
                body["model"] = model
                try:
                    async with httpx.AsyncClient(timeout=timeout) as client:
                        r = await client.post(base + OPENAI, json=body,
                                              headers={"Authorization": req.headers.get("authorization","")})
                        response_data = r.json()
                        
                        # 응답 토큰 수 계산
                        response_text = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
                        tokens_out = int(len(response_text.split()) * 1.3)
                        
                        # 로그 기록 (최종 폴백)
                        latency_ms = int((time.time() - start_time) * 1000)
                        log_entry = f"ts={datetime.now().isoformat()} lane=general model=\"{model}\" latency_ms={latency_ms} tokens_in={tokens_in} tokens_out={tokens_out} err={error_flag} hint=\"{hint_with_len}\""
                        
                        with open("/tmp/router.log", "a") as f:
                            f.write(log_entry + "\n")
                        
                        return response_data
                except Exception as e3:
                    # 최종 실패 로그
                    latency_ms = int((time.time() - start_time) * 1000)
                    log_entry = f"ts={datetime.now().isoformat()} lane=general model=\"{model}\" latency_ms={latency_ms} tokens_in={tokens_in} tokens_out=0 err=1 hint=\"{hint_with_len}\""
                    
                    with open("/tmp/router.log", "a") as f:
                        f.write(log_entry + "\n")
                    
                    raise e3
            else:
                # 최종 실패 로그
                latency_ms = int((time.time() - start_time) * 1000)
                log_entry = f"ts={datetime.now().isoformat()} lane={alt_lane} model=\"{model}\" latency_ms={latency_ms} tokens_in={tokens_in} tokens_out=0 err=1 hint=\"{hint_with_len}\""
                
                with open("/tmp/router.log", "a") as f:
                    f.write(log_entry + "\n")
                
                raise e2

@app.get("/health")
async def health():
    return {"status": "ok", "service": "DreamSeedAI Auto Router"}

@app.get("/models")
async def models():
    return {
        "object": "list",
        "data": [
            {
                "id": "auto-llm",
                "object": "model",
                "created": 1677610602,
                "owned_by": "dreamseed-ai"
            }
        ]
    }
