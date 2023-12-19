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
from vertexai.preview.generative_models import Part
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
            response = requests.get(url)
            response.raise_for_status()
            image_data = base64.b64encode(response.content).decode("utf-8")
            decoded_images.append(Part.from_data(data=base64.b64decode(image_data), mime_type="image/png"))

        llm = VertexAI(
            model_name="gemini-pro-vision",
            max_output_tokens=request.generation_config.max_output_tokens,
            temperature=request.generation_config.temperature,
            top_p=request.generation_config.top_p,
            top_k=request.generation_config.top_k,
            verbose=True,
        )

        atributo_template = PromptGallery.Atributo_visible()
        atributo_prompt = PromptTemplate(input_variables=["attributes"],
                                         template=atributo_template)
        atributo_chain = LLMChain(llm=llm, prompt=atributo_prompt, output_key="list_atributos", verbose=True)

        images_template = PromptGallery.Enriquecimiento_imagenes()
        images_prompt = PromptTemplate(
            input_variables=["list_atributos"],
            template=images_template)
        images_chain = LLMChain(llm=llm, prompt=images_prompt, output_key="response", verbose=True)

        overall_chain = SequentialChain(
            chains=[atributo_chain, images_chain],
            input_variables=["attributes", "images"],
            output_variables=["response"],
            verbose=True
        )
        
        

        model_response = overall_chain({
            "attributes": request.attributes,
            "images": decoded_images,
        })

        response = {
            "output_text": model_response["response"].replace('\n', '').replace('```JSON', '').replace('```', '')
        }

        print(response['output_text'])

        return response
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8080))
    print("Using port:", port)
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
