# Mapeamento de Padrões GoF por Funcionalidade

Este documento descreve as principais *features* do sistema, suas responsabilidades arquiteturais e os Padrões de Projeto (GoF) mapeados para a implementação de cada módulo.

---

## Feature 1: Autenticação de Usuários
**Camada:** Service / Controller  
**Padrões Aplicados:** Strategy, Factory Method

Módulo responsável por gerar e validar a "chave de acesso" do usuário durante o processo de login e autenticação contínua.

* **Descrição:** O sistema deve ser flexível o suficiente para trabalhar com uma "chave genérica", suportando múltiplas implementações de autenticação (ex: tokens JWT, API-keys, tokens opacos), sendo facilmente extensível para novos métodos no futuro.
* **Aplicação dos Padrões:** * O **Strategy** permite que o sistema ou o usuário decida qual estratégia de validação utilizar em tempo de execução.
  * O **Factory Method** atua na criação da instância correta da estratégia de autenticação com base no tipo de credencial fornecida.

---

## Feature 2: Middleware de Proteção de Rotas
**Camada:** Middleware (Intermediário entre View e Controller)  
**Padrões Aplicados:** Chain of Responsibility, Composite

Interceptador de requisições que garante que apenas usuários devidamente autenticados e autorizados acessem recursos protegidos.

* **Descrição:** Para cada requisição feita à API, o middleware executa uma série de validações sequenciais.
* **Aplicação dos Padrões:**
  * O **Chain of Responsibility** divide a validação em etapas independentes e encadeadas (ex: Etapa 1: Verifica a validade da chave de acesso -> Etapa 2: Verifica o nível de permissão do usuário).
  * O **Composite** é utilizado para modelar a estrutura de permissões do sistema (RBAC - *Role-Based Access Control*), tratando permissões individuais (folhas) e grupos de permissões/cargos (nós compostos) de forma uniforme durante a verificação de acesso.

---

## Feature 3: Endpoint para Integração com Sistemas Externos
**Camada:** Endpoint / View  
**Padrões Aplicados:** Adapter, Bridge, Template Method, Singleton, Command

Módulo responsável por realizar o *fetch* de dados em outras APIs REST. Deve ser genérico, permitindo a adição de novas integrações sem modificação na lógica central da aplicação.

* **Cenário 1 (Abordagem Estática):** Adição de novos endpoints de integração diretamente no código-fonte.
  * **Adapter:** Traduz os contratos e formatos de dados específicos de cada API externa para um modelo interno padronizado.
  * **Bridge:** Desacopla a abstração da chamada do endpoint da sua implementação técnica específica.
  * **Template Method:** Define o esqueleto do algoritmo de requisição HTTP (setup, auth, fetch, parse), permitindo que subclasses sobrescrevam apenas os detalhes específicos de cada sistema.
  * **Singleton:** Garante uma instância única do cliente HTTP (ex: *connection pool*) para otimizar o uso de recursos de rede.

* **Cenário 2 (Abordagem Dinâmica - Avançada):** Adição de novas chamadas/endpoints em tempo de execução (configuráveis por usuários com alto nível de privilégio).
  * **Command:** Encapsula todos os dados e ações necessárias para realizar uma chamada externa como um objeto. Isso permite que um "Invocador" genérico dispare requisições para novos sistemas dinamicamente, baseando-se apenas nos parâmetros do comando.

---

## Feature 4: Gestão e Persistência de Dados de Terceiros
**Camada:** Service / Controller  
**Padrões Aplicados:** Facade, Memento, State

Módulo que dita o comportamento da aplicação em relação aos dados obtidos através da Feature 3.

* **Cenário 1 (Proxy/Gateway):** Os dados são apenas repassados ao cliente, sem persistência local.
  * **Facade:** O sistema atua como uma fachada, orquestrando as chamadas complexas aos microsserviços externos e devolvendo uma resposta consolidada ao usuário final, ocultando a complexidade da infraestrutura externa.

* **Cenário 2 (Cache e Sincronização):** Os dados recentes são armazenados localmente (RAM ou Banco de Dados) para otimização, exigindo rotinas periódicas de atualização (*polling* ou sincronização).
  * **Memento:** Permite salvar estados anteriores dos dados recebidos para fins de auditoria, *rollback* ou comparação de histórico, sem violar o encapsulamento dos objetos.
  * **State:** Gerencia o ciclo de vida da informação armazenada, alterando o comportamento do dado com base no seu status atual (ex: `ATUALIZADO`, `DESATUALIZADO`, `EM_SINCRONIZACAO`).