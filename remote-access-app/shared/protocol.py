"""
Protocolo de comunicação para acesso remoto
Define o formato de mensagens trocadas entre cliente e servidor
"""

import json
import struct
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from config.settings import MESSAGE_TYPES, PROTOCOL_VERSION

logger = logging.getLogger(__name__)


class Message:
    """
    Classe base para mensagens do protocolo
    """

    def __init__(
        self,
        msg_type: str,
        session_id: str = None,
        data: Dict[str, Any] = None,
        timestamp: str = None
    ):
        """
        Inicializa uma mensagem

        Args:
            msg_type (str): Tipo da mensagem (AUTH_REQUEST, SCREEN_CAPTURE, etc)
            session_id (str): ID da sessão (opcional)
            data (Dict): Dados da mensagem
            timestamp (str): Timestamp da mensagem (auto-gerado se não fornecido)
        """
        self.msg_type = msg_type
        self.session_id = session_id
        self.data = data or {}
        self.timestamp = timestamp or datetime.utcnow().isoformat()
        self.protocol_version = PROTOCOL_VERSION

    def to_dict(self) -> Dict[str, Any]:
        """Converte mensagem para dicionário"""
        return {
            "protocol_version": self.protocol_version,
            "type": self.msg_type,
            "session_id": self.session_id,
            "timestamp": self.timestamp,
            "data": self.data
        }

    def to_json(self) -> str:
        """Converte mensagem para JSON"""
        return json.dumps(self.to_dict())

    @staticmethod
    def from_dict(data: Dict) -> "Message":
        """Cria mensagem a partir de dicionário"""
        return Message(
            msg_type=data.get("type"),
            session_id=data.get("session_id"),
            data=data.get("data", {}),
            timestamp=data.get("timestamp")
        )

    @staticmethod
    def from_json(json_str: str) -> "Message":
        """Cria mensagem a partir de JSON"""
        data = json.loads(json_str)
        return Message.from_dict(data)

    def __repr__(self):
        return f"Message(type={self.msg_type}, session_id={self.session_id})"


