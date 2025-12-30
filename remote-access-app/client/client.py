"""
Cliente de acesso remoto para Windows
Interface e lógica de conexão
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

# Adiciona diretório pai ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import (
    DEFAULT_SERVER_HOST, DEFAULT_SERVER_PORT, LOG_FILE, LOG_LEVEL,
    SCREEN_CAPTURE_FPS, SCREEN_QUALITY
)
from shared.protocol import ProtocolHandler, Message
from shared.encryption import CryptoManager
from shared.screen_capture import ScreenCapture

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


@dataclass
class ClientConfig:
    """Configuração do cliente"""
    server_host: str = DEFAULT_SERVER_HOST
    server_port: int = DEFAULT_SERVER_PORT
    username: str = "admin"
    password: str = "admin123"
    device_name: str = "RemotePC"
    capture_fps: int = SCREEN_CAPTURE_FPS
    capture_quality: int = SCREEN_QUALITY


class RemoteAccessClient:
    """
    Cliente de acesso remoto
    """

    def __init__(self, config: ClientConfig):
        self.config = config
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.session_id: Optional[str] = None
        self.authenticated = False
        self.crypto = CryptoManager("sua-chave-secreta-super-segura-32-chars!!")
        self.screen_capture = ScreenCapture(
            target_fps=config.capture_fps,
            quality=config.capture_quality
        )
        self.running = False
        self.buffer = b""

        logger.info(f"Cliente inicializado: {config.username}@{config.server_host}:{config.server_port}")

    async def connect(self) -> bool:
        """
        Conecta ao servidor

        Returns:
            bool: True se conectado com sucesso
        """
        try:
            self.reader, self.writer = await asyncio.open_connection(
                self.config.server_host,
                self.config.server_port
            )

            logger.info(f"Conectado ao servidor em {self.config.server_host}:{self.config.server_port}")

            # Autentica
            if await self.authenticate():
                self.running = True
                return True
            else:
                self.disconnect()
                return False

        except Exception as e:
            logger.error(f"Erro ao conectar: {e}")
            return False

    async def authenticate(self) -> bool:
        """
        Autentica no servidor

        Returns:
            bool: True se autenticado
        """
        try:
            # Cria mensagem de autenticação
            password_hash = CryptoManager.hash_password(self.config.password)
            auth_msg = ProtocolHandler.create_auth_request(
                self.config.username,
                password_hash,
                self.config.device_name
            )

            # Envia
            auth_data = ProtocolHandler.serialize_message(auth_msg)
            self.writer.write(auth_data)
            await self.writer.drain()

            logger.info("Mensagem de autenticação enviada")

            # Aguarda resposta
            response_data = await self.reader.read(4096)

            if not response_data:
                logger.error("Servidor desconectou antes de responder")
                return False

            # Processa resposta
            msg, _ = ProtocolHandler.deserialize_message(response_data)

            if msg and msg.msg_type == "auth_res":
                if msg.data.get("success"):
                    self.session_id = msg.session_id
                    self.authenticated = True
                    logger.info(f"Autenticação bem-sucedida. Session ID: {self.session_id}")
                    return True
                else:
                    logger.error(f"Falha na autenticação: {msg.data.get('message')}")
                    return False

            logger.error("Resposta de autenticação inválida")
            return False

        except Exception as e:
            logger.error(f"Erro ao autenticar: {e}")
            return False

    async def start_capture_loop(self):
        """Inicia loop de captura de tela"""
        if not self.authenticated or not self.writer:
            logger.error("Cliente não autenticado ou não conectado")
            return

        logger.info("Iniciando loop de captura de tela")

        try:
            while self.running:
                # Captura tela
                result = self.screen_capture.capture_frame()

                if result:
                    jpeg_data, (width, height) = result

                    # Cria mensagem
                    screen_msg = ProtocolHandler.create_screen_capture(
                        self.session_id,
                        jpeg_data,
                        compression_type="jpeg",
                        width=width,
                        height=height
                    )

                    # Envia
                    screen_data = ProtocolHandler.serialize_message(screen_msg)
                    self.writer.write(screen_data)
                    await self.writer.drain()

                    logger.debug(f"Tela enviada: {len(jpeg_data)} bytes ({width}x{height})")

                else:
                    await asyncio.sleep(0.01)

        except Exception as e:
            logger.error(f"Erro no loop de captura: {e}")
        finally:
            logger.info("Loop de captura encerrado")

    async def start_receive_loop(self):
        """Inicia loop de recepção de eventos"""
        if not self.authenticated or not self.reader:
            return

        logger.info("Iniciando loop de recepção de eventos")

        try:
            while self.running:
                data = await asyncio.wait_for(
                    self.reader.read(4096),
                    timeout=30.0
                )

                if not data:
                    logger.warning("Servidor desconectou")
                    self.running = False
                    break

                self.buffer += data

                # Processa mensagens
                while self.buffer:
                    msg, self.buffer = ProtocolHandler.deserialize_message(self.buffer)

                    if msg is None:
                        break

                    await self._handle_message(msg)

        except asyncio.TimeoutError:
            logger.warning("Timeout na recepção de dados")
        except Exception as e:
            logger.error(f"Erro no loop de recepção: {e}")
        finally:
            logger.info("Loop de recepção encerrado")

    async def _handle_message(self, msg: Message):
        """Processa mensagem recebida"""
        msg_type = msg.msg_type

        logger.debug(f"Mensagem recebida: {msg_type}")

        if msg_type == "mouse_evt":
            # Simula movimento de mouse
            x = msg.data.get("x")
            y = msg.data.get("y")
            logger.info(f"Evento de mouse: ({x}, {y})")

        elif msg_type == "key_evt":
            # Simula pressionamento de tecla
            key = msg.data.get("key")
            action = msg.data.get("action")
            logger.info(f"Evento de teclado: {action} {key}")

        elif msg_type == "ping":
            # Responde com pong
            pong = ProtocolHandler.create_pong(self.session_id)
            pong_data = ProtocolHandler.serialize_message(pong)
            self.writer.write(pong_data)
            await self.writer.drain()

    async def run(self):
        """Executa cliente"""
        if not await self.connect():
            logger.error("Falha ao conectar ao servidor")
            return

        # Inicia loops de captura e recepção
        try:
            await asyncio.gather(
                self.start_capture_loop(),
                self.start_receive_loop()
            )
        except KeyboardInterrupt:
            logger.info("Cliente interrompido pelo usuário")
        except Exception as e:
            logger.error(f"Erro no cliente: {e}")
        finally:
            self.disconnect()

    def disconnect(self):
        """Desconecta do servidor"""
        self.running = False

        if self.session_id and self.writer:
            try:
                msg = ProtocolHandler.create_disconnect(
                    self.session_id,
                    "Desconexão normal"
                )
                data = ProtocolHandler.serialize_message(msg)
                self.writer.write(data)
            except Exception as e:
                logger.error(f"Erro ao enviar desconexão: {e}")

        if self.writer:
            try:
                self.writer.close()
            except:
                pass

        self.screen_capture.close()
        logger.info("Cliente desconectado")


async def main():
    """Função principal"""
    config = ClientConfig(
        server_host="localhost",
        server_port=5500,
        username="admin",
        password="admin123",
        device_name="PC-Teste"
    )

    client = RemoteAccessClient(config)

    try:
        await client.run()
    except KeyboardInterrupt:
        logger.info("Aplicação interrompida")


if __name__ == "__main__":
    asyncio.run(main())
