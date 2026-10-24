# Sistema de Gerenciamento de Academia

**Autora:** Mariana Costa Melo de Carvalho  
**Matrícula:** 2024003941  
**Instituição:** Universidade Federal de Itajubá (UNIFEI)  
**Disciplina:** ECOT11A – Engenharia de Software I

## 1. Descrição do Projeto

O Sistema de Gerenciamento de Academia é um software desenvolvido como MVP (*Minimum Viable Product*), com base nos requisitos e nas modelagens elaborados nos Labs 1 a 5 da disciplina de Engenharia de Software I.

O sistema permite gerenciar alunos, planos, turmas e vagas, além de controlar o acesso por perfil de usuário. O administrador possui acesso às funcionalidades de gerenciamento, enquanto o aluno pode consultar seus próprios dados, visualizar aulas disponíveis e realizar ou cancelar inscrições.

**Tecnologias utilizadas:** Python, FastAPI, SQLAlchemy, SQLite, HTML5, CSS3, JavaScript, Uvicorn e bcrypt.

## 2. Como Executar o Projeto Localmente

### Pré-requisitos

- Python 3 instalado.
- Git instalado.

### Passo 1 — Clonar o repositório

Abra o terminal e execute:

```bash
git clone https://github.com/marianacmc27/sistema-gerenciamento-academia.git
```

Acesse a pasta do projeto:

```bash
cd sistema-gerenciamento-academia
```

### Passo 2 — Criar o ambiente virtual

```bash
python3 -m venv venv
```

No Linux, ative o ambiente virtual com:

```bash
source venv/bin/activate
```

No Windows, utilize:

```powershell
venv\Scripts\activate
```

### Passo 3 — Instalar as dependências

Com o ambiente virtual ativado, execute:

```bash
pip install fastapi uvicorn sqlalchemy bcrypt
```

### Passo 4 — Executar o backend

Na pasta raiz do projeto, execute:

```bash
uvicorn backend.main:app --reload
```

O servidor será iniciado em:

http://127.0.0.1:8000

### Passo 5 — Acessar o sistema

Com o backend em execução, abra o arquivo `login.html` no navegador ou utilize a extensão Live Server do Visual Studio Code para acessar a interface.

A documentação interativa da API pode ser acessada em:

http://127.0.0.1:8000/docs

### Credenciais para teste

**Administrador**
- Usuário: `admin`
- Senha: `1234`

**Aluno**
- Usuário: `aluno1`
- Senha: `1234`

