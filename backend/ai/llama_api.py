# llama_api.py

from fastapi import FastAPI
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import uvicorn

app = FastAPI()

model_id = "meta-llama/Meta-Llama-3-8B-Instruct"

tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    model_id, torch_dtype=torch.float16, trust_remote_code=True
).cuda()  # ✅ device_map 제거 + 수동 .cuda()


class GenerationRequest(BaseModel):
    prompt: str


@app.post("/generate")
def generate_text(request: GenerationRequest):
    inputs = tokenizer(request.prompt, return_tensors="pt").to("cuda")
    outputs = model.generate(**inputs, max_new_tokens=256)
    return {"response": tokenizer.decode(outputs[0], skip_special_tokens=True)}


if __name__ == "__main__":
    uvicorn.run("llama_api:app", host="0.0.0.0", port=8000, reload=True)
