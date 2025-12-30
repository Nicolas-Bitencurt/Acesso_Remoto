# 🏗️ Documentação da Arquitetura

## Índice

1. [Visão Geral](#visão-geral)
2. [Camadas](#camadas)
3. [Fluxo de Dados](#fluxo-de-dados)
4. [Componentes Detalhados](#componentes-detalhados)
5. [Integração](#integração)

---

## Visão Geral

```
┌──────────────────────────────────────────────────────────────┐
│                    REMOTE ACCESS APP                         │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │          CAMADA DE APLICAÇÃO                            │ │
│  │  (Client: Captura | Server: Autenticação & Roteamento)  │ │
│  └─────────────────────────────────────────────────────────┘ │
│                           △                                   │
│                           │                                   │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │          CAMADA DE PROTOCOLO                            │ │
│  │  (Serialização, Desserialização, Compressão)            │ │
│  └─────────────────────────────────────────────────────────┘ │
│                           △                                   │
│                           │                                   │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │          CAMADA DE SEGURANÇA                            │ │
│  │  (Criptografia AES-256, Hash SHA-256)                   │ │
│  └─────────────────────────────────────────────────────────┘ │
│                           △                                   │
│                           │                                   │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │          CAMADA DE TRANSPORTE                           │ │
│  │  (TCP Sockets, Asyncio)                                 │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

---

## Camadas

### 1. Camada de Transporte (Nível Mais Baixo)

**Responsabilidade:** Comunicação de rede

**Componentes:**
- `asyncio.StreamReader/StreamWriter` - I/O assíncrono
- TCP Sockets - Protocolo de comunicação

**Características:**
- Comunicação bidirecional
- Tratamento assíncrono
- Timeout automático

```python
# Exemplo
reader, writer = await asyncio.open_connection("localhost", 5500)
```

### 2. Camada de Segurança

**Responsabilidade:** Proteger dados em trânsito

**Componentes:**
- `CryptoManager` - Criptografia/descriptografia
- Hash de senhas

**Algoritmos:**
- AES-256-GCM (autenticado)
- SHA-256 (hashing)
- PBKDF2 (derivação de chave)

```python
crypto = CryptoManager("chave-mestra")
encrypted = crypto.encrypt("dados sensíveis")
```

### 3. Camada de Protocolo

**Responsabilidade:** Estruturar mensagens

**Componentes:**
- `Message` - Classe de mensagem
- `ProtocolHandler` - Serialização/desserialização

**Formato:**
```
[4 bytes: tamanho] [JSON: tipo, sessão, dados, timestamp]
```

```python
msg = ProtocolHandler.create_screen_capture(session_id, jpeg_data)
serialized = ProtocolHandler.serialize_message(msg)
```

### 4. Camada de Aplicação (Nível Mais Alto)

**Responsabilidade:** Lógica de negócio

**Componentes:**
- `RemoteAccessBroker` (servidor)
- `RemoteAccessClient` (cliente)
- `ScreenCapture` (captura)

**Funcionalidades:**
- Autenticação de usuários
- Gerenciamento de sessões
- Captura de tela
- Roteamento de eventos

---

## Fluxo de Dados

### Autenticação

```
CLIENTE                        SERVIDOR
   │                               │
   ├─── AUTH_REQUEST ────────────>│
   │     (username, password)      │
   │                               ├─ Verifica credenciais
   │                               ├─ Cria sessão
   │                               │
   │<────── AUTH_RESPONSE ─────────┤
   │     (session_id, sucesso)     │
   │                               │
```

### Captura de Tela

```
CLIENTE (Capturador)          SERVIDOR          CLIENTE (Receptor)
        │                        │                       │
        ├─ Captura frame        │                       │
        ├─ Comprime JPEG        │                       │
        ├─ SCREEN_CAPTURE ─────>│                       │
        │     (JPEG data)       ├─ Autentica sessão    │
        │                       ├─ Roteia para clientes│
        │                       ├─ SCREEN_CAPTURE ────>│
        │                       │     (JPEG data)      │
        │                       │                      ├─ Descomprime
        │                       │                      ├─ Exibe na tela
```

### Eventos de Input

```
CLIENTE (Controlador)         SERVIDOR          CLIENTE (Controlado)
        │                        │                       │
        ├─ Clique mouse         │                       │
        ├─ MOUSE_EVENT ────────>│                       │
        │     (x, y, button)    ├─ Autentica sessão    │
        │                       ├─ Roteia para cliente │
        │                       ├─ MOUSE_EVENT ───────>│
        │                       │     (x, y, button)   │
        │                       │                      ├─ Simula evento
```

---

## Componentes Detalhados

### Server (server/server.py)

```
RemoteAccessBroker
├── handle_client()         # Gerencia conexão de cliente
├── _process_message()      # Processa mensagens recebidas
├── _handle_auth()          # Processa autenticação
└── start()                 # Inicia servidor assincronamente

UserManager
├── authenticate()          # Verifica credenciais
├── add_user()             # Adiciona novo usuário
├── _load_users()          # Carrega de arquivo JSON
└── _save_users()          # Salva em arquivo JSON

SessionManager
├── create_session()        # Cria nova sessão
├── is_session_valid()      # Verifica validade
├── update_activity()       # Atualiza timestamp
├── end_session()          # Encerra sessão
└── get_session_info()     # Retorna dados da sessão
```

**Fluxo de Execução:**

```
1. Servidor inicia (start())
   └─ Bind na porta 5500
   └─ Aguarda conexões

2. Cliente conecta
   └─ handle_client() inicia
   └─ Buffer de dados criado

3. Recebe AUTH_REQUEST
   └─ _process_message()
   └─ _handle_auth()
   └─ UserManager.authenticate()
   └─ SessionManager.create_session()
   └─ Retorna AUTH_RESPONSE com session_id

4. Recebe mensagens autenticadas
   └─ _process_message()
   └─ SessionManager.is_session_valid()
   └─ Roteia para outro cliente ou armazena

5. Cliente desconecta
   └─ SessionManager.end_session()
   └─ writer.close()
```

### Client (client/client.py)

```
RemoteAccessClient
├── connect()              # Conecta ao servidor
├── authenticate()         # Envia credenciais
├── start_capture_loop()   # Loop de captura de tela
├── start_receive_loop()   # Loop de recepção de eventos
├── _handle_message()      # Processa eventos recebidos
├── run()                  # Executa cliente (gather loops)
└── disconnect()           # Desconecta do servidor

ScreenCapture (shared/screen_capture.py)
├── capture_frame()        # Captura um frame
├── _resize_frame()        # Redimensiona imagem
├── _compress_frame()      # Comprime para JPEG
└── get_monitor_info()     # Retorna info do monitor
```

**Fluxo de Execução:**

```
1. Cliente inicia (run())
   └─ connect()
      └─ Abre conexão TCP
      └─ authenticate()
         └─ Envia AUTH_REQUEST
         └─ Aguarda AUTH_RESPONSE
         └─ Armazena session_id

2. Inicia dois loops assincronamente (gather)
   ├─ start_capture_loop()
   │  └─ Captura frames a cada 1/FPS segundos
   │  └─ Comprime para JPEG
   │  └─ Envia SCREEN_CAPTURE ao servidor
   │
   └─ start_receive_loop()
      └─ Aguarda mensagens do servidor
      └─ Processa MOUSE_EVENT
      └─ Processa KEYBOARD_EVENT
      └─ Responde PING com PONG

3. Ciclo contínuo até disconnect
```

### Protocol (shared/protocol.py)

**Estrutura de Mensagem:**

```json
{
  "protocol_version": "1.0",
  "type": "screen_cap",
  "session_id": "abc123def456...",
  "timestamp": "2024-12-30T10:15:36.123456",
  "data": {
    "image": "base64_encoded_jpeg_data",
    "compression": "jpeg",
    "width": 1920,
    "height": 1080
  }
}
```

**Serialização:**

```
Entrada: Message object
   │
   ├─ to_dict() → Dicionário Python
   ├─ to_json() → String JSON
   ├─ serialize_message()
   │  ├─ Codifica JSON
   │  ├─ Calcula tamanho (4 bytes)
   │  └─ Concatena: [size][json_data]
   │
Saída: bytes para enviar via socket
```

**Desserialização:**

```
Entrada: bytes do socket
   │
   ├─ deserialize_message()
   │  ├─ Lê 4 primeiros bytes = tamanho
   │  ├─ Lê N bytes = dados JSON
   │  ├─ from_json()
   │  └─ from_dict()
   │
Saída: (Message, remaining_bytes)
```

### Encryption (shared/encryption.py)

**Processo de Criptografia:**

```
Plaintext
   │
   ├─ _derive_key()
   │  └─ PBKDF2(master_key, 100k iterações)
   │
   ├─ _generate_nonce()
   │  └─ 12 bytes aleatórios (ou counter para MVP)
   │
   ├─ AESGCM.encrypt()
   │  └─ Criptografa com nonce
   │  └─ Gera tag de autenticação (16 bytes)
   │
   └─ Retorna dicionário:
      {
        "ciphertext": "base64_dados_criptografados",
        "nonce": "base64_nonce_12_bytes",
        "tag": "base64_tag_16_bytes",
        "aad": "base64_associated_data"
      }
```

**Processo de Descriptografia:**

```
Encrypted Data
   │
   ├─ Decodifica de base64
   │
   ├─ _derive_key()
   │
   ├─ AESGCM.decrypt()
   │  ├─ Verifica tag (autenticação)
   │  ├─ Descriptografa com nonce
   │  └─ Retorna plaintext ou erro se falhar
   │
   └─ Plaintext (ou exceção)
```

### Screen Capture (shared/screen_capture.py)

**Pipeline de Captura:**

```
Monitor (1920x1080)
   │
   ├─ mss.grab() → Screenshot RGB
   │
   ├─ Aplicar escala (se configurado)
   │  └─ Redimensionar com Lanczos
   │
   ├─ Image.fromarray() → PIL Image
   │
   ├─ Salvar em memória (BytesIO)
   │  └─ JPEG compress, quality=80
   │
   └─ Retorna (jpeg_bytes, (width, height))

Output: ~40-50 KB por frame @ 15 FPS = ~600 KB/s
```

---

## Integração

### Fluxo Completo: Captura e Transmissão

```
┌─────────────────────────────────────────────────────────────────┐
│ CLIENTE A (Capturador)                                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ 1. ScreenCapture.capture_frame()                                │
│    → RGB frame (1920x1080)                                      │
│                                                                  │
│ 2. _compress_frame()                                            │
│    → JPEG (45 KB)                                               │
│                                                                  │
│ 3. ProtocolHandler.create_screen_capture()                      │
│    → Message object                                             │
│       {type: "screen_cap",                                      │
│        data: {image: "base64...", width: 1920, ...}}            │
│                                                                  │
│ 4. ProtocolHandler.serialize_message()                          │
│    → Binary: [size][json]                                       │
│                                                                  │
│ 5. CryptoManager.encrypt() [opcional]                           │
│    → {ciphertext, nonce, tag}                                   │
│                                                                  │
│ 6. writer.write() + await writer.drain()                        │
│    → TCP socket                                                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                            │ TCP
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ SERVIDOR (Broker)                                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ 1. reader.read(4096) → bytes                                    │
│                                                                  │
│ 2. ProtocolHandler.deserialize_message()                        │
│    → Message object                                             │
│                                                                  │
│ 3. _process_message()                                           │
│    ├─ Valida sessão                                             │
│    ├─ Atualiza atividade                                        │
│    └─ Roteia para cliente B                                     │
│                                                                  │
│ 4. ProtocolHandler.serialize_message()                          │
│    → Binary para enviar                                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                            │ TCP
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ CLIENTE B (Receptor)                                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ 1. reader.read(4096) → bytes                                    │
│                                                                  │
│ 2. ProtocolHandler.deserialize_message()                        │
│    → Message object                                             │
│                                                                  │
│ 3. _handle_message()                                            │
│    ├─ Extrai base64 image                                       │
│    ├─ Descomprime JPEG                                          │
│    └─ Exibe na tela                                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Decisões de Design

### 1. Por que asyncio em vez de threading?

- **asyncio** é mais eficiente para I/O
- Melhor para múltiplas conexões simultâneas
- Código mais legível com async/await
- Menos overhead de criação de threads

### 2. Por que TCP em vez de UDP?

- **TCP** garante entrega de pacotes
- Importante para eventos de controle
- Imagens podem ser comprimidas e retransmitidas
- UDP seria mais adequado para video em tempo real (futuro)

### 3. Por que JPEG em vez de PNG?

- **JPEG** menor (45 KB vs 200 KB para mesma imagem)
- 15 FPS * 45 KB = 675 KB/s vs PNG 3 MB/s
- Qualidade visual adequada para 80% de compressão
- PNG será opção secundária para imagens com pouca mudança

### 4. Por que JSON em vez de protobuf/messagepack?

- Prototipo/MVP requer ciclos rápidos
- JSON é human-readable (debugging)
- Sem necessidade de compilação .proto
- Futuro: otimizar com messagepack se necessário

### 5. Por que arquivo JSON para banco de dados?

- MVP não precisa de SQL database
- JSON é suficiente para poucos usuários
- Fácil de editar e debugar
- Futuro: migrar para PostgreSQL

---

## Escalabilidade

### Limite Atual

- **Máximo 100 conexões simultâneas** (MAX_CONNECTIONS)
- Servidor processa ~1-2 MB/s
- Cada client consome ~2-5 MB de RAM

### Para 1000+ Usuários

```python
# 1. Remover limite de conexões
MAX_CONNECTIONS = 10000

# 2. Usar load balancer (nginx)
# 3. Múltiplos servidores broker
# 4. Redis para sessões distribuídas
# 5. Database relacional (PostgreSQL)

# 6. Otimizar:
#    - Compressão diferencial
#    - Caching de frames
#    - Reduzir FPS adaptativamente
```

---

## Diagrama de Classes

```
┌─────────────────────────────┐
│        RemoteAccessApp      │
└──────────────┬──────────────┘
               │
       ┌───────┴───────┐
       │               │
   ┌───▼────┐      ┌───▼────┐
   │ Server │      │ Client │
   └───┬────┘      └───┬────┘
       │               │
   ┌───▼──────┐    ┌───▼─────────┐
   │ Managers │    │  Loaders    │
   ├──────────┤    ├─────────────┤
   │ User     │    │ Screen      │
   │ Session  │    │ Capture     │
   └──────────┘    └─────────────┘
       │               │
       └───────┬───────┘
               │
       ┌───────▼────────┐
       │     Shared     │
       ├────────────────┤
       │ Protocol       │
       │ Encryption     │
       │ Settings       │
       └────────────────┘
```

---

Última atualização: 30 de Dezembro de 2024
