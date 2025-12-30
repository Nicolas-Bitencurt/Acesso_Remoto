# 📋 Especificação do Protocolo

## Visão Geral

Protocolo binário baseado em TCP para comunicação entre Cliente e Servidor no Remote Access App.

**Versão:** 1.0  
**Porta Padrão:** 5500  
**Encoding:** UTF-8 para strings  

---

## Formato de Pacote

### Estrutura

```
┌─────────────┬──────────────────────┐
│  Header     │  Payload             │
├─────────────┼──────────────────────┤
│ 4 bytes     │  N bytes             │
│ (tamanho)   │  (dados JSON)        │
└─────────────┴──────────────────────┘
```

### Header

```
┌──────────┬──────────┬──────────┬──────────┐
│ Byte 0   │ Byte 1   │ Byte 2   │ Byte 3   │
├──────────┼──────────┼──────────┼──────────┤
│ Tamanho (32-bit big-endian)              │
└──────────┴──────────┴──────────┴──────────┘

Exemplo: 
- Payload de 500 bytes
- Header: 0x000001F4 (500 em hexadecimal big-endian)
```

### Payload (JSON)

```json
{
  "protocol_version": "1.0",
  "type": "string - tipo da mensagem",
  "session_id": "string ou null - ID da sessão",
  "timestamp": "ISO 8601 - data/hora UTC",
  "data": {
    "campo1": "valor",
    "campo2": 123
  }
}
```

---

## Tipos de Mensagem

### 1. AUTH_REQUEST

**Descrição:** Cliente solicita autenticação

**Direction:** Cliente → Servidor

**Estrutura:**
```json
{
  "type": "auth_req",
  "session_id": null,
  "data": {
    "username": "admin",
    "password": "hash_sha256_da_senha",
    "device_name": "PC-Sala-01"
  }
}
```

**Validações:**
- `username`: 1-64 caracteres, alfanumérico + underscore
- `password`: 64 caracteres (hex SHA-256)
- `device_name`: opcional, máx 128 caracteres

**Exemplo de requisição:**
```bash
# Cliente envia:
{
  "protocol_version": "1.0",
  "type": "auth_req",
  "session_id": null,
  "timestamp": "2024-12-30T10:15:36.123456",
  "data": {
    "username": "admin",
    "password": "8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918",
    "device_name": "PC-Nicolas"
  }
}
```

### 2. AUTH_RESPONSE

**Descrição:** Servidor responde autenticação

**Direction:** Servidor → Cliente

**Estrutura:**
```json
{
  "type": "auth_res",
  "session_id": "abc123def456...",
  "data": {
    "success": true,
    "message": "Autenticado com sucesso!",
    "server_nonce": "optional_nonce_value"
  }
}
```

**Respostas Possíveis:**
```json
// Sucesso
{
  "success": true,
  "message": "Autenticado com sucesso!",
  "session_id": "a1b2c3d4e5f6..."
}

// Falha - Credenciais Inválidas
{
  "success": false,
  "message": "Usuário ou senha inválidos",
  "session_id": null
}

// Falha - Conta Bloqueada
{
  "success": false,
  "message": "Usuário bloqueado. Tente novamente em 300s",
  "session_id": null
}
```

### 3. SCREEN_CAPTURE

**Descrição:** Cliente envia captura de tela

**Direction:** Cliente → Servidor → Cliente(s)

**Estrutura:**
```json
{
  "type": "screen_cap",
  "session_id": "abc123def456...",
  "data": {
    "image": "base64_encoded_jpeg_data",
    "compression": "jpeg",
    "width": 1920,
    "height": 1080,
    "timestamp": "2024-12-30T10:15:36.456789"
  }
}
```

**Campos:**
- `image`: Base64 da imagem comprimida
- `compression`: "jpeg" ou "png"
- `width`: largura em pixels
- `height`: altura em pixels

**Exemplo (truncado):**
```json
{
  "type": "screen_cap",
  "session_id": "a1b2c3d4e5f6...",
  "data": {
    "image": "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBD...",
    "compression": "jpeg",
    "width": 1920,
    "height": 1080
  }
}
```

**Tamanho Típico:**
- Sem compressão: 24 MB (1920x1080 RGB)
- Com JPEG 80%: ~45 KB
- Compressão: 99.8%

### 4. MOUSE_EVENT

**Descrição:** Evento de mouse

