import base64
from typing import Optional
import vertexai
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from vertexai.preview.generative_models import GenerativeModel, Part

app = FastAPI()

vertexai.init(project="crp-sdx-cx-ia", location="us-central1")


class GenerationConfig(BaseModel):
    max_output_tokens: Optional[int] = 2048
    temperature: Optional[float] = 0.4
    top_p: Optional[float] = 1
    top_k: Optional[int] = 32


class GenerateRequest(BaseModel):
    prompt: str
    images: list[str]
    generation_config: GenerationConfig


@app.post("/generate")
async def generate(request: GenerateRequest):
    try:
        if not request.images:
            raise HTTPException(status_code=400, detail="No images provided")

        decoded_images = [Part.from_data(data=base64.b64decode(img), mime_type="image/png") for img in request.images]
        model = GenerativeModel("gemini-pro-vision")
        response = model.generate_content(
            [request.prompt] + decoded_images,
            generation_config={
                "max_output_tokens": request.generation_config.max_output_tokens,
                "temperature": request.generation_config.temperature,
                "top_p": request.generation_config.top_p,
                "top_k": request.generation_config.top_k
            },
        )
        generated_content = str(response)
        return {"respuesta": generated_content}
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
