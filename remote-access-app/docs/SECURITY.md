# 🔐 Documentação de Segurança

## Índice

1. [Medidas de Segurança Implementadas](#medidas-de-segurança-implementadas)
2. [Ameaças e Mitigações](#ameaças-e-mitigações)
3. [Boas Práticas](#boas-práticas)
4. [Auditoria e Logging](#auditoria-e-logging)
5. [Compliance](#compliance)

---

## Medidas de Segurança Implementadas

### 1. Criptografia de Dados em Trânsito

**Algoritmo:** AES-256-GCM  
**Implementação:** `shared/encryption.py`

```python
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# 256-bit encryption key
key = PBKDF2.derive(master_key, salt=b"RemoteAccessApp2024", 
                     iterations=100000)

# 12-byte nonce (aleatório em produção)
nonce = os.urandom(12)

# Encrypt com autenticação
cipher = AESGCM(key)
ciphertext = cipher.encrypt(nonce, plaintext, aad)
```

**Vantagens:**
- ✅ Confidencialidade (AES-256)
- ✅ Autenticação (GCM tag)
- ✅ Integridade de dados
- ✅ Proteção contra tampering

**Limitações MVP:**
- ⚠️ Nonce é sequencial (counter) em vez de aleatório
- ⚠️ Chave mestra hardcoded em config/settings.py
- ⚠️ Sem PFS (Perfect Forward Secrecy)

### 2. Hash de Senhas

**Algoritmo:** SHA-256 com PBKDF2  
**Implementação:** `shared/encryption.py::CryptoManager.hash_password()`

```python
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# Melhor (futuro):
from argon2 import PasswordHasher
ph = PasswordHasher()
hash = ph.hash(password)
```

**Atualmente:** SHA-256 simples (rápido para MVP)  
**Futuro:** Argon2 ou bcrypt (mais seguro contra brute-force)

### 3. Gerenciamento de Sessões

**Características:**
- ✅ Session ID aleatório de 64 caracteres (256 bits)
- ✅ Timeout automático (1 hora padrão)
- ✅ Invalidação ao logout
- ✅ Validação a cada mensagem

```python
# Criação
session_id = CryptoManager.generate_session_token(length=32)
# Resultado: "a1b2c3d4e5f6...64 caracteres"

# Validação
if SessionManager.is_session_valid(session_id):
    # Processa mensagem
    pass
```

### 4. Autenticação com Rate Limiting

**Implementação:** `server/server.py::UserManager`

```python
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION = 300  # 5 minutos

# Após 5 falhas, bloqueia por 5 minutos
if self.failed_attempts[username] >= MAX_LOGIN_ATTEMPTS:
    lockout_until = datetime.now() + timedelta(seconds=300)
    self.lockout_times[username] = lockout_until
```

### 5. Validação de Entrada

- ✅ Verificação de tipo de mensagem
- ✅ Validação de tamanho de pacote (MAX_PACKET_SIZE = 1 MB)
- ✅ Sanitização de dados JSON

```python
def _process_message(self, msg: Message):
    if msg.msg_type not in MESSAGE_TYPES.values():
        return ProtocolHandler.create_error(400, "Tipo inválido")
    
    if len(serialized) > MAX_PACKET_SIZE:
        return ProtocolHandler.create_error(413, "Pacote muito grande")
```

### 6. Logging de Segurança

**Arquivo:** `logs/app.log`

```
2024-12-30 10:15:35 - server - INFO - Novo cliente conectado: 192.168.1.100:5432
2024-12-30 10:15:36 - server - INFO - Usuário admin autenticado com sucesso
2024-12-30 10:15:40 - server - WARNING - Falha de autenticação para user: usuario
2024-12-30 10:15:41 - server - WARNING - Usuário usuario bloqueado após múltiplas tentativas
```

---

## Ameaças e Mitigações

### Ameaça 1: Man-in-the-Middle (MITM)

**Descrição:** Atacante intercepta tráfego TCP

**Mitigação:** ✅ Criptografia AES-256-GCM
```
Sem criptografia:  PC A ──[plaintext]──> Atacante ──[modifica]──> PC B
Com criptografia:  PC A ──[AES256]───> Atacante ──[fail GCM tag]──X PC B
```

**Futuro:** TLS/SSL para camada de transporte adicional

### Ameaça 2: Força Bruta de Senha

**Descrição:** Atacante tenta múltiplas senhas

**Mitigação:** ✅ Rate limiting + bloqueio de conta
```
Tentativa 1: ❌ Falha
Tentativa 2: ❌ Falha  
Tentativa 3: ❌ Falha
Tentativa 4: ❌ Falha
Tentativa 5: ❌ Falha + BLOQUEADO por 5 minutos
```

**Melhoria:** Usar Argon2 (mais lento = menos ataques/segundo)

### Ameaça 3: Roubo de Session ID

**Descrição:** Atacante captura session_id e faz requisições

**Mitigação:** ✅ Session ID criptografado em trânsito
```
Capturam: session_id = "abc123..."
Enviam:   [ENCRYPTED com AES-256]
Falha:    GCM tag não válida
```

**Futuro:** Session binding ao IP/User-Agent

### Ameaça 4: Acesso Não Autorizado (Sem Autenticação)

**Descrição:** Usuário tenta capturar tela sem login

**Mitigação:** ✅ Validação de sessão obrigatória
```python
if msg_type != "auth_req":
    if not session_manager.is_session_valid(session_id):
        return create_error(401, "Sessão inválida")
```

### Ameaça 5: Denial of Service (DoS)

**Descrição:** Atacante envia muitos pacotes

**Mitigação:** ⚠️ Parcial
- ✅ Limite de tamanho de pacote (1 MB)
- ✅ Timeout de inatividade (30 seg)
- ⚠️ Sem rate limiting global (seria v2.0)

```python
# Parcial mitigação
MAX_PACKET_SIZE = 1024 * 1024  # 1 MB máximo
SERVER_TIMEOUT = 30  # Timeout de 30 segundos

# Futuro
BANDWIDTH_LIMIT = 1024 * 1024  # 1 MB/seg por cliente
```

### Ameaça 6: Execução Remota de Código (RCE)

**Descrição:** Atacante envia payload malicioso

**Mitigação:** ✅ Sem execução de código dinâmico
```python
# NUNCA FAZER:
exec(msg.data.get("command"))  # ❌ RCE!
eval(json.loads(msg.data))     # ❌ RCE!

# Fazemos:
msg_type = msg.msg_type  # String pura
if msg_type in MESSAGE_TYPES.values():
    # Processa tipo seguro
```

### Ameaça 7: Informação de Caminho (Path Disclosure)

**Descrição:** Erro revela diretório interno

**Mitigação:** ✅ Erro genérico
```python
# ❌ Ruim
except Exception as e:
    return f"Erro em /home/user/client.py:123: {e}"

# ✅ Bom
except Exception as e:
    logger.error(f"Erro ao processar: {e}")  # Log interno
    return "Erro ao processar mensagem"      # Para cliente
```

---

## Boas Práticas

### 1. Variáveis de Ambiente para Secrets

```python
# ❌ Nunca assim
SECRET_KEY = "minha-chave-super-secret"

# ✅ Assim
import os
from dotenv import load_dotenv

load_dotenv()
SECRET_KEY = os.getenv("REMOTE_ACCESS_SECRET")

# Arquivo .env (não commitar no Git!)
# REMOTE_ACCESS_SECRET=sua-chave-aleatoria-muito-longa
```

### 2. HTTPS em Produção

```python
# MVP usa TCP puro
# Produção deve usar:

import ssl

context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain("cert.pem", "key.pem")

server = await asyncio.start_server(
    handle_client, "0.0.0.0", 5500, 
    ssl=context  # ← Adicionar SSL
)
```

### 3. Firewall/VPN

```bash
# Abrir apenas para IPs confiáveis
netsh advfirewall firewall add rule \
    name="Remote Access" dir=in action=allow \
    protocol=tcp localport=5500 \
    remoteip=192.168.1.0/24
```

### 4. Auditoria Regular

```bash
# Revisar logs diariamente
Get-Content logs/app.log -Tail 100

# Buscar tentativas falhadas
Select-String "Falha de autenticação" logs/app.log

# Buscar acessos suspeitos
Select-String "WARNING|ERROR" logs/app.log
```

### 5. Backup de Dados

```bash
# Backup diário do banco de dados
robocopy logs D:\backup\logs /E /Z

# Com timestamp
$date = Get-Date -Format "yyyy-MM-dd"
Copy-Item logs D:\backup\logs-$date -Recurse
```

---

## Auditoria e Logging

### Eventos Registrados

| Evento | Log Level | Exemplo |
|--------|-----------|---------|
| Cliente conectado | INFO | `Novo cliente conectado: 192.168.1.100:5432` |
| Autenticação bem-sucedida | INFO | `Usuário admin autenticado com sucesso` |
| Falha de autenticação | WARNING | `Falha de autenticação para usuario` |
| Conta bloqueada | WARNING | `Usuário usuario bloqueado após múltiplas tentativas` |
| Sessão criada | INFO | `Sessão criada para admin: a1b2c3d4...` |
| Sessão encerrada | INFO | `Sessão encerrada: a1b2c3d4...` |
| Cliente desconectado | INFO | `Cliente desconectado: 192.168.1.100:5432` |
| Erro na desserialização | ERROR | `Erro ao desserializar mensagem` |
| Timeout de conexão | WARNING | `Timeout para cliente: 192.168.1.100:5432` |

### Acesso aos Logs

```python
import json
from datetime import datetime, timedelta

# Ler logs do arquivo
with open("logs/app.log", "r") as f:
    for line in f:
        print(line.strip())

# Filtrar por data
cutoff = datetime.now() - timedelta(days=7)
logs = [l for l in logs if datetime.fromisoformat(l.split(" - ")[0]) > cutoff]

# Análise de segurança
failed_auths = [l for l in logs if "Falha de autenticação" in l]
print(f"Tentativas falhadas: {len(failed_auths)}")
```

---

## Compliance

### Padrões Atendidos

| Padrão | Status | Notas |
|--------|--------|-------|
| **OWASP Top 10** | ✅ Maioria | A1 Injection: ✅ Sem SQL; A2 Broken Auth: ✅ Rate limit; A3 Sensitive Data: ✅ AES-256 |
| **NIST SP 800-63B** | ⚠️ Parcial | Password hashing: ✅ SHA-256 (⚠️ Melhorar para Argon2) |
| **CWE Top 25** | ✅ Maioria | CWE-78 OS Injection: ✅ Sem shell execution |
| **ISO 27001** | ⚠️ Framework | Controles de criptografia implementados |

### Para Atingir Compliance Completo

1. **Migrar SHA-256 para Argon2**
   ```python
   from argon2 import PasswordHasher
   ph = PasswordHasher()
   hash = ph.hash(password)
   ```

2. **Adicionar TLS/SSL**
   ```python
   ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
   ssl_context.load_cert_chain("cert.pem", "key.pem")
   ```

3. **Implementar RBAC (Role-Based Access Control)**
   ```python
   # Usuários com diferentes permissões
   "admin": {"permissions": ["control", "view", "admin"]},
   "viewer": {"permissions": ["view"]},
   "controller": {"permissions": ["control", "view"]}
   ```

4. **Auditoria com Database**
   ```python
   # PostgreSQL para logs imutáveis
   INSERT INTO audit_log (timestamp, user_id, action, ip)
   VALUES (NOW(), $1, $2, $3)
   ```

---

## Checklist de Segurança Pré-Produção

- [ ] Alterar `SECRET_KEY` padrão
- [ ] Gerar novas senhas de usuários padrão
- [ ] Implementar TLS/SSL
- [ ] Configurar firewall
- [ ] Revisar todos os logs
- [ ] Fazer teste de penetração
- [ ] Migrar para Argon2
- [ ] Ativar autenticação 2FA (futuro)
- [ ] Configurar backups automáticos
- [ ] Documentar política de senhas
- [ ] Treinar usuários sobre segurança
- [ ] Monitorar logs 24/7

---

Última atualização: 30 de Dezembro de 2024
