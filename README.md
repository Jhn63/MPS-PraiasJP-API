# 🏖️ Praias JP - Sistema de Monitoramento de Praias

Um sistema inteligente de monitoramento de qualidade de água em praias de João Pessoa, Paraíba. Implementado com FastAPI, SQLAlchemy, e diversos padrões de projeto GoF.

---

## 1. Purpose of the Project

**Objetivo Principal:** Monitorar continuamente o nível do mar e a qualidade da água (baneabilidade) nas principales praias de João Pessoa.

**Funcionalidades Principais:**
- ✅ Autenticação segura com suporte a múltiplas estratégias (API Key, JWT)
- ✅ Monitoramento automático de 7 praias de João Pessoa
- ✅ Rastreamento de níveis de maré e status de baneabilidade (PRÓPRIO/IMPRÓPRIO)
- ✅ API REST para consulta de dados e gestão de estações
- ✅ Sistema de permissões com verificação de tokens
- ✅ Histórico de sincronização com padrão Memento
- ✅ Gerenciamento automático de estados de sincronização

**Praias Monitoradas:**
1. Praia de Tambaú (PRÓPRIO)
2. Praia do Bessa (IMPRÓPRIO)
3. Praia de Manaíra (PRÓPRIO)
4. Praia de Cabo Branco (PRÓPRIO)
5. Praia de Jaguaribe (IMPRÓPRIO)
6. Praia de Intermares (PRÓPRIO)
7. Praia de Jacaré (IMPRÓPRIO)

---

## 2. Installation & Running

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Installation Steps

```bash
# 1. Clone or download the project
cd mps-praiasjp

# 2. Create and activate a virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1   # Windows
source venv/bin/activate       # Linux/Mac

# 3. Install dependencies
pip install -r requirements.txt

# 4. Navigate to app source directory
cd app/src
```

### Running the Application

**Option 1: Direct Python Execution**
```bash
python main.py
```
The app will start without the web server (useful for background monitoring).

**Option 2: FastAPI with Uvicorn (Recommended)**
```bash
..\..\venv\Scripts\python.exe -m uvicorn main:app --host localhost --port 8000 --reload
```

**Option 3: Using Gunicorn (Production)**
```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000
```

### Application Startup Process
1. ✅ Tables created (EstacaoMonitoramento, User)
2. ✅ Database seeded with 7 beaches via Alembic migrations
3. ✅ Error logger initialized
4. ✅ Middleware registered
5. ✅ Monitoring loop started (runs every 3 hours - 10800 seconds)

The app will output:
```
[Migrations] ✓ Alembic migrations completed successfully
[Agendador] Iniciando loop automático de monitoramento a cada 10800 segundos...
INFO:     Uvicorn running on http://localhost:8000
```

---

## 3. Testing & Sending Requests

### 3.1 Authentication First - Register a User

**Endpoint:** `POST /users/`

```bash
curl -X POST "http://localhost:8000/users/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "usuario_teste",
    "password": "Senha@123"
  }' \
  -G --data-urlencode "auth_type=API_KEY"
```

**Response:**
```json
{
  "message": "Usuário criado com sucesso",
  "username": "usuario_teste",
  "access_token": "api_key_xyz12345",
  "auth_type": "API_KEY"
}
```

### 3.2 Login to Get Token

**Endpoint:** `POST /login/`

```bash
curl -X POST "http://localhost:8000/login/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "usuario_teste",
    "password": "Senha@123"
  }' \
  -G --data-urlencode "auth_type=API_KEY"
```

**Response:**
```json
{
  "message": "Login realizado com sucesso",
  "username": "usuario_teste",
  "access_token": "api_key_xyz12345",
  "auth_type": "API_KEY"
}
```

### 3.3 Query Beaches by Name

**Endpoint:** `GET /estacoes/nome/{nome}`

```bash
curl -X GET "http://localhost:8000/estacoes/nome/Tambaú" \
  -H "x-token: api_key_xyz12345"
```

### 3.4 Query Beaches by Location

**Endpoint:** `GET /estacoes/localizacao/{localizacao}`

```bash
curl -X GET "http://localhost:8000/estacoes/localizacao/Tambaú" \
  -H "x-token: api_key_xyz12345"
```

### 3.5 Query Beaches by Status

**Endpoint:** `GET /estacoes/status/{status}`

```bash
curl -X GET "http://localhost:8000/estacoes/status/ATUALIZADO" \
  -H "x-token: api_key_xyz12345"
```

### 3.6 Query Beaches by Baneabilidade (NEW!)

