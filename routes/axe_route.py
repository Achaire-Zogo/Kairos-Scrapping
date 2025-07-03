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
    prefix="/api/service-axes",
    tags=["Axes"],
    responses={404: {"description": "Not found"}},
)

# Charger les variables d'environnement avant d'importer les autres modules
load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())


@router.get("/get-all-axes", response_model=StandardResponse)
def get_axes(nom: Optional[str] = None, db: Session = Depends(get_db)):
    try:
        query = db.query(AxeEntity)
        if nom:
            query = query.filter(AxeEntity.name.like(f'%{nom}%'))
        axes = query.all()
        axes_list = [axe.to_dict() for axe in axes]

        if nom:
            message = f"Axes found for name: {nom}"
        else:
            message = "List of all axes"
        
        return StandardResponse(
            statusCode=200,
            message=message,
            data={"axes": axes_list}
        )
    except Exception as e:
        return StandardResponse(
            statusCode=500,
            message=str(e),
            data={}
        )

@router.get("/get-axe/{axe_id}", response_model=StandardResponse)
def get_axe(axe_id: int, db: Session = Depends(get_db)):
    try:
        axe = db.query(AxeEntity).filter(AxeEntity.id == axe_id).first()
        if axe:
            return StandardResponse(
                statusCode=200,
                message="axe found",
                data={"axe": axe.to_dict()}
            )
        else:
            return StandardResponse(
                statusCode=404,
                message="axe not found",
                data={}
            )
    except Exception as e:
        return StandardResponse(
            statusCode=500,
            message=str(e),
            data={}
        )


@router.post("/create-axe", response_model=StandardResponse)
async def create_axe(
    name: str = Form(...),
    icon: str = Form(...),
    color: str = Form(...),
    theme_id: int = Form(...),
    db: Session = Depends(get_db)
):
    try:
        # Vérifier si l'utilisateur existe déjà
        existing_axe = db.query(AxeEntity).filter(AxeEntity.name == name).first()
        if existing_axe:
            return JSONResponse(
                status_code=400,
                content={
                    "statusCode": 400,
                    "message": "Axe already exists",
                    "data": {}
                }
            )

        existing_theme = db.query(AxeEntity).filter(AxeEntity.theme_id == theme_id).first()
        if existing_theme:
            return JSONResponse(
                status_code=400,
                content={
                    "statusCode": 400,
                    "message": "Theme already exists",
                    "data": {}
                }
            )       
        
        # Créer l'utilisateur
        axe_data = {
            "name": name,
            "icon": icon,
            "color": color,
            "theme_id": theme_id,
        }
        
        axe = AxeEntity(**axe_data)
        db.add(axe)
        db.commit()
        db.refresh(axe)
        
        return StandardResponse(
            statusCode=201,
            message="Axe created successfully",
            data={"axe": axe.to_dict()}
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
@router.put("/update-axe/{axe_id}", response_model=StandardResponse)
async def update_user(
    axe_id: int,
    name: str = Form(None),
    icon: str = Form(None),
    color: str = Form(None),
    theme_id: int = Form(None),
    db: Session = Depends(get_db)
):
    try:
        # Récupérer l'utilisateur existant
        axe = db.query(AxeEntity).filter(AxeEntity.id == axe_id).first()
        if not axe:
            return StandardResponse(
                statusCode=404,
                message="User not found",
                data={}
            )
            
        # Vérifier si l'email est déjà utilisé par un autre utilisateur
        if name and name != axe.name:
            existing_name = db.query(AxeEntity).filter(
                AxeEntity.name == name,
                AxeEntity.id != axe_id
            ).first()
            if existing_name:
                return StandardResponse(
                    statusCode=400,
                    message="Axe name already in use by another user",
                    data={}
                )
        
        # Vérifier si le numéro de téléphone est déjà utilisé par un autre utilisateur
        if icon and icon != axe.icon:
            existing_icon = db.query(AxeEntity).filter(
                AxeEntity.icon == icon,
                AxeEntity.id != axe_id
            ).first()
            if existing_icon:
                return StandardResponse(
                    statusCode=400,
                    message="Phone number already in use by another user",
                    data={}
                )
        
        # Mettre à jour les champs fournis
        if name is not None:
            axe.name = name
        if icon is not None:
            axe.icon = icon
        if color is not None:
            axe.color = color
        if theme_id is not None:
            axe.theme_id = theme_id        
        axe.updated_at = datetime.datetime.now()
        db.commit()
        db.refresh(axe)
        
        return StandardResponse(
            statusCode=200,
            message="Axe updated successfully",
            data={"axe": axe.to_dict()}
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
@router.delete("/delete-axe/{axe_id}", response_model=StandardResponse)
def delete_user(axe_id: int, db: Session = Depends(get_db)):
    try:
        axe = db.query(AxeEntity).filter(AxeEntity.id == axe_id).first()
        if axe:
            db.delete(axe)
            db.commit()
            return StandardResponse(
                statusCode=200,
                message="Axe deleted",
                data={}
            )
        else:
            return StandardResponse(
                statusCode=404,
                message="Axe not found",
                data={}
            )
    except Exception as e:
        return StandardResponse(
            statusCode=500,
            message=str(e),
            data={}
        )