**Direction:** Cliente → Servidor → Cliente

**Estrutura:**
```json
{
  "type": "mouse_evt",
  "session_id": "abc123def456...",
  "data": {
    "x": 960,
    "y": 540,
    "button": "left",
    "action": "press"
  }
}
```

**Campos:**
- `x`: coordenada X (0-width)
- `y`: coordenada Y (0-height)
- `button`: "left", "right", "middle", "scroll", "move"
- `action`: "press", "release" (opcional para "move")

**Exemplos:**
```json
// Movimento do mouse
{
  "data": {
    "x": 100,
    "y": 200,
    "button": "move"
  }
}

// Clique esquerdo
{
  "data": {
    "x": 100,
    "y": 200,
    "button": "left",
    "action": "press"
  }
}

// Scroll
{
  "data": {
    "button": "scroll",
    "action": "up"
  }
}
```

### 5. KEYBOARD_EVENT

**Descrição:** Evento de teclado

**Direction:** Cliente → Servidor → Cliente

**Estrutura:**
```json
{
  "type": "key_evt",
  "session_id": "abc123def456...",
  "data": {
    "key": "a",
    "action": "press"
  }
}
```

**Campos:**
- `key`: tecla (ex: "a", "shift", "ctrl", "return", "f1")
- `action`: "press" ou "release"

**Exemplos:**
```json
// Digitar 'a'
{"data": {"key": "a", "action": "press"}}
{"data": {"key": "a", "action": "release"}}

// Ctrl+C
{"data": {"key": "ctrl", "action": "press"}}
{"data": {"key": "c", "action": "press"}}
{"data": {"key": "c", "action": "release"}}
{"data": {"key": "ctrl", "action": "release"}}

// F1
{"data": {"key": "f1", "action": "press"}}
```

### 6. PING

**Descrição:** Keep-alive / latência

**Direction:** Bidirecional

**Estrutura:**
```json
{
  "type": "ping",
  "session_id": "abc123def456...",
  "data": {
    "timestamp": "2024-12-30T10:15:36.789012"
  }
}
```

**Objetivo:** Manter conexão ativa, detectar timeouts

### 7. PONG

**Descrição:** Resposta a PING

**Direction:** Bidirecional

**Estrutura:**
```json
{
  "type": "pong",
  "session_id": "abc123def456...",
  "data": {
    "timestamp": "2024-12-30T10:15:36.789012"
  }
}
```

### 8. DISCONNECT

**Descrição:** Encerrar conexão

**Direction:** Cliente → Servidor

**Estrutura:**
```json
{
  "type": "disconnect",
  "session_id": "abc123def456...",
  "data": {
    "reason": "Usuário solicitou desconexão"
  }
}
```

### 9. ERROR

**Descrição:** Erro na comunicação

**Direction:** Bidirecional

**Estrutura:**
```json
{
  "type": "error",
  "session_id": "abc123def456...",
  "data": {
    "error_code": 400,
    "message": "Descrição do erro"
  }
}
```

**Códigos de Erro:**
- `400`: Bad Request - Mensagem inválida
- `401`: Unauthorized - Sessão inválida
- `403`: Forbidden - Permissão negada
- `413`: Payload Too Large - Pacote > 1 MB
- `500`: Internal Server Error - Erro no servidor

**Exemplos:**
```json
// Sessão inválida
{
  "error_code": 401,
  "message": "Sessão inválida ou expirada"
}

// Tipo desconhecido
{
  "error_code": 400,
  "message": "Tipo de mensagem desconhecido: xyz"
}
```

---

## Fluxo de Sessão

```
Cliente                          Servidor
  │                                 │
  ├──────── AUTH_REQUEST ────────>│
  │         (user, pass)           │
  │                                ├─ Valida credenciais
  │                                ├─ Cria sessão
  │                                ├─ Gera session_id
  │                                │
  │<────── AUTH_RESPONSE ──────────┤
  │         (session_id, success)  │
  │                                │
  ├──────── SCREEN_CAPTURE ──────>│
  │         (session_id, jpeg)     │
  │                                ├─ Autentica sessão
  │                                ├─ Roteia para clientes
  │                                │
  │<─────── MOUSE_EVENT ───────────┤
  │         (session_id, coords)   │
  │                                │
  ├────── KEYBOARD_EVENT ────────>│
  │         (session_id, key)      │
  │                                │
  ├──────────── PING ────────────>│
  │                                │
  │<───────── PONG ────────────────┤
  │                                │
  ├──────── DISCONNECT ──────────>│
  │         (session_id, reason)   │
  │                                ├─ Encerra sessão
  │                                │
  └────────────────────────────────┘
```

