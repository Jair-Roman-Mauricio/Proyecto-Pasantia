from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, OperationalError
from fastapi import HTTPException


def safe_commit(db: Session, user_msg: str = "Error al guardar los datos") -> None:
    """
    Realiza db.commit() con manejo de excepciones de SQLAlchemy.
    - IntegrityError  → 400 (dato duplicado o FK inválida)
    - OperationalError → 503 (conexión caída o timeout)
    """
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail=user_msg)
    except OperationalError:
        db.rollback()
        raise HTTPException(status_code=503, detail="Error de conexion con la base de datos")