**Endpoint:** `GET /estacoes/baneabilidade/{baneabilidade}`

```bash
# Get all PRÓPRIO beaches
curl -X GET "http://localhost:8000/estacoes/baneabilidade/PROPRIO" \
  -H "x-token: api_key_xyz12345"

# Get all IMPRÓPRIO beaches
curl -X GET "http://localhost:8000/estacoes/baneabilidade/IMPROPRIO" \
  -H "x-token: api_key_xyz12345"
```

### 3.7 Using Postman/Thunder Client

For easier testing, create requests with:
- **Header:** `x-token: <your_access_token>`
- **Query Parameter:** `auth_type=API_KEY` (for user creation/login)

---

## 4. GoF Design Patterns Implementation

### 4.1 Strategy Pattern
**Module:** `app/src/modules/auth/auth_strategy.py`  
**Purpose:** Support multiple authentication methods flexibly

- Allows different authentication strategies (API_KEY, JWT) to be swapped at runtime
- Each strategy implements `gerar_chave()` method with its own logic
- Used in login and token generation

### 4.2 Factory Method Pattern
**Module:** `app/src/modules/auth/auth_factory.py`  
**Purpose:** Create appropriate authentication strategy based on type

- `AuthFactory.get_strategy(auth_type)` returns the correct strategy instance
- Centralizes object creation logic
- Simplifies adding new authentication methods
- Returns concrete strategy (ApiKeyStrategy or JWTStrategy) based on parameter

---

### 4.4 Abstract Factory Pattern
**Module:** `app/src/modules/logger/error_logger.py`  
**Purpose:** Create families of related log observers and formatters together

- `LogObserverFactory` creates complete logging configurations (observer + formatter pairs)
- **Abstract Products:**
  - `LogObserver` interface (implemented by FileLogObserver, ConsoleLogObserver, RotatingFileLogObserver)
  - `LogFormatter` interface (implemented by TextFormatter, JSONFormatter, CompactFormatter)
- **Concrete Factory Methods:**
  - `create_file_observer()` - Creates FileLogObserver with chosen formatter
  - `create_rotating_file_observer()` - Creates RotatingFileLogObserver with rotation settings
  - `create_console_observer()` - Creates ConsoleLogObserver with console-specific formatting
- Ensures consistent observer + formatter combinations
- Easy to add new output types (e.g., DatabaseLogObserver)

**Usage Example:**
```python
file_observer = LogObserverFactory.create_file_observer(
    file_path="logs/errors.log",
    format_type="json",
    min_level=LogLevel.ERROR
)

console_observer = LogObserverFactory.create_console_observer(
    format_type="compact",
    min_level=LogLevel.WARNING
)

error_logger.attach(file_observer)
error_logger.attach(console_observer)
```

---

### 4.5 Chain of Responsibility Pattern
**Camada:** Middleware (Intermediário entre View e Controller)  
**Padrões Aplicados:** Chain of Responsibility, Composite

Interceptador de requisições que garante que apenas usuários devidamente autenticados e autorizados acessem recursos protegidos.

* **Descrição:** Para cada requisição feita à API, o middleware executa uma série de validações sequenciais.
* **Aplicação dos Padrões:**
  * O **Chain of Responsibility** divide a validação em etapas independentes e encadeadas (ex: Etapa 1: Verifica a validade da chave de acesso -> Etapa 2: Verifica o nível de permissão do usuário).
  * O **Composite** é utilizado para modelar a estrutura de permissões do sistema (RBAC - *Role-Based Access Control*), tratando permissões individuais (folhas) e grupos de permissões/cargos (nós compostos) de forma uniforme durante a verificação de acesso.

### 4.6 Composite Pattern
**Module:** `app/src/middlewares/permissoes_composite.py`  
**Purpose:** Treat individual and group permissions uniformly

- Composite permissions (roles) can contain individual permissions
- RBAC (Role-Based Access Control) implementation
- Tree-like structure for flexible permission management

### 4.7 Facade Pattern
**Module:** `app/src/service/facade.py` (FacadeSingletonController)  
**Purpose:** Simplify complex subsystem interactions

- Hides business logic complexity from routes
- Single entry point for operations:
  - `obterEstacaoPorNome()` - Get beach by name
  - `obterEstacaoPorLocalizacao()` - Get beach by location
  - `listarEstacoesPorStatus()` - List beaches by status
  - `listarEstacoesPorBaneabilidade()` - List beaches by water quality
  - `gerarAcessoUsuario()` - Create user with token
  - `realizarLogin()` - Authenticate user

