from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.config import settings

# Crear el motor de conexión a PostgreSQL.
# pool_pre_ping=True verifica la conexión antes de cada uso para evitar errores
# por conexiones inactivas que hayan sido cerradas por el servidor o un proxy.
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

# Fábrica de sesiones: autocommit y autoflush desactivados para control
# explícito de transacciones en cada endpoint.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """
    Dependencia de FastAPI que provee una sesión de base de datos por request.

    Abre una sesión al inicio del request y la cierra al finalizar,
    garantizando que los recursos se liberen incluso si ocurre una excepción.

    Uso:
        db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
