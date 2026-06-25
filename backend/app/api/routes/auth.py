from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.dependencies import get_db, get_current_user
from app.models.user import User, UserPreferences
from app.schemas.user import (
    UserRegister,
    UserLogin,
    UserResponse,
    Token,
    TokenRefresh,
    ProfileUpdate,
    PreferencesUpdate,
    PasswordUpdate
)
from app.services.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    # 1. Validation
    if user_data.password != user_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )
        
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered"
        )
        
    # 2. Creation
    pwd_hash = hash_password(user_data.password)
    user = User(
        full_name=user_data.full_name,
        email=user_data.email,
        password_hash=pwd_hash,
        last_login=datetime.utcnow()
    )
    db.add(user)
    db.flush()  # Populates user.id
    
    # Create default user preferences
    prefs = UserPreferences(
        user_id=user.id,
        theme="dark",
        language="en",
        default_ai_model="llama-3.3-70b-versatile",
        market_region="US",
        notifications_enabled=True,
        email_notifications=True,
        dashboard_layout="default",
        watchlist_default="default",
        daily_brief_time="08:00"
    )
    db.add(prefs)
    db.commit()
    db.refresh(user)
    
    # 3. Issue Tokens
    access_token = create_access_token({"sub": user.email})
    refresh_token = create_refresh_token({"sub": user.email})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user
    }


@router.post("/login", response_model=Token)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is deactivated"
        )
        
    user.last_login = datetime.utcnow()
    db.commit()
    db.refresh(user)
    
    # Issue Tokens (Access expire 15m, Refresh expire 7d)
    access_token = create_access_token({"sub": user.email})
    refresh_token = create_refresh_token({"sub": user.email})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user
    }


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    # Since JWT is stateless, client should discard token.
    # In a stateful config, blacklist. We return success.
    return {"message": "Successfully logged out"}


@router.post("/refresh")
def refresh(refresh_data: TokenRefresh, db: Session = Depends(get_db)):
    payload = verify_token(refresh_data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
        
    email = payload.get("sub")
    user = db.query(User).filter(User.email == email).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or deactivated"
        )
        
    # Rotate refresh tokens
    access_token = create_access_token({"sub": user.email})
    new_refresh_token = create_refresh_token({"sub": user.email})
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "user": UserResponse.model_validate(user)
    }



@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/profile", response_model=UserResponse)
def update_profile(
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if profile_data.full_name is not None:
        current_user.full_name = profile_data.full_name
    if profile_data.timezone is not None:
        current_user.timezone = profile_data.timezone
    if profile_data.preferred_market is not None:
        current_user.preferred_market = profile_data.preferred_market
    if profile_data.profile_picture is not None:
        current_user.profile_picture = profile_data.profile_picture
        
    current_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(current_user)
    return current_user


@router.put("/preferences")
def update_preferences(
    pref_data: PreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    prefs = current_user.preferences
    if not prefs:
        prefs = UserPreferences(user_id=current_user.id)
        db.add(prefs)
        
    for field, value in pref_data.model_dump(exclude_unset=True).items():
        setattr(prefs, field, value)
        
    db.commit()
    db.refresh(prefs)
    
    return {
        "message": "Preferences updated successfully",
        "preferences": {
            "theme": prefs.theme,
            "language": prefs.language,
            "default_ai_model": prefs.default_ai_model,
            "market_region": prefs.market_region,
            "notifications_enabled": prefs.notifications_enabled,
            "email_notifications": prefs.email_notifications,
            "dashboard_layout": prefs.dashboard_layout,
            "watchlist_default": prefs.watchlist_default,
            "daily_brief_time": prefs.daily_brief_time
        }
    }


@router.put("/password")
def update_password(
    pwd_data: PasswordUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not verify_password(pwd_data.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect old password"
        )
        
    if pwd_data.new_password != pwd_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New passwords do not match"
        )
        
    current_user.password_hash = hash_password(pwd_data.new_password)
    current_user.updated_at = datetime.utcnow()
    db.commit()
    return {"message": "Password updated successfully"}


@router.delete("/account")
def delete_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db.delete(current_user)
    db.commit()
    return {"message": "Account successfully deleted"}