### 4.8 Singleton Pattern
**Module:** `app/src/service/facade.py` (FacadeSingletonController) & `app/src/modules/logger/error_logger.py` (ErrorLogger)  
**Purpose:** Ensure single instance of key components across application

**Facade Singleton:**
- `FacadeSingletonController.get_instance()` returns unique instance
- Optimizes resource usage
- Consistent state across all operations

**Logger Singleton:**
- `ErrorLogger` uses metaclass-based Singleton implementation
- Thread-safe instance creation
- Global `error_logger` instance for application-wide use

### 4.9 Memento Pattern
**Module:** `app/src/modules/monitoring/memento.py`  
**Purpose:** Save and restore object states without breaking encapsulation

- `Memento` class stores beach state snapshots
- `Caretaker` class manages history of snapshots
- Used to track historical changes in beach monitoring
- Supports rollback and audit trails

### 4.10 State Pattern
**Module:** `app/src/modules/monitoring/state_manager.py`  
**Purpose:** Alter object behavior based on internal state

- Beach states: `ATUALIZADO`, `DESATUALIZADO`, `EM_SINCRONIZACAO`
- State transitions managed automatically
- Different behaviors for each state
- Prevents invalid state transitions

### 4.11 Observer Pattern
**Module:** `app/src/modules/logger/error_logger.py`  
**Purpose:** Notify multiple observers when events occur

- Multiple observers (File, Console, Rotating File) listen to logging events
- Decouples logger from output destinations
- Easy to add new output formats
- Automatic error propagation across system
- Thread-safe observer management with lock support

### 4.12 Template Method Pattern
**Module:** `app/src/modules/providers/commands.py`  
**Purpose:** Define reusable algorithm skeleton for external API requests

- `BaseCommand` abstract class defines the template: `connect()` → `fetch()` → `parse()`
- Subclasses implement specific hooks for different external APIs
- Concrete example: `TabuaMareCabedeloCommand` fetches tide tables from weather API
- Guarantees proper resource management (connection open/close with try/finally)
- Easy to add new providers by extending `BaseCommand`
- Follows DRY principle - common HTTP logic in base class, API-specific logic in subclasses

**Example Flow:**
```
execute() [final - controls flow]
  ├── connect()    → Opens HttpReceiver connection
  ├── fetch()      → Makes HTTP GET request to tide API
  └── parse()      → Extracts hours data from nested JSON response
```

### 4.13 Command Pattern
**Module:** `app/src/modules/providers/` (invoker.py, commands.py, concrete_commands.py)  
**Purpose:** Encapsulate requests as objects for deferred/dynamic execution

- `CommandProtocol` - Interface that all commands must implement
- `Invoker` class - Manages and executes registered commands by key
- `BaseCommand` - Abstract base implementing both Template Method and Command patterns
- Concrete implementations - `TabuaMareCabedeloCommand` and others
- Benefits:
  - Commands decoupled from execution logic
  - Dynamic command registration/unregistration at runtime
  - Can queue, log, undo commands easily
  - Supports batch execution with `execute_all()`

**Usage Example:**
```python
invoker = Invoker()
invoker.register("tide_table", TabuaMareCabedeloCommand())

# Execute single command
result = await invoker.execute("tide_table")

# Execute all registered commands
results = await invoker.execute_all()
```

**Error Handling:**
- Individual command failures don't break execution of other commands
- Errors captured and returned in results dict for batch operations

### 4.14 Adapter & Bridge Patterns (Future)
**Planned for:** Enhanced external API integrations
- Adapter: Convert external API formats to internal models
- Bridge: Decouple API calls from implementation details

---

## 5. What Was Missing & Improvements Needed

### 5.1 Issues Fixed (Recent Updates)
✅ **Database URL Path Resolution**
- Fixed: Relative paths causing Alembic migration failures
- Solution: Converted to absolute paths in `database/db.py`

✅ **Automatic Database Seeding**
- Fixed: Alembic migrations now properly seed 7 beaches on startup
- Solution: Synced Alembic config with app's DATABASE_URL in `migrations.py`

✅ **Baneabilidade Filtering**
- Added: New route `GET /estacoes/baneabilidade/{baneabilidade}`
- Allows filtering beaches by water quality status

### 5.2 Current Limitations & Improvements Needed

#### Security
- ⚠️ **Passwords stored in plaintext** → Should use bcrypt hashing
- ⚠️ **No role-based access control implemented** → Composite pattern prepared but not used
- ⚠️ **No token expiration** → Add TTL to tokens
- ⚠️ **No rate limiting** → Protect against brute force attacks

