from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm

from .database import get_db
from .models import User, Fleet
from .security import hash_password, verify_password, create_access_token

from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/auth", tags=["Auth"])


# =========================
# SCHEMAS
# =========================

class RegisterSchema(BaseModel):
    email: EmailStr
    password: str
    fleet_name: str


class LoginSchema(BaseModel):
    email: EmailStr
    password: str


# =========================
# REGISTER
# =========================

@router.post("/register")
def register(data: RegisterSchema, db: Session = Depends(get_db)):

    existing_user = db.query(User).filter(User.email == data.email).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        role="fleet_manager"
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    # Auto-create fleet
    fleet = Fleet(
        name=data.fleet_name,
        owner_id=user.id
    )

    db.add(fleet)
    db.commit()

    return {"message": "User registered successfully"}


# =========================
# LOGIN
# =========================

@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == form_data.username).first()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=60)
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }