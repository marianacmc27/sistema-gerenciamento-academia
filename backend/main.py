from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Table, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Session
import bcrypt

# Configuração do Banco de Dados SQLite Local
DATABASE_URL = "sqlite:///./academia.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Tabela associativa para Inscrições (Alunos <-> Aulas)
inscricoes_table = Table(
    "inscricoes",
    Base.metadata,
    Column("aluno_id", Integer, ForeignKey("alunos.id"), primary_key=True),
    Column("aula_id", Integer, ForeignKey("aulas.id"), primary_key=True)
)

# Modelos do Banco de Dados (SQLAlchemy)
class AlunoDB(Base):
    __tablename__ = "alunos"
    id = Column(Integer, primary_key=True, index=True)
    usuario = Column(String, unique=True, index=True)
    senha_hash = Column(String)
    nome = Column(String)
    email = Column(String)
    plano = Column(String)
    status_pagamento = Column(String)  # Quitado / Pendente
    vencimento_plano = Column(String)
    perfil = Column(String, default="aluno") # admin ou aluno
    
    aulas_inscritas = relationship("AulaDB", secondary=inscricoes_table, back_populates="alunos_inscritos")

class AulaDB(Base):
    __tablename__ = "aulas"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String)
    professor = Column(String)
    horario = Column(String)
    vagas_maximas = Column(Integer)
    
    alunos_inscritos = relationship("AlunoDB", secondary=inscricoes_table, back_populates="aulas_inscritas")

Base.metadata.create_all(bind=engine)

# Schemas Pydantic (Validação de Entrada/Saída)
class AlunoCreate(BaseModel):
    id: int
    usuario: str
    nome: str
    email: str
    plano: str
    status_pagamento: str
    vencimento_plano: str

class AlunoUpdate(BaseModel):
    nome: str
    email: str
    plano: str
    status_pagamento: str
    vencimento_plano: str

class AulaCreate(BaseModel):
    id: int
    nome: str
    professor: str
    horario: str
    vagas_maximas: int

class AulaUpdate(BaseModel):
    id: int
    nome: str
    professor: str
    horario: str
    vagas_maximas: int

class LoginRequest(BaseModel):
    usuario: str
    senha: str

