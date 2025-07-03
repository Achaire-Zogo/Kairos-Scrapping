#!/usr/bin/env python3
import uuid
from typing import List, Optional
import os
import shutil
import datetime
from fastapi import APIRouter, Depends, status, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from models.axe_model import AxeEntity
from models.theme_model import ThemeEntity
from dotenv import load_dotenv
# Importer les dépendances depuis le fichier dependencies.py
from utils.dependencies import StandardResponse
from utils.database import get_db
import os
import requests
import datetime
import logging

router = APIRouter(
    prefix="/api/service-themes",
    tags=["Themes"],
    responses={404: {"description": "Not found"}},
)

# Charger les variables d'environnement avant d'importer les autres modules
load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())


@router.get("/get-all-themes", response_model=StandardResponse)
def get_themes(nom: Optional[str] = None, db: Session = Depends(get_db)):
    try:
        query = db.query(ThemeEntity)
        if nom:
            query = query.filter(ThemeEntity.name.like(f'%{nom}%'))
        themes = query.all()
        themes_list = [theme.to_dict() for theme in themes]

        if nom:
            message = f"Themes found for name: {nom}"
        else:
            message = "List of all themes"
        
        return StandardResponse(
            statusCode=200,
            message=message,
            data={"themes": themes_list}
        )
    except Exception as e:
        return StandardResponse(
            statusCode=500,
            message=str(e),
            data={}
        )

@router.get("/get-theme/{theme_id}", response_model=StandardResponse)
def get_theme(theme_id: int, db: Session = Depends(get_db)):
    try:
        theme = db.query(ThemeEntity).filter(ThemeEntity.id == theme_id).first()
        if theme:
            return StandardResponse(
                statusCode=200,
                message="theme found",
                data={"theme": theme.to_dict()}
            )
        else:
            return StandardResponse(
                statusCode=404,
                message="theme not found",
                data={}
            )
    except Exception as e:
        return StandardResponse(
            statusCode=500,
            message=str(e),
            data={}
        )


@router.post("/create-theme", response_model=StandardResponse)
async def create_theme(
    name: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        # Vérifier si l'utilisateur existe déjà
        existing_theme = db.query(ThemeEntity).filter(ThemeEntity.name == name).first()
        if existing_theme:
            return JSONResponse(
                status_code=400,
                content={
                    "statusCode": 400,
                    "message": "Theme already exists",
                    "data": {}
                }
            )
            
        # Vérifier si le numéro de téléphone existe déjà
        if name:
            existing_name = db.query(ThemeEntity).filter(ThemeEntity.name == name).first()
            if existing_name:
                return JSONResponse(
                    status_code=400,
                    content={
                        "statusCode": 400,
                        "message": "Theme name already exists",
                        "data": {}
                    }
                )
        
        # Créer l'utilisateur
        theme_data = {
            "name": name,
        }
        
        theme = ThemeEntity(**theme_data)
        db.add(theme)
        db.commit()
        db.refresh(theme)
        
        return StandardResponse(
            statusCode=201,
            message="Theme created successfully",
            data={"theme": theme.to_dict()}
        )
        
    except Exception as e:
        db.rollback()
        return StandardResponse(
            statusCode=500,
            message=str(e),
            data={
                "statusCode": 500,
                "message": f"An error occurred: {str(e)}",
                "data": {}
            }
        )

#update user
@router.put("/update-theme/{theme_id}", response_model=StandardResponse)
async def update_user(
    theme_id: int,
    name: str = Form(None),
    db: Session = Depends(get_db)
):
    try:
        # Récupérer l'utilisateur existant
        theme = db.query(ThemeEntity).filter(ThemeEntity.id == theme_id).first()
        if not theme:
            return StandardResponse(
                statusCode=404,
                message="Theme not found",
                data={}
            )
            
        # Vérifier si l'email est déjà utilisé par un autre utilisateur
        if name and name != theme.name:
            existing_name = db.query(ThemeEntity).filter(
                ThemeEntity.name == name,
                ThemeEntity.id != theme_id
            ).first()
            if existing_name:
                return StandardResponse(
                    statusCode=400,
                    message="Theme name already in use by another user",
                    data={}
                )
        
        # Mettre à jour les champs fournis
        if name is not None:
            theme.name = name
        
        theme.updated_at = datetime.datetime.now()
        db.commit()
        db.refresh(theme)
        
        return StandardResponse(
            statusCode=200,
            message="Theme updated successfully",
            data={"theme": theme.to_dict()}
        )
        
    except Exception as e:
        db.rollback()
        return StandardResponse(
            statusCode=500,
            message=str(e),
            data={
                "statusCode": 500,
                "message": f"An error occurred: {str(e)}",
                "data": {}
            }
        )
        
    except Exception as e:
        db.rollback()
        return StandardResponse(
            statusCode=500,
            message=str(e),
            data={}
        )

#delete user
@router.delete("/delete-theme/{theme_id}", response_model=StandardResponse)
def delete_user(theme_id: int, db: Session = Depends(get_db)):
    try:
        theme = db.query(ThemeEntity).filter(ThemeEntity.id == theme_id).first()
        if theme:
            db.delete(theme)
            db.commit()
            return StandardResponse(
                statusCode=200,
                message="Theme deleted",
                data={}
            )
        else:
            return StandardResponse(
                statusCode=404,
                message="Theme not found",
                data={}
            )
    except Exception as e:
        return StandardResponse(
            statusCode=500,
            message=str(e),
            data={}
        )

