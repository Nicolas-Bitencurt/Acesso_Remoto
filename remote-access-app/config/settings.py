"""
Arquivo de configuração centralizada da aplicação
"""

import os
from pathlib import Path

# Diretórios principais
BASE_DIR = Path(__file__).resolve().parent.parent
SERVER_DIR = BASE_DIR / "server"
CLIENT_DIR = BASE_DIR / "client"
SHARED_DIR = BASE_DIR / "shared"
LOGS_DIR = BASE_DIR / "logs"

# Criar diretório de logs se não existir
LOGS_DIR.mkdir(exist_ok=True)

# ==================== CONFIGURAÇÕES DO SERVIDOR ====================

# Servidor TCP
SERVER_HOST = "0.0.0.0"  # Escuta em todas as interfaces
SERVER_PORT = 5500
SERVER_TIMEOUT = 30

# Banco de dados de usuários (para MVP, arquivo JSON)
USERS_DB_FILE = LOGS_DIR / "users.json"
SESSIONS_DB_FILE = LOGS_DIR / "sessions.json"

# ==================== CONFIGURAÇÕES DO CLIENTE ====================

# Conexão com servidor
DEFAULT_SERVER_HOST = "localhost"
DEFAULT_SERVER_PORT = SERVER_PORT

# Captura de tela
SCREEN_CAPTURE_FPS = 15
SCREEN_QUALITY = 80  # Qualidade JPEG (0-100)
SCREEN_RESIZE_SCALE = 1.0  # 1.0 = sem redimensionamento

# Mouse/Teclado
INPUT_DELAY = 0.05  # Delay mínimo entre eventos (segundos)

# ==================== SEGURANÇA ====================

# Criptografia
ENCRYPTION_ALGORITHM = "AES-256-GCM"
HASH_ALGORITHM = "sha256"

# Chaves (em produção, usar variáveis de ambiente)
SECRET_KEY = "sua-chave-secreta-super-segura-32-chars!!"  # ⚠️ MUDAR EM PRODUÇÃO

# Autenticação
SESSION_TIMEOUT = 3600  # 1 hora em segundos
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION = 300  # 5 minutos em segundos

# ==================== LOGGING ====================

LOG_FILE = LOGS_DIR / "app.log"
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# ==================== LIMITES ====================

# Tamanho máximo de pacote
MAX_PACKET_SIZE = 1024 * 1024  # 1 MB

# Máximo de conexões simultâneas
MAX_CONNECTIONS = 100

# Bandwidth (bytes por segundo) - 0 = ilimitado
BANDWIDTH_LIMIT = 0

# ==================== MODO DEBUG ====================

DEBUG = True
VERBOSE = True

# ==================== FORMATOS DE MENSAGEM ====================

PROTOCOL_VERSION = "1.0"
MESSAGE_TYPES = {
    "AUTH_REQUEST": "auth_req",
    "AUTH_RESPONSE": "auth_res",
    "SCREEN_CAPTURE": "screen_cap",
    "MOUSE_EVENT": "mouse_evt",
    "KEYBOARD_EVENT": "key_evt",
    "PING": "ping",
    "PONG": "pong",
    "DISCONNECT": "disconnect",
    "ERROR": "error",
    "NOTIFICATION": "notification"
}

# ==================== COMPRESSÃO ====================

# Método de compressão de imagem
COMPRESSION_ENABLED = True
COMPRESSION_METHOD = "jpeg"  # png, jpeg
COMPRESSION_LEVEL = 85  # Para JPEG

# ==================== RESOLUÇÃO DA TELA ====================

# Resoluções recomendadas para teste
SCREEN_RESOLUTIONS = [
    (1920, 1080),
    (1366, 768),
    (1024, 768),
    (800, 600)
]

print("[CONFIG] Configurações carregadas com sucesso!")
print(f"[CONFIG] Diretório base: {BASE_DIR}")
