# app/schemas/image.py
from pydantic import BaseModel, Field
from typing import List, Optional
from fastapi import Form
import json

class ConversionSettings(BaseModel):
    quality: int = Field(ge=1, le=100, default=80)
    preserve_metadata: bool = True
    smart_optimize: bool = True

    @classmethod
    def from_form(cls, settings_json: str = Form(default=None)):
        if settings_json:
            try:
                settings_dict = json.loads(settings_json)
                return cls(**settings_dict)
            except:
                return cls()
        return cls()

class ConversionResponse(BaseModel):
    original_size: int
    converted_size: int
    reduction_percent: float
    output_path: str

class BatchConversionResponse(BaseModel):
    total_files: int
    total_original_size: int
    total_converted_size: int
    average_reduction: float
    files: List[ConversionResponse]
    failed_files: Optional[List[dict]] = None

class ErrorResponse(BaseModel):
    detail: str
    file: Optional[str] = None