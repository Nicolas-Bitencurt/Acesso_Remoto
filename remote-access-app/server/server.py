"""
Servidor intermediário (Broker) para acesso remoto
Responsável por autenticação, roteamento de mensagens e gerenciamento de sessões
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, Set
import socket
import sys
from pathlib import Path

# Adiciona diretório pai ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import (
    SERVER_HOST, SERVER_PORT, SERVER_TIMEOUT, USERS_DB_FILE, SESSIONS_DB_FILE,
    MAX_CONNECTIONS, SESSION_TIMEOUT, MAX_LOGIN_ATTEMPTS, LOCKOUT_DURATION,
    LOG_FILE, LOG_LEVEL
)
from shared.protocol import ProtocolHandler, Message
from shared.encryption import CryptoManager

# Configurar logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class UserManager:
    """
    Gerencia usuários e credenciais
    Para MVP, usa arquivo JSON
    """

    def __init__(self, db_file: Path):
        self.db_file = db_file
        self.users = self._load_users()
        self.failed_attempts = {}  # Rastreamento de tentativas falhadas
        self.lockout_times = {}  # Rastreamento de bloqueios

    def _load_users(self) -> Dict:
        """Carrega usuários do arquivo"""
        try:
            if self.db_file.exists():
                with open(self.db_file, "r") as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Erro ao carregar usuários: {e}")

        return self._get_default_users()

    def _get_default_users(self) -> Dict:
        """Retorna usuários padrão para teste"""
        # Senhas hasheadas (usar CryptoManager.hash_password para gerar)
        return {
            "admin": {
                "password": CryptoManager.hash_password("admin123"),
                "created_at": datetime.now().isoformat(),
                "permissions": ["control", "view"]
            },
            "viewer": {
                "password": CryptoManager.hash_password("viewer123"),
                "created_at": datetime.now().isoformat(),
                "permissions": ["view"]
            }
        }

    def _save_users(self):
        """Salva usuários no arquivo"""
        try:
            self.db_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.db_file, "w") as f:
                json.dump(self.users, f, indent=2)
        except Exception as e:
            logger.error(f"Erro ao salvar usuários: {e}")

    def authenticate(self, username: str, password_hash: str) -> Optional[str]:
        """
        Autentica um usuário

        Args:
            username: Nome do usuário
            password_hash: Hash da senha

        Returns:
            str: Mensagem de erro, ou None se sucesso
        """
        # Verifica bloqueio
        if username in self.lockout_times:
            lockout_time = self.lockout_times[username]
            if datetime.now() < lockout_time:
                remaining = (lockout_time - datetime.now()).seconds
                return f"Usuário bloqueado. Tente novamente em {remaining}s"
            else:
                # Libera bloqueio
                del self.lockout_times[username]
                self.failed_attempts[username] = 0

        # Verifica existência
        if username not in self.users:
            logger.warning(f"Tentativa de login com usuário inexistente: {username}")
            return "Usuário ou senha inválidos"

        # Verifica senha
        user = self.users[username]
        if user["password"] != password_hash:
            self.failed_attempts[username] = self.failed_attempts.get(username, 0) + 1

            if self.failed_attempts[username] >= MAX_LOGIN_ATTEMPTS:
                # Bloqueia usuário
                lockout_until = datetime.now() + timedelta(seconds=LOCKOUT_DURATION)
                self.lockout_times[username] = lockout_until
                logger.warning(f"Usuário {username} bloqueado após múltiplas tentativas")
                return f"Muitas tentativas falhadas. Tente novamente em {LOCKOUT_DURATION}s"

            logger.warning(f"Falha de autenticação para {username}")
            return "Usuário ou senha inválidos"

        # Sucesso
        self.failed_attempts[username] = 0
        logger.info(f"Usuário {username} autenticado com sucesso")
        return None

    def add_user(self, username: str, password: str, permissions: list = None):
        """Adiciona novo usuário"""
        if username in self.users:
            return False

        self.users[username] = {
            "password": CryptoManager.hash_password(password),
            "created_at": datetime.now().isoformat(),
            "permissions": permissions or ["view"]
        }
        self._save_users()
        logger.info(f"Novo usuário criado: {username}")
        return True


class SessionManager:
    """
    Gerencia sessões de conexão
    """

    def __init__(self, db_file: Path):
        self.db_file = db_file
        self.sessions = self._load_sessions()
        self.client_sessions: Dict[socket.socket, str] = {}  # Socket -> session_id

    def _load_sessions(self) -> Dict:
        """Carrega sessões do arquivo"""
        try:
            if self.db_file.exists():
                with open(self.db_file, "r") as f:
                    sessions = json.load(f)
                    # Remove sessões expiradas
                    return {
                        sid: sess for sid, sess in sessions.items()
                        if datetime.fromisoformat(sess["expires_at"]) > datetime.now()
                    }
        except Exception as e:
            logger.error(f"Erro ao carregar sessões: {e}")

        return {}

    def _save_sessions(self):
        """Salva sessões no arquivo"""
        try:
            self.db_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.db_file, "w") as f:
                json.dump(self.sessions, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Erro ao salvar sessões: {e}")

    def create_session(self, username: str, device_name: str = None) -> str:
        """
        Cria nova sessão

        Args:
            username: Nome do usuário
            device_name: Nome do dispositivo

        Returns:
            str: ID da sessão
        """
        session_id = CryptoManager.generate_session_token()
        expires_at = datetime.now() + timedelta(seconds=SESSION_TIMEOUT)

        self.sessions[session_id] = {
            "username": username,
            "device_name": device_name or "Unknown",
            "created_at": datetime.now().isoformat(),
            "expires_at": expires_at.isoformat(),
            "last_activity": datetime.now().isoformat()
        }

        self._save_sessions()
        logger.info(f"Sessão criada para {username}: {session_id}")

        return session_id

    def is_session_valid(self, session_id: str) -> bool:
        """Verifica se sessão é válida"""
        if session_id not in self.sessions:
            return False

        session = self.sessions[session_id]
        expires_at = datetime.fromisoformat(session["expires_at"])

        return expires_at > datetime.now()

    def update_activity(self, session_id: str):
        """Atualiza timestamp de última atividade"""
        if session_id in self.sessions:
            self.sessions[session_id]["last_activity"] = datetime.now().isoformat()

    def end_session(self, session_id: str):
        """Encerra uma sessão"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            self._save_sessions()
            logger.info(f"Sessão encerrada: {session_id}")

    def get_session_info(self, session_id: str) -> Optional[dict]:
        """Retorna informações da sessão"""
        return self.sessions.get(session_id)


