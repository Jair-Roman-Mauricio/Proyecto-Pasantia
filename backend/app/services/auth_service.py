"""
Módulo de autenticación de usuarios.

Provee la clase AuthService, que encapsula la lógica de autenticación
basada en nombre de usuario y contraseña (hash bcrypt), así como la
generación de tokens de acceso JWT firmados con los datos de identidad
y rol del usuario autenticado.
"""

from sqlalchemy.orm import Session
from app.models.user import User
from app.utils.security import verify_password, create_access_token


class AuthService:
    """
    Servicio de autenticación de usuarios del sistema.

    Centraliza las operaciones de verificación de credenciales y emisión
    de tokens JWT, desacoplando la lógica de seguridad de los endpoints
    de la API.

    Attributes:
        db (Session): Sesión activa de SQLAlchemy utilizada para consultar
            usuarios en la base de datos.
    """

    def __init__(self, db: Session):
        """
        Inicializa el servicio con una sesión de base de datos.

        Args:
            db (Session): Sesión de SQLAlchemy inyectada desde el contexto
                de la solicitud HTTP.
        """
        self.db = db

    def authenticate(self, username: str, password: str) -> User | None:
        """
        Verifica las credenciales de un usuario y valida que su cuenta esté activa.

        Busca al usuario por nombre de usuario, compara la contraseña
        proporcionada contra el hash almacenado mediante bcrypt y, si ambas
        condiciones se cumplen, verifica que el estado de la cuenta sea
        ``'active'``.

        Args:
            username (str): Nombre de usuario tal como fue registrado en
                el sistema.
            password (str): Contraseña en texto plano enviada por el cliente;
                se compara internamente contra el hash almacenado.

        Returns:
            User | None: El objeto ``User`` si las credenciales son válidas
                y la cuenta está activa. Retorna ``None`` si el usuario no
                existe, la contraseña es incorrecta o la cuenta está inactiva.
        """
        # Consultar el usuario por nombre; retornar None si no existe
        user = self.db.query(User).filter(User.username == username).first()
        if not user or not verify_password(password, user.password_hash):
            return None

        # Rechazar el acceso si la cuenta del usuario ha sido desactivada
        if user.status != "active":
            return None

        return user

    def create_token(self, user: User) -> str:
        """
        Genera un token de acceso JWT firmado para el usuario autenticado.

        El token incluye el identificador único del usuario como ``sub``
        (subject) y su rol para que los middlewares de autorización puedan
        aplicar control de acceso basado en roles (RBAC) sin consultar la
        base de datos en cada solicitud.

        Args:
            user (User): Objeto de usuario autenticado previamente mediante
                ``authenticate()``. Se utiliza ``user.id`` y ``user.role``
                para construir el payload del token.

        Returns:
            str: Token JWT codificado y firmado, listo para ser enviado
                al cliente en la respuesta de inicio de sesión.
        """
        # Construir el payload con la identidad y el rol del usuario
        return create_access_token(data={"sub": str(user.id), "role": user.role})