#### Data Validation
- ⚠️ **Minimal input validation** → Add stricter verification
- ⚠️ **No pagination** → Implement for large result sets
- ⚠️ **No filtering/sorting options** → Improve query flexibility

#### Testing
- ⚠️ **No unit tests** → Add pytest test suite
- ⚠️ **No integration tests** → Test full workflows
- ⚠️ **No load testing** → Verify performance under stress

#### Monitoring
- ⚠️ **Limited error recovery** → Add retry mechanisms
- ⚠️ **No alerting system** → Notify when beaches become unsafe
- ⚠️ **No database backups** → Implement backup strategy
- ⚠️ **No metrics/analytics** → Add Prometheus/Grafana integration

#### Documentation
- ⚠️ **No API documentation** → Add Swagger/OpenAPI specs
- ⚠️ **No deployment guide** → Docker, CI/CD setup needed
- ⚠️ **No database schema docs** → Add ERD diagrams

#### Architecture
- ⚠️ **Monolithic design** → Could benefit from microservices
- ⚠️ **Synchronous processing** → Add async tasks (Celery)
- ⚠️ **No caching layer** → Redis for frequently accessed data
- ⚠️ **No event streaming** → Kafka/RabbitMQ for real-time updates

#### Performance
- ⚠️ **No database indexing strategy documented** → Optimize queries
- ⚠️ **All beaches polled serially** → Parallelize monitoring with asyncio
- ⚠️ **No query optimization** → Add proper JOIN queries where needed

### 5.3 High-Priority Improvements (Next Iteration)
1. **Security:** Implement password hashing with bcrypt
2. **Testing:** Create comprehensive test suite (unit + integration)
3. **Validation:** Add stricter input/output validation
4. **Performance:** Parallelize beach monitoring with asyncio
5. **Monitoring:** Add alert system for unsafe water conditions

### 5.4 Nice-to-Have Features
- Real-time webhook notifications
- Mobile app companion
- Water quality prediction ML model
- Historical data visualization dashboard
- Multi-language support (EN, PT)

---

## Project Structure

```
mps-praiasjp/
├── app/
│   ├── src/
│   │   ├── main.py                    # FastAPI entry point
│   │   ├── database/
│   │   │   ├── db.py                  # SQLAlchemy configuration
│   │   │   ├── migrations.py          # Alembic migration runner
│   │   │   └── base.db                # SQLite database
│   │   ├── models/
│   │   │   └── estacao_model.py       # Beach monitoring station model
│   │   ├── routes/
│   │   │   └── routes.py              # API endpoints
│   │   ├── service/
│   │   │   └── facade.py              # Facade + Singleton pattern
│   │   ├── schemas/
│   │   │   └── estacao.py             # Pydantic schemas
│   │   ├── modules/
│   │   │   ├── auth/                  # Strategy + Factory Method patterns
│   │   │   ├── users/                 # User management
│   │   │   ├── monitoring/            # State + Memento patterns
│   │   │   ├── logger/                # Observer + Abstract Factory patterns
│   │   │   │   ├── error_logger.py    # LogObserverFactory + ErrorLogger (Singleton)
│   │   │   │   └── logger_service.py  # Middleware integration
│   │   │   └── providers/             # Command + Template Method patterns
│   │   │       ├── invoker.py         # Command invoker
│   │   │       ├── commands.py        # BaseCommand + CommandProtocol
│   │   │       ├── concrete_commands.py # Concrete command implementations
│   │   │       └── service.py         # Provider service orchestrator
│   │   ├── middlewares/
│   │   │   ├── auth_chain.py          # Chain of Responsibility
│   │   │   └── permissoes_composite.py # Composite pattern
│   │   └── exceptions/
│   │       └── domain_exceptions.py   # Custom exceptions
│   ├── alembic/
│   │   ├── env.py                     # Alembic configuration
│   │   └── versions/
│   │       └── 001_seed_estacoes.py   # Beach seeding migration
│   └── alembic.ini                    # Alembic settings
└── requirements.txt                    # Python dependencies
```

---

## Contributing

To contribute to this project:
1. Create a new feature branch
2. Make your changes following the established patterns
3. Test thoroughly
4. Submit a pull request

---

## License

This project is part of the Academic Curriculum at UFPB (Universidade Federal da Paraíba).

---

## Contact & Support

For issues or questions, contact the development team or open an issue on the repository.