class RemoteAccessBroker:
    """
    Servidor intermediário principal
    """

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.user_manager = UserManager(USERS_DB_FILE)
        self.session_manager = SessionManager(SESSIONS_DB_FILE)
        self.crypto = CryptoManager("sua-chave-secreta-super-segura-32-chars!!")
        self.active_clients: Set[asyncio.StreamWriter] = set()
        self.client_sessions: Dict[str, Dict] = {}  # session_id -> client_info

        logger.info(f"Broker inicializado: {host}:{port}")

    async def handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter
    ):
        """Gerencia conexão de cliente"""
        client_addr = writer.get_extra_info("peername")
        logger.info(f"Novo cliente conectado: {client_addr}")

        self.active_clients.add(writer)
        session_id = None

        try:
            buffer = b""

            while True:
                # Lê dados
                data = await asyncio.wait_for(
                    reader.read(4096),
                    timeout=SERVER_TIMEOUT
                )

                if not data:
                    break

                buffer += data

                # Processa mensagens
                while buffer:
                    msg, buffer = ProtocolHandler.deserialize_message(buffer)

                    if msg is None:
                        break

                    # Processa mensagem
                    response = await self._process_message(msg, session_id)

                    if response:
                        # Atualiza session_id se foi autenticado
                        if (
                            msg.msg_type == "auth_req" and
                            response.data.get("success")
                        ):
                            session_id = response.session_id

                        # Envia resposta
                        response_data = ProtocolHandler.serialize_message(response)
                        writer.write(response_data)
                        await writer.drain()

                    # Verifica desconexão
                    if msg.msg_type == "disconnect":
                        if session_id:
                            self.session_manager.end_session(session_id)
                        break

        except asyncio.TimeoutError:
            logger.warning(f"Timeout para cliente: {client_addr}")
        except Exception as e:
            logger.error(f"Erro ao processar cliente: {e}")
        finally:
            self.active_clients.discard(writer)
            if session_id:
                self.session_manager.end_session(session_id)
            writer.close()
            await writer.wait_closed()
            logger.info(f"Cliente desconectado: {client_addr}")

    async def _process_message(
        self,
        msg: Message,
        session_id: Optional[str]
    ) -> Optional[Message]:
        """
        Processa mensagem do cliente

        Args:
            msg: Mensagem recebida
            session_id: ID da sessão atual

        Returns:
            Message: Resposta para enviar ao cliente
        """
        msg_type = msg.msg_type

        if msg_type == "auth_req":
            return await self._handle_auth(msg)

        # Valida sessão para outros tipos
        if not session_id or not self.session_manager.is_session_valid(session_id):
            return ProtocolHandler.create_error(
                session_id or "unknown",
                401,
                "Sessão inválida ou expirada"
            )

        # Atualiza atividade
        self.session_manager.update_activity(session_id)

        if msg_type == "ping":
            return ProtocolHandler.create_pong(session_id)

        elif msg_type == "screen_cap":
            # Rotearia para outro cliente ou armazenaria
            return ProtocolHandler.create_pong(session_id)

        elif msg_type == "mouse_evt" or msg_type == "key_evt":
            # Rotearia para o cliente alvo
            return ProtocolHandler.create_pong(session_id)

        elif msg_type == "disconnect":
            return ProtocolHandler.create_disconnect(session_id, "OK")

        else:
            return ProtocolHandler.create_error(
                session_id,
                400,
                f"Tipo de mensagem desconhecido: {msg_type}"
            )

    async def _handle_auth(self, msg: Message) -> Message:
        """Processa autenticação"""
        data = msg.data
        username = data.get("username")
        password_hash = data.get("password")
        device_name = data.get("device_name")

        if not username or not password_hash:
            return ProtocolHandler.create_auth_response(False, None, "Credenciais inválidas")

        # Autentica
        error = self.user_manager.authenticate(username, password_hash)

        if error:
            return ProtocolHandler.create_auth_response(False, None, error)

        # Cria sessão
        session_id = self.session_manager.create_session(username, device_name)

        return ProtocolHandler.create_auth_response(
            True,
            session_id,
            "Autenticado com sucesso!"
        )

    async def start(self):
        """Inicia o servidor"""
        server = await asyncio.start_server(
            self.handle_client,
            self.host,
            self.port,
            backlog=MAX_CONNECTIONS
        )

        logger.info(f"Servidor iniciado em {self.host}:{self.port}")

        async with server:
            await server.serve_forever()


async def main():
    """Função principal"""
    broker = RemoteAccessBroker(SERVER_HOST, SERVER_PORT)

    try:
        await broker.start()
    except KeyboardInterrupt:
        logger.info("Servidor interrompido pelo usuário")
    except Exception as e:
        logger.error(f"Erro fatal no servidor: {e}")


if __name__ == "__main__":
    asyncio.run(main())