class ProtocolHandler:
    """
    Gerenciador do protocolo de comunicação
    Responsável por serializar/desserializar mensagens com tamanho e criptografia
    """

    HEADER_FORMAT = "!I"  # Unsigned int de 4 bytes para tamanho
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

    @staticmethod
    def create_auth_request(
        username: str,
        password_hash: str,
        device_name: str = None
    ) -> Message:
        """Cria mensagem de autenticação"""
        return Message(
            msg_type=MESSAGE_TYPES["AUTH_REQUEST"],
            data={
                "username": username,
                "password": password_hash,
                "device_name": device_name or "Unknown Device"
            }
        )

    @staticmethod
    def create_auth_response(
        success: bool,
        session_id: str = None,
        message: str = None,
        server_nonce: str = None
    ) -> Message:
        """Cria resposta de autenticação"""
        return Message(
            msg_type=MESSAGE_TYPES["AUTH_RESPONSE"],
            session_id=session_id,
            data={
                "success": success,
                "message": message or ("Autenticado com sucesso!" if success else "Falha na autenticação"),
                "server_nonce": server_nonce
            }
        )

    @staticmethod
    def create_screen_capture(
        session_id: str,
        image_data: bytes,
        compression_type: str = "jpeg",
        width: int = None,
        height: int = None
    ) -> Message:
        """Cria mensagem de captura de tela"""
        import base64
        return Message(
            msg_type=MESSAGE_TYPES["SCREEN_CAPTURE"],
            session_id=session_id,
            data={
                "image": base64.b64encode(image_data).decode(),
                "compression": compression_type,
                "width": width,
                "height": height
            }
        )

    @staticmethod
    def create_mouse_event(
        session_id: str,
        x: int,
        y: int,
        button: str = "move",
        action: str = None
    ) -> Message:
        """
        Cria evento de mouse

        Args:
            session_id: ID da sessão
            x: Coordenada X
            y: Coordenada Y
            button: "left", "right", "middle", "scroll", "move"
            action: "press", "release" (opcional para move/scroll)
        """
        return Message(
            msg_type=MESSAGE_TYPES["MOUSE_EVENT"],
            session_id=session_id,
            data={
                "x": x,
                "y": y,
                "button": button,
                "action": action
            }
        )

    @staticmethod
    def create_keyboard_event(
        session_id: str,
        key: str,
        action: str = "press"
    ) -> Message:
        """
        Cria evento de teclado

        Args:
            session_id: ID da sessão
            key: Tecla (ex: "a", "shift", "return", "f1")
            action: "press" ou "release"
        """
        return Message(
            msg_type=MESSAGE_TYPES["KEYBOARD_EVENT"],
            session_id=session_id,
            data={
                "key": key,
                "action": action
            }
        )

    @staticmethod
    def create_ping(session_id: str = None) -> Message:
        """Cria ping"""
        return Message(
            msg_type=MESSAGE_TYPES["PING"],
            session_id=session_id,
            data={"timestamp": datetime.utcnow().isoformat()}
        )

    @staticmethod
    def create_pong(session_id: str = None) -> Message:
        """Cria pong (resposta de ping)"""
        return Message(
            msg_type=MESSAGE_TYPES["PONG"],
            session_id=session_id,
            data={"timestamp": datetime.utcnow().isoformat()}
        )

    @staticmethod
    def create_error(
        session_id: str,
        error_code: int,
        message: str
    ) -> Message:
        """Cria mensagem de erro"""
        return Message(
            msg_type=MESSAGE_TYPES["ERROR"],
            session_id=session_id,
            data={
                "error_code": error_code,
                "message": message
            }
        )

    @staticmethod
    def create_disconnect(session_id: str, reason: str = None) -> Message:
        """Cria mensagem de desconexão"""
        return Message(
            msg_type=MESSAGE_TYPES["DISCONNECT"],
            session_id=session_id,
            data={
                "reason": reason or "Desconexão normal"
            }
        )

    @staticmethod
    def serialize_message(msg: Message) -> bytes:
        """
        Serializa mensagem para bytes com header de tamanho

        Formato:
        [4 bytes: tamanho da mensagem JSON] [JSON]

        Args:
            msg (Message): Mensagem a serializar

        Returns:
            bytes: Dados serializados
        """
        json_data = msg.to_json().encode()
        size = struct.pack(ProtocolHandler.HEADER_FORMAT, len(json_data))
        return size + json_data

    @staticmethod
    def deserialize_message(data: bytes) -> Tuple[Optional[Message], bytes]:
        """
        Desserializa mensagem de bytes

        Args:
            data (bytes): Dados a desserializar

        Returns:
            Tuple[Message, remaining_bytes]: Mensagem (ou None se incompleta) e dados restantes
        """
        if len(data) < ProtocolHandler.HEADER_SIZE:
            return None, data

        # Lê tamanho
        msg_size = struct.unpack(
            ProtocolHandler.HEADER_FORMAT,
            data[:ProtocolHandler.HEADER_SIZE]
        )[0]

        # Verifica se tem dados suficientes
        total_needed = ProtocolHandler.HEADER_SIZE + msg_size
        if len(data) < total_needed:
            return None, data

        # Extrai JSON e desserializa
        json_data = data[ProtocolHandler.HEADER_SIZE:total_needed]

        try:
            msg = Message.from_json(json_data.decode())
            remaining = data[total_needed:]
            return msg, remaining
        except Exception as e:
            logger.error(f"Erro ao desserializar mensagem: {e}")
            return None, data[total_needed:]


# Exemplo de uso
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)

    # Teste de criação de mensagem
    msg = ProtocolHandler.create_auth_request("usuario", "hash_senha_123", "PC-Teste")
    print("Mensagem original:")
    print(msg.to_dict())

    # Teste de serialização
    serialized = ProtocolHandler.serialize_message(msg)
    print(f"\nSerializado: {len(serialized)} bytes")

    # Teste de desserialização
    deserialized, remaining = ProtocolHandler.deserialize_message(serialized)
    print(f"\nDesserializado:")
    print(deserialized.to_dict())
    print(f"Dados restantes: {len(remaining)} bytes")
