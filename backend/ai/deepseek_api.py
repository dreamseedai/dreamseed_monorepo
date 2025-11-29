# deepseek_api.py
from fastapi import FastAPI, Body
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

app = FastAPI()

model_id = "deepseek-ai/deepseek-llm-7b-chat"
tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    model_id, device_map="auto", torch_dtype=torch.float16
)


@app.post("/test-gpt")
def test_prompt(prompt: str = Body(..., embed=True)):
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    outputs = model.generate(**inputs, max_new_tokens=300)
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return {"response": response}
