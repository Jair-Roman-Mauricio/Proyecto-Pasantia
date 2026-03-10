from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, OperationalError
from fastapi import HTTPException


def safe_commit(db: Session, user_msg: str = "Error al guardar los datos") -> None:
    """
    Realiza db.commit() con manejo de excepciones de SQLAlchemy.

    Captura los errores más comunes de base de datos y los convierte en
    respuestas HTTP apropiadas para que el cliente reciba un mensaje claro:

    - IntegrityError  → HTTP 400 (dato duplicado o FK inválida)
    - OperationalError → HTTP 503 (conexión caída o timeout)

    Parámetros:
        db:       Sesión activa de SQLAlchemy.
        user_msg: Mensaje personalizado para el error 400 (opcional).

    Lanza:
        HTTPException 400 si hay violación de restricción de integridad.
        HTTPException 503 si hay fallo de conexión con la base de datos.
    """
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail=user_msg)
    except OperationalError:
        db.rollback()
        raise HTTPException(status_code=503, detail="Error de conexion con la base de datos")
