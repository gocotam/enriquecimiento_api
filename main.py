"""
@Autor Iván Martinez
Contacto: imartinezt@liverpool.com.mx
"""
from typing import Optional
import uvicorn
import vertexai
from fastapi import FastAPI, HTTPException
from langchain.prompts import PromptTemplate
from pydantic import BaseModel
from starlette.responses import JSONResponse
from vertexai.preview.generative_models import Part, GenerativeModel

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
        multimodal_model = GenerativeModel("gemini-pro-vision")
        if not request.images or not request.attributes:
            raise HTTPException(status_code=400, detail="Invalid request data")

        # Convertir la lista de imágenes en partes decodificadas
        decoded_images = [Part.from_uri(url, mime_type="image/jpeg") for url in request.images]

        # Generación de contenido basado en la plantilla de atributos
        atributo_template = PromptGallery.Atributo_visible()
        atributo = PromptTemplate.from_template(atributo_template)
        atributo_prompt = atributo.format(attributes=request.attributes)
        atributo_response = multimodal_model.generate_content([atributo_prompt, *decoded_images])

        # Emparejamiento de la respuesta de atributos con la plantilla de imágenes
        images_template = PromptGallery.Enriquecimiento_imagenes()
        images = PromptTemplate.from_template(images_template)
        images_prompt = images.format(attributes=atributo_response.text)
        image_response = multimodal_model.generate_content([images_prompt, *decoded_images])

        # Devolver respuesta procesada
        return {
            "Status": {
                "General": "Success",
                "Details": {
                    "Images": {
                        "Code": "00",
                        "Message": "Generado exitosamente."
                    }
                }
            },
            "output_text": image_response.text
        }

    except HTTPException as he:
        return JSONResponse(content={
            "Status": {
                "General": "Error",
                "Details": {
                    "Images": {
                        "Code": "01",
                        "Message": str(he.detail)
                    }
                }
            }
        }, status_code=he.status_code)

    except Exception as e:
        print(f"Error: {e}")
        return JSONResponse(content={
            "Status": {
                "General": "Error",
                "Details": {
                    "Images": {
                        "Code": "01",
                        "Message": "Servicio no disponible."
                    }
                }
            }
        }, status_code=500)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
