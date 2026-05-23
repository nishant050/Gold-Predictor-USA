from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models.schemas import APIKey, AppSetting

router = APIRouter(prefix="/settings", tags=["settings"])

class APIKeyCreate(BaseModel):
    provider: str
    key_value: str
    is_primary: bool = False

class APIKeyResponse(BaseModel):
    id: int
    provider: str
    key_value: str
    is_active: int
    exhausted_until: datetime | None = None
    is_primary: int

    class Config:
        from_attributes = True

class AppSettingUpsert(BaseModel):
    value: str

class AppSettingResponse(BaseModel):
    key: str
    value: str

DEFAULT_APP_SETTINGS = {
    "openrouter_model": "poolside/laguna-m.1:free",
}

@router.get("/keys", response_model=Dict[str, List[APIKeyResponse]])
def get_api_keys(db: Session = Depends(get_db)):
    keys = db.query(APIKey).all()
    grouped_keys = {}
    for key in keys:
        if key.provider not in grouped_keys:
            grouped_keys[key.provider] = []
        grouped_keys[key.provider].append(key)
    return grouped_keys

@router.post("/keys", response_model=APIKeyResponse)
def add_api_key(key_in: APIKeyCreate, db: Session = Depends(get_db)):
    # If primary, unset others for this provider
    if key_in.is_primary:
        db.query(APIKey).filter(APIKey.provider == key_in.provider).update({"is_primary": 0})
        
    db_key = APIKey(
        provider=key_in.provider,
        key_value=key_in.key_value,
        is_active=1,
        is_primary=1 if key_in.is_primary else 0
    )
    db.add(db_key)
    db.commit()
    db.refresh(db_key)
    return db_key

@router.delete("/keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_api_key(key_id: int, db: Session = Depends(get_db)):
    db_key = db.query(APIKey).filter(APIKey.id == key_id).first()
    if not db_key:
        raise HTTPException(status_code=404, detail="API Key not found")
    db.delete(db_key)
    db.commit()
    return None

@router.post("/keys/{key_id}/reactivate", response_model=APIKeyResponse)
def reactivate_api_key(key_id: int, db: Session = Depends(get_db)):
    db_key = db.query(APIKey).filter(APIKey.id == key_id).first()
    if not db_key:
        raise HTTPException(status_code=404, detail="API Key not found")
    db_key.is_active = 1
    db_key.exhausted_until = None
    db.commit()
    db.refresh(db_key)
    return db_key

@router.get("/{key}", response_model=AppSettingResponse)
def get_app_setting(key: str, db: Session = Depends(get_db)):
    db_setting = db.query(AppSetting).filter(AppSetting.setting_key == key).first()
    if db_setting:
        return AppSettingResponse(key=db_setting.setting_key, value=db_setting.setting_value)

    if key in DEFAULT_APP_SETTINGS:
        return AppSettingResponse(key=key, value=DEFAULT_APP_SETTINGS[key])

    raise HTTPException(status_code=404, detail="Setting not found")

@router.post("/{key}", response_model=AppSettingResponse)
def upsert_app_setting(key: str, setting_in: AppSettingUpsert, db: Session = Depends(get_db)):
    value = setting_in.value.strip()
    if not value:
        raise HTTPException(status_code=400, detail="Setting value cannot be empty")

    db_setting = db.query(AppSetting).filter(AppSetting.setting_key == key).first()
    if db_setting:
        db_setting.setting_value = value
    else:
        db_setting = AppSetting(setting_key=key, setting_value=value)
        db.add(db_setting)

    db.commit()
    db.refresh(db_setting)
    return AppSettingResponse(key=db_setting.setting_key, value=db_setting.setting_value)