# Inicialização do FastAPI
app = FastAPI(title="Sistema de Gerenciamento de Academia", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Popular Dados Iniciais (Seed)
def popular_dados_iniciais():
    db = SessionLocal()
    if db.query(AlunoDB).count() == 0:
        senha_padrao = bcrypt.hashpw("1234".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Criando Admin e Alunos de Teste
        admin = AlunoDB(id=1, usuario="admin", senha_hash=senha_padrao, nome="Administrador Geral", email="admin@academia.com", plano="Gestão", status_pagamento="Quitado", vencimento_plano="2026-12-31", perfil="admin")
        aluno1 = AlunoDB(id=2, usuario="aluno1", senha_hash=senha_padrao, nome="Mariana Carvalho", email="mariana@unifei.edu.br", plano="Musculação Completa", status_pagamento="Quitado", vencimento_plano="2026-12-31", perfil="aluno")
        aluno2 = AlunoDB(id=3, usuario="aluno2", senha_hash=senha_padrao, nome="Carlos Silva", email="carlos@gmail.com", plano="Pilates", status_pagamento="Pendente", vencimento_plano="2026-05-01", perfil="aluno")
        
        db.add_all([admin, aluno1, aluno2])
        
        # Criando Aulas Iniciais
        aula1 = AulaDB(id=1, nome="Musculação Orientada", professor="Prof. Ricardo", horario="Seg/Qua/Sex 08:00", vagas_maximas=5)
        aula2 = AulaDB(id=2, nome="Pilates Avançado", professor="Profa. Juliana", horario="Ter/Qui 10:00", vagas_maximas=2)
        aula3 = AulaDB(id=3, nome="Spinning", professor="Prof. Marcos", horario="Seg/Qua 18:00", vagas_maximas=10)
        
        db.add_all([aula1, aula2, aula3])
        db.commit()
    db.close()

popular_dados_iniciais()

# Rotas de Autenticação
@app.post("/login")
def login(dados: LoginRequest, db: Session = Depends(get_db)):
    usuario = db.query(AlunoDB).filter(AlunoDB.usuario == dados.usuario).first()
    if not usuario or not bcrypt.checkpw(dados.senha.encode('utf-8'), usuario.senha_hash.encode('utf-8')):
        raise HTTPException(status_code=401, detail="Usuário ou senha incorretos.")
    return {
        "message": "Login bem-sucedido",
        "usuario": usuario.usuario,
        "nome": usuario.nome,
        "perfil": usuario.perfil
    }

# Rotas de Alunos
@app.get("/alunos")
def listar_alunos(db: Session = Depends(get_db)):
    return db.query(AlunoDB).all()

@app.get("/alunos/{usuario}")
def buscar_aluno(usuario: str, db: Session = Depends(get_db)):
    aluno = db.query(AlunoDB).filter(AlunoDB.usuario == usuario).first()
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno não encontrado.")
    return aluno

@app.post("/alunos")
def criar_aluno(dados: AlunoCreate, db: Session = Depends(get_db)):
    existente = db.query(AlunoDB).filter((AlunoDB.id == dados.id) | (AlunoDB.usuario == dados.usuario)).first()
    if existente:
        raise HTTPException(status_code=400, detail="ID ou nome de usuário já cadastrado.")
    
    senha_padrao = bcrypt.hashpw("1234".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    novo = AlunoDB(
        id=dados.id,
        usuario=dados.usuario,
        senha_hash=senha_padrao,
        nome=dados.nome,
        email=dados.email,
        plano=dados.plano,
        status_pagamento=dados.status_pagamento,
        vencimento_plano=dados.vencimento_plano,
        perfil="aluno"
    )
    db.add(novo)
    db.commit()
    return {"message": "Aluno cadastrado com sucesso!"}

@app.put("/alunos/{id}")
def atualizar_aluno(id: int, dados: AlunoUpdate, db: Session = Depends(get_db)):
    aluno = db.query(AlunoDB).filter(AlunoDB.id == id).first()
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno não encontrado.")
    
    aluno.nome = dados.nome
    aluno.email = dados.email
    aluno.plano = dados.plano
    aluno.status_pagamento = dados.status_pagamento
    aluno.vencimento_plano = dados.vencimento_plano
    db.commit()
    return {"message": "Aluno atualizado com sucesso!"}

# Rotas de Aulas e Inscrições
@app.get("/aulas")
def listar_aulas(db: Session = Depends(get_db)):
    aulas = db.query(AulaDB).all()
    resultado = []
    for a in aulas:
        resultado.append({
            "id": a.id,
            "nome": a.nome,
            "professor": a.professor,
            "horario": a.horario,
            "vagas_maximas": a.vagas_maximas,
            "inscritos": len(a.alunos_inscritos),
            "lista_alunos": [al.nome for al in a.alunos_inscritos]
        })
    return resultado

@app.post("/aulas")
def criar_aula(dados: AulaCreate, db: Session = Depends(get_db)):
    existente = db.query(AulaDB).filter(AulaDB.id == dados.id).first()
    if existente:
        raise HTTPException(status_code=400, detail="ID de turma já existente.")
    nova = AulaDB(
        id=dados.id,
        nome=dados.nome,
        professor=dados.professor,
        horario=dados.horario,
        vagas_maximas=dados.vagas_maximas
    )
    db.add(nova)
    db.commit()
    return {"message": "Turma cadastrada com sucesso!"}

@app.put("/aulas/{id}")
def atualizar_aula(id: int, dados: AulaUpdate, db: Session = Depends(get_db)):
    aula = db.query(AulaDB).filter(AulaDB.id == id).first()
    if not aula:
        raise HTTPException(status_code=404, detail="Turma não encontrada.")
    aula.nome = dados.nome
    aula.professor = dados.professor
    aula.horario = dados.horario
    aula.vagas_maximas = dados.vagas_maximas
    db.commit()
    return {"message": "Turma alterada com sucesso!"}

@app.delete("/aulas/{id}")
def remover_aula(id: int, db: Session = Depends(get_db)):
    aula = db.query(AulaDB).filter(AulaDB.id == id).first()
    if not aula:
        raise HTTPException(status_code=404, detail="Turma não encontrada.")
    db.delete(aula)
    db.commit()
    return {"message": "Turma removida com sucesso!"}

@app.post("/aulas/{id}/inscrever")
def inscrever_aula(id: int, aluno_usuario: str, db: Session = Depends(get_db)):
    aula = db.query(AulaDB).filter(AulaDB.id == id).first()
    aluno = db.query(AlunoDB).filter(AlunoDB.usuario == aluno_usuario).first()
    
    if not aula or not aluno:
        raise HTTPException(status_code=404, detail="Aula ou aluno não encontrado.")
    
    # Validação de Inadimplência (RN05)
    if aluno.status_pagamento != "Quitado":
        raise HTTPException(status_code=400, detail="Inscrição negada: Pagamento pendente ou plano vencido.")
    
    # Validação de Limite de Vagas (RN01 / RNF02.3)
    if len(aula.alunos_inscritos) >= aula.vagas_maximas:
        raise HTTPException(status_code=400, detail="Turma lotada! Não há vagas disponíveis.")
    
    if aluno in aula.alunos_inscritos:
        raise HTTPException(status_code=400, detail="Aluno já está inscrito nesta turma.")
    
    aula.alunos_inscritos.append(aluno)
    db.commit()
    return {"message": "Inscrição confirmada com sucesso!"}

@app.post("/aulas/{id}/cancelar")
def cancelar_inscricao(id: int, aluno_usuario: str, db: Session = Depends(get_db)):
    aula = db.query(AulaDB).filter(AulaDB.id == id).first()
    aluno = db.query(AlunoDB).filter(AlunoDB.usuario == aluno_usuario).first()
    
    if not aula or not aluno:
        raise HTTPException(status_code=404, detail="Aula ou aluno não encontrado.")
    
    if aluno not in aula.alunos_inscritos:
        raise HTTPException(status_code=400, detail="Você não possui inscrição ativa nesta turma.")
    
    aula.alunos_inscritos.remove(aluno)
    db.commit()
    return {"message": "Inscrição cancelada com sucesso!"}

# Estatísticas para o Dashboard
@app.get("/estatisticas")
def estatisticas(db: Session = Depends(get_db)):
    total_alunos = db.query(AlunoDB).filter(AlunoDB.perfil == "aluno").count()
    aulas = db.query(AulaDB).all()
    total_aulas = len(aulas)
    
    vagas_ocupadas = sum(len(a.alunos_inscritos) for a in aulas)
    vagas_totais = sum(a.vagas_maximas for a in aulas)
    
    return {
        "total_alunos": total_alunos,
        "total_aulas": total_aulas,
        "vagas_ocupadas": vagas_ocupadas,
        "vagas_totais": vagas_totais
    }
