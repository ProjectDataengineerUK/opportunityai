import json
import re
from typing import TypeVar, Type
import vertexai
from vertexai.generative_models import GenerativeModel
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class GeminiClient:
    def __init__(self, project_id: str, location: str = "us-central1", model: str = "gemini-2.5-flash"):
        vertexai.init(project=project_id, location=location)
        self._model = GenerativeModel(model)

    def generate_structured(self, prompt: str, schema: Type[T]) -> T:
        schema_json = json.dumps(schema.model_json_schema(), indent=2)
        full_prompt = (
            f"{prompt}\n\n"
            f"Responda APENAS com JSON válido seguindo exatamente este schema:\n{schema_json}\n"
            "Não inclua markdown, explicações ou texto fora do JSON."
        )
        response = self._model.generate_content(full_prompt)
        raw = response.text.strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        return schema.model_validate_json(raw)
