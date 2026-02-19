from sqlalchemy.orm import Session
from app.models.user import User
from app.utils.security import verify_password, create_access_token


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def authenticate(self, username: str, password: str) -> User | None:
        user = self.db.query(User).filter(User.username == username).first()
        if not user or not verify_password(password, user.password_hash):
            return None
        if user.status != "active":
            return None
        return user

    def create_token(self, user: User) -> str:
        return create_access_token(data={"sub": str(user.id), "role": user.role})