---

## Implementação em Python

### Serialização

```python
from shared.protocol import ProtocolHandler, Message

# Criar mensagem
msg = ProtocolHandler.create_auth_request("admin", "hash_senha")

# Serializar
serialized = ProtocolHandler.serialize_message(msg)
# Result: b'\x00\x00\x01\xf4{"protocol_version":"1.0","type":"auth_req"...}'

# Enviar
writer.write(serialized)
await writer.drain()
```

### Desserialização

```python
# Receber bytes
buffer = b'\x00\x00\x01\xf4{"protocol_version":"1.0",...}'

# Desserializar
msg, remaining = ProtocolHandler.deserialize_message(buffer)

# Usar
if msg.msg_type == "auth_res":
    session_id = msg.session_id
    success = msg.data.get("success")
```

---

## Limites e Especificações

| Parâmetro | Valor | Justificativa |
|-----------|-------|---------------|
| Max Tamanho Pacote | 1 MB | Evita DoS |
| Max Session ID | 64 chars | 256 bits aleatório |
| Timeout Conexão | 30 seg | Detectar clientes zumbis |
| Timeout Sessão | 3600 seg | 1 hora de inatividade |
| Max Conexões | 100 | MVP - escalar depois |
| FPS Captura | 15 | ~600 KB/s |
| Qualidade JPEG | 80% | Balance compressão/qualidade |

---

## Segurança do Protocolo

### Criptografia (Opcional, para MVP)

```json
// Mensagem DESCRIPTOGRAFADA
{
  "type": "screen_cap",
  "session_id": "abc123",
  "data": {"image": "..."}
}

// Mensagem CRIPTOGRAFADA (futuro)
{
  "type": "encrypted",
  "data": {
    "ciphertext": "base64_encrypted_json",
    "nonce": "base64_nonce_12_bytes",
    "tag": "base64_auth_tag_16_bytes",
    "aad": null
  }
}
```

### Validações Obrigatórias

1. **Verificar Protocol Version**
   ```python
   if msg.protocol_version != "1.0":
       return error(400, "Versão incompatível")
   ```

2. **Validar Sessão**
   ```python
   if msg.type != "auth_req" and not is_session_valid(msg.session_id):
       return error(401, "Sessão inválida")
   ```

3. **Tamanho Máximo**
   ```python
   if len(serialized) > 1024 * 1024:
       return error(413, "Pacote muito grande")
   ```

4. **Tipo de Mensagem**
   ```python
   if msg.type not in VALID_TYPES:
       return error(400, "Tipo desconhecido")
   ```

---

## Exemplos Completos

### Exemplo 1: Login

**Cliente:**
```python
msg = ProtocolHandler.create_auth_request(
    "admin",
    CryptoManager.hash_password("admin123"),
    "PC-01"
)
data = ProtocolHandler.serialize_message(msg)
writer.write(data)
await writer.drain()
```

**Servidor:**
```python
msg, _ = ProtocolHandler.deserialize_message(data)
error = user_manager.authenticate(msg.data["username"], msg.data["password"])
if not error:
    session_id = session_manager.create_session(msg.data["username"])
    response = ProtocolHandler.create_auth_response(True, session_id)
else:
    response = ProtocolHandler.create_auth_response(False, None, error)
```

**Resposta:**
```python
data = ProtocolHandler.serialize_message(response)
writer.write(data)
```

### Exemplo 2: Transmissão de Tela

**Cliente:**
```python
screenshot, (w, h) = screen_capture.capture_frame()
msg = ProtocolHandler.create_screen_capture(
    session_id="abc123",
    image_data=screenshot,
    width=w,
    height=h
)
data = ProtocolHandler.serialize_message(msg)
writer.write(data)
```

**Servidor:**
```python
msg, _ = ProtocolHandler.deserialize_message(data)
if session_manager.is_session_valid(msg.session_id):
    # Roteia para outros clientes
    for client_socket in active_clients:
        client_socket.write(data)
        await client_socket.drain()
```

---

Última atualização: 30 de Dezembro de 2024
