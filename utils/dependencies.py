#!/usr/bin/env python3
from typing import Optional
from sqlalchemy.orm import Session
from pydantic import BaseModel

# Modèle de réponse standardisée
class StandardResponse(BaseModel):
    statusCode: int
    message: str
    data: Optional[dict] = None
