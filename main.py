"""
@Autor Iván Martinez
Contacto: imartinezt@liverpool.com.mx
"""
import base64
from typing import Optional
import requests
import vertexai
from fastapi import FastAPI, HTTPException
from langchain.chains import LLMChain, SequentialChain
from langchain.llms import VertexAI
from langchain.prompts import PromptTemplate
from pydantic import BaseModel
from vertexai.preview.generative_models import Part, GenerativeModel
import uvicorn

import PromptGallery

app = FastAPI()

vertexai.init(project="crp-sdx-cx-ia", location="us-central1")


class GenerationConfig(BaseModel):
    max_output_tokens: Optional[int] = 2048
    temperature: Optional[float] = 0.4
    top_p: Optional[float] = 1
    top_k: Optional[int] = 32


class GenerateRequest(BaseModel):
    attributes: str
    images: list[str]
    generation_config: GenerationConfig


@app.post("/generate")
async def generate(request: GenerateRequest):
    try:
        if not request.images:
            raise HTTPException(status_code=400, detail="No images provided")
        decoded_images = []

        for url in request.images:
            decoded_images.append(Part.from_uri(url, mime_type="image/jpeg"))

        llm = GenerativeModel(
            model_name="gemini-pro-vision",
        )
        
        generation_config = {"max_output_tokens":request.generation_config.max_output_tokens,
            "temperature":request.generation_config.temperature,
            "top_p":request.generation_config.top_p,
            "top_k":request.generation_config.top_k,}

        atributo_template = PromptGallery.Atributo_visible()
        atributo = PromptTemplate.from_template(atributo_template)
        atributo_prompt = atributo.format(attributes=request.attributes)
        print(atributo_prompt)
        atributo_response = llm.generate_content(atributo_prompt,
                                         generation_config=generation_config)
        
        print(atributo_response.text)
        images_template = PromptGallery.Enriquecimiento_imagenes()
        images = PromptTemplate.from_template(images_template)
        images_prompt = images.format(attributes=atributo_response.text)
        print(images_prompt)
        
        image_response = llm.generate_content(
            [images_prompt, *decoded_images],
            #generation_config=generation_config
        )
        
        return image_response.text
        
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8080))
    print("Using port:", port)
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
