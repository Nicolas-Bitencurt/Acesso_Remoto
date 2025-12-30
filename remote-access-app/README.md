# 🖥️ Remote Access App - Acesso Remoto para Windows

Uma aplicação profissional e segura de acesso remoto de desktop para Windows, desenvolvida em Python com arquitetura cliente-servidor robusta.

**Versão:** 1.0.0  
**Status:** MVP (Produto Mínimo Viável)  
**Última atualização:** Dezembro 2024

---

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Arquitetura](#arquitetura)
3. [Recursos](#recursos)
4. [Requisitos](#requisitos)
5. [Instalação](#instalação)
6. [Configuração](#configuração)
7. [Uso](#uso)
8. [Estrutura do Projeto](#estrutura-do-projeto)
9. [Segurança](#segurança)
10. [Troubleshooting](#troubleshooting)
11. [Desenvolvimento](#desenvolvimento)
12. [Roadmap](#roadmap)
13. [Licença](#licença)

---

## 🎯 Visão Geral

**Remote Access App** é uma solução completa de acesso remoto que permite:

✅ **Capturar e transmitir tela** em tempo real  
✅ **Controlar mouse e teclado** remotamente  
✅ **Autenticação segura** com criptografia AES-256  
✅ **Gerenciamento de sessões** robusto  
✅ **Logging detalhado** de todas as ações  
✅ **Escalável** para múltiplas conexões simultâneas  

### Comparação com Concorrentes

| Recurso | Remote Access | TeamViewer | AnyDesk | Chrome RDP |
|---------|---------------|-----------|---------|-----------|
| Open Source | ✅ | ❌ | ❌ | ✅ |
| Criptografia E2E | ✅ | ✅ | ✅ | ✅ |
| Sem Dependência Cloud | ✅ | ❌ | ❌ | ⚠️ |
| Compressão Diferencial | ⏳ | ✅ | ✅ | ✅ |
| P2P Direto | ⏳ | ✅ | ✅ | ❌ |
| Transferência Arquivos | ⏳ | ✅ | ✅ | ❌ |

---

## 🏗️ Arquitetura

```
┌─────────────────┐          ┌──────────────────┐          ┌─────────────────┐
│  PC A (Cliente) │          │  Servidor Broker │          │  PC B (Cliente) │
│                 │          │                  │          │                 │
│ ┌─────────────┐ │          │ ┌──────────────┐ │          │ ┌─────────────┐ │
│ │ Captura Tela│ │          │ │ Autenticação │ │          │ │ Captura Tela│ │
│ │ Mouse/Teclado  │ ──TCP──> │ │ Roteamento   │ <──TCP── │ │ Mouse/Teclado  │
│ │ Criptografia│ │          │ │ Sessões      │ │          │ │ Criptografia│ │
│ └─────────────┘ │          │ │ Compressão   │ │          │ └─────────────┘ │
└─────────────────┘          │ └──────────────┘ │          └─────────────────┘
                              │  Porta: 5500    │
                              │  Logs: /logs    │
                              │  Users: JSON    │
                              └──────────────────┘
```

### 3 Componentes Principais

#### 1️⃣ **Cliente (client.py)**
- Captura tela usando `mss` e `Pillow`
- Comprime imagens em JPEG
- Envia/recebe eventos de mouse e teclado
- Comunica via TCP/IP

#### 2️⃣ **Servidor (server.py)**
- Autentica usuários
- Gerencia sessões
- Roteia mensagens entre clientes
- Suporta múltiplas conexões assíncronas

#### 3️⃣ **Protocolo (shared/protocol.py)**
- Serialização de mensagens
- Compressão de imagens
- Criptografia AES-256-GCM
- Sincronização de eventos

---

## ✨ Recursos

### Versão 1.0 (MVP - Atual)

- ✅ Autenticação com usuário/senha
- ✅ Captura de tela em tempo real (15 FPS)
- ✅ Envio de imagem comprimida (JPEG 80%)
- ✅ Criptografia AES-256-GCM
- ✅ Gerenciamento robusto de sessões
- ✅ Logging detalhado
- ✅ Timeout automático
- ✅ Bloqueio de conta após falhas
- ✅ Suporte para múltiplas conexões

### Versão 2.0 (Roadmap)

- 🔄 Interface gráfica com PyQt5
- 🔄 Compressão diferencial (enviar só mudanças)
- 🔄 Redimensionamento automático de tela
- 🔄 Transmissão de áudio
- 🔄 Transferência de arquivos
- 🔄 Clipboard compartilhado

### Versão 3.0 (Futuro)

- 🔜 P2P direto (NAT traversal)
- 🔜 Suporte mobile
- 🔜 WebRTC para browser
- 🔜 Banco de dados relacional
- 🔜 Dashboard web

---

## 📦 Requisitos

### Sistema
- **Windows 7 ou superior** (testado em Win 10/11)
- **Python 3.9+**
- **Mínimo 2 GB de RAM**
- **Conexão de rede estável**

### Dependências Python
Ver [requirements.txt](requirements.txt)

---

## 🚀 Instalação

### 1. Clone ou Extraia o Projeto

```bash
cd remote-access-app
```

### 2. Crie um Ambiente Virtual

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Ou com conda
conda create -n remote_access python=3.9
conda activate remote_access
```

### 3. Instale Dependências

```bash
pip install -r requirements.txt
```

### 4. Verifique a Instalação

```bash
python -c "import mss; import cryptography; print('✅ Dependências OK!')"
```

---

## ⚙️ Configuração

### Arquivo Principal: `config/settings.py`

```python
# ===== SERVIDOR =====
SERVER_HOST = "0.0.0.0"           # Escuta em todas as interfaces
SERVER_PORT = 5500                # Porta de comunicação

# ===== CLIENTE =====
DEFAULT_SERVER_HOST = "localhost" # Host do servidor
DEFAULT_SERVER_PORT = 5500        # Porta do servidor

# ===== CAPTURA DE TELA =====
SCREEN_CAPTURE_FPS = 15           # 15 quadros por segundo
SCREEN_QUALITY = 80               # 80% de qualidade JPEG

# ===== SEGURANÇA =====
SECRET_KEY = "sua-chave-secreta-super-segura-32-chars!!"
SESSION_TIMEOUT = 3600            # 1 hora
MAX_LOGIN_ATTEMPTS = 5            # 5 tentativas antes de bloquear
LOCKOUT_DURATION = 300            # 5 minutos de bloqueio
```

### Variáveis de Ambiente (Recomendado)

```bash
# Windows (PowerShell)
$env:REMOTE_ACCESS_SECRET = "sua-chave-secreta-super-segura"
$env:REMOTE_ACCESS_HOST = "0.0.0.0"
$env:REMOTE_ACCESS_PORT = "5500"

# Windows (CMD)
set REMOTE_ACCESS_SECRET=sua-chave-secreta-super-segura
set REMOTE_ACCESS_HOST=0.0.0.0
set REMOTE_ACCESS_PORT=5500
```

---

## 💻 Uso

### Iniciar o Servidor

```bash
# Ativa ambiente virtual
venv\Scripts\activate

# Inicia servidor na porta 5500
python server/server.py
```

**Saída esperada:**
```
2024-12-30 10:15:30 - __main__ - INFO - Broker inicializado: 0.0.0.0:5500
2024-12-30 10:15:30 - __main__ - INFO - Servidor iniciado em 0.0.0.0:5500
```

### Iniciar o Cliente

**Em outro terminal/PC:**

```bash
# Ativa ambiente virtual
venv\Scripts\activate

# Inicia cliente (conecta a localhost:5500 por padrão)
python client/client.py
```

**Para conectar a outro servidor:**

```python
# Edite client/client.py
config = ClientConfig(
    server_host="192.168.1.100",  # IP do servidor
    server_port=5500,
    username="admin",
    password="admin123"
)
```

### Saída Esperada

```
2024-12-30 10:15:35 - __main__ - INFO - Cliente inicializado: admin@localhost:5500
2024-12-30 10:15:35 - __main__ - INFO - Conectado ao servidor
2024-12-30 10:15:36 - __main__ - INFO - Mensagem de autenticação enviada
2024-12-30 10:15:36 - __main__ - INFO - Autenticação bem-sucedida. Session ID: a1b2c3d4e5...
2024-12-30 10:15:36 - __main__ - INFO - Iniciando loop de captura de tela
2024-12-30 10:15:36 - __main__ - INFO - Iniciando loop de recepção de eventos
2024-12-30 10:15:37 - __main__ - DEBUG - Tela enviada: 45234 bytes (1920x1080)
```

---

## 📁 Estrutura do Projeto

```
remote-access-app/
│
├── config/
│   ├── __init__.py
│   └── settings.py              # Configurações centralizadas
│
├── server/
│   ├── __init__.py
│   └── server.py                # Servidor intermediário (broker)
│
├── client/
│   ├── __init__.py
│   └── client.py                # Cliente de acesso remoto
│
├── shared/
│   ├── __init__.py
│   ├── encryption.py            # Módulo de criptografia AES-256
│   ├── protocol.py              # Protocolo de comunicação
│   └── screen_capture.py        # Captura de tela
│
├── docs/
│   ├── ARCHITECTURE.md          # Detalhes da arquitetura
│   ├── PROTOCOL.md              # Especificação do protocolo
│   └── SECURITY.md              # Análise de segurança
│
├── logs/
│   ├── app.log                  # Log da aplicação
│   ├── users.json               # Banco de dados de usuários
│   └── sessions.json            # Sessões ativas
│
├── requirements.txt             # Dependências Python
├── README.md                    # Este arquivo
├── LICENSE                      # Licença MIT
└── .gitignore                   # Ignore para Git
```

---

## 🔐 Segurança

### Implementado ✅

| Medida | Descrição |
|--------|-----------|
| **Criptografia AES-256-GCM** | Criptografia de ponta a ponta |
| **Hash SHA-256** | Armazenamento seguro de senhas |
| **Tokens de Sessão** | Geração criptográfica aleatória |
| **Timeout de Sessão** | Expiração após 1 hora |
| **Bloqueio de Conta** | 5 tentativas = bloqueio de 5 min |
| **Logging** | Todas as ações são registradas |
| **Validação de Entrada** | Verificação de dados recebidos |

### Configurações de Segurança

```python
# config/settings.py
ENCRYPTION_ALGORITHM = "AES-256-GCM"  # Padrão de ouro
SECRET_KEY = "sua-chave-aqui"         # ⚠️ MUDAR EM PRODUÇÃO
HASH_ALGORITHM = "sha256"
SESSION_TIMEOUT = 3600                # 1 hora
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION = 300                # 5 minutos
```

### ⚠️ Avisos Importantes

1. **NUNCA** commite `SECRET_KEY` no Git
2. Use HTTPS/TLS em produção
3. Mude as senhas padrão `admin:admin123`
4. Implemente firewall/VPN para acesso remoto
5. Faça backup regular dos arquivos de sessão
6. Revise logs regularmente para atividades suspeitas

### Exemplos de Uso Seguro

```python
# ❌ INSEGURO - Não faça assim!
SECRET_KEY = "admin123"  # Muito fraco
client = RemoteAccessClient(
    server_host="192.168.1.1",
    password="senha123"  # Armazenada em texto plano
)

# ✅ SEGURO - Assim sim!
import os
from dotenv import load_dotenv

load_dotenv()
SECRET_KEY = os.getenv("REMOTE_ACCESS_SECRET")
PASSWORD = os.getenv("USER_PASSWORD")
```

---

## 🐛 Troubleshooting

### Erro: "ModuleNotFoundError: No module named 'mss'"

```bash
pip install --upgrade mss
```

### Erro: "Conexão recusada" (Connection refused)

```bash
# Verifique se servidor está rodando
netstat -ano | findstr :5500

# Se porta está em uso por outro programa
netsh int ipv4 set dynamic tcp start=49152 num=16384
```

### Erro: "Falha na autenticação"

1. Verifique usuário e senha em `config/settings.py`
2. Limpe arquivo `logs/users.json` e reinicie
3. Verifique se conta não está bloqueada

```python
# Para resetar usuários padrão
from shared.encryption import CryptoManager

admin_hash = CryptoManager.hash_password("admin123")
viewer_hash = CryptoManager.hash_password("viewer123")
print(f"Admin: {admin_hash}")
print(f"Viewer: {viewer_hash}")
```

### Erro: "Timeout na recepção de dados"

1. Verifique conexão de rede
2. Aumente `SERVER_TIMEOUT` em `config/settings.py`
3. Verif firewall

```python
SERVER_TIMEOUT = 60  # Aumenta para 60 segundos
```

### Performance Baixa / Alto Uso de CPU

```python
# Reduza FPS e qualidade
SCREEN_CAPTURE_FPS = 10           # De 15 para 10
SCREEN_QUALITY = 60               # De 80 para 60
SCREEN_RESIZE_SCALE = 0.75        # Redimensiona para 75%
```

### Erro: "Acesso negado" ao salvar logs

```bash
# Garanta permissões na pasta logs
icacls "logs" /grant:r "%username%:F" /t
```

---

## 🛠️ Desenvolvimento

### Estrutura de Testes

```bash
# Teste unitário do protocolo
python -m pytest shared/test_protocol.py -v

# Teste de criptografia
python -m pytest shared/test_encryption.py -v

# Teste de captura de tela
python shared/screen_capture.py
```

### Adicionar Novo Tipo de Mensagem

1. **Atualize MESSAGE_TYPES em config/settings.py**
   ```python
   MESSAGE_TYPES = {
       ...
       "MY_NEW_MESSAGE": "my_new_msg",
   }
   ```

2. **Implemente handler em shared/protocol.py**
   ```python
   @staticmethod
   def create_my_new_message(session_id: str, **kwargs) -> Message:
       return Message(
           msg_type=MESSAGE_TYPES["MY_NEW_MESSAGE"],
           session_id=session_id,
           data=kwargs
       )
   ```

3. **Processe em server.py ou client.py**
   ```python
   elif msg_type == "my_new_msg":
       # Sua lógica aqui
       pass
   ```

### Debug Mode

```python
# config/settings.py
DEBUG = True
VERBOSE = True
LOG_LEVEL = "DEBUG"
```

### Profiling de Performance

```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Seu código aqui
client.run()

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)
```

---

## 📊 Roadmap

### Q1 2025

- [ ] Interface GUI com PyQt5
- [ ] Suporte a múltiplos monitores
- [ ] Detector de mudanças (delta encoding)
- [ ] Testes automatizados completos

### Q2 2025

- [ ] Transmissão de áudio
- [ ] Transferência de arquivos
- [ ] Chat em tempo real
- [ ] Gerenciador de permissões

### Q3 2025

- [ ] Suporte P2P (NAT traversal com STUN/TURN)
- [ ] Banco de dados PostgreSQL
- [ ] API REST para integração

### Q4 2025

- [ ] Cliente web (HTML5/WebRTC)
- [ ] Suporte mobile (Android/iOS)
- [ ] Dashboard administrativo
- [ ] Relatórios de segurança

---

## 📝 Exemplo de Fluxo Completo

### Cenário: PC A controla PC B

```
PASSO 1: Iniciar Servidor
┌─────────────────────────────┐
│ python server/server.py      │
│ Porta: 5500                  │
│ Status: Aguardando clientes  │
└─────────────────────────────┘

PASSO 2: Conectar PC A (Cliente 1)
┌─────────────────────────────┐
│ python client/client.py      │
│ Conecta a localhost:5500     │
│ Autentica com: admin/admin123
│ Session ID: abc123...        │
│ Status: Enviando tela        │
└─────────────────────────────┘

PASSO 3: Conectar PC B (Cliente 2)
┌─────────────────────────────┐
│ python client/client.py      │
│ Conecta a localhost:5500     │
│ Autentica com: viewer/viewer123
│ Session ID: def456...        │
│ Status: Aguardando eventos   │
└─────────────────────────────┘

PASSO 4: Transmissão de Dados
PC A ──[Tela em JPEG 45KB]──> Servidor ──[Redireciona]──> PC B
PC B ──[Clique Mouse (50B)]──> Servidor ──[Redireciona]──> PC A
PC A ──[Tecla Digitada (30B)]> Servidor ──[Redireciona]──> PC B

PASSO 5: Monitoramento
Servidor registra:
- [10:15:36] PC A autenticado (admin@PC-A)
- [10:15:37] PC B autenticado (viewer@PC-B)
- [10:15:38] Transmissão de tela iniciada
- [10:15:40] 45 KB tela enviada (15ms)
- [10:15:41] Evento mouse recebido
- [10:16:00] Ping recebido de PC A
```

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Para contribuir:

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

### Padrões de Código

- PEP 8 para formatação
- Type hints em todas as funções
- Docstrings em formato Google
- 100% coverage de testes para código crítico

---

## 📄 Licença

Este projeto está licenciado sob a MIT License - veja [LICENSE](LICENSE) para detalhes.

---

## 👥 Autores

- **Nicolas Bitencourt** - Desenvolvedor Principal
- Contribuidores são bem-vindos!

---

## 📞 Suporte

- **Issues**: [GitHub Issues](https://github.com/seu-usuario/remote-access-app/issues)
- **Email**: seu-email@exemplo.com
- **Discord**: [Link do servidor]

---

## 🙏 Agradecimentos

- `mss` - Screenshot library
- `cryptography` - Criptografia
- `Pillow` - Processamento de imagens
- Comunidade Python

---

## 📚 Documentação Adicional

Veja a pasta `docs/` para documentação detalhada:

- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - Detalhes técnicos
- [PROTOCOL.md](docs/PROTOCOL.md) - Especificação do protocolo
- [SECURITY.md](docs/SECURITY.md) - Análise de segurança
- [API.md](docs/API.md) - Referência da API
- [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) - Dicas avançadas

---

**Última atualização: 30 de Dezembro de 2024**

⭐ Se você gostou do projeto, considere deixar uma estrela!
