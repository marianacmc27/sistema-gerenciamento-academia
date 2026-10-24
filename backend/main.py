from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Configuração do Banco de Dados SQLite local
SQLALCHEMY_DATABASE_URL = "sqlite:///./academia.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Modelos do Banco de Dados (SQLAlchemy)
class AlunoDB(Base):
    __tablename__ = "alunos"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    plano = Column(String)

class AulaDB(Base):
    __tablename__ = "aulas"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    professor = Column(String)
    horario = Column(String)
    vagas_maximas = Column(Integer)
    inscritos = Column(Integer, default=0)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sistema de Gerenciamento de Academia - ECOT11A", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependência de Sessão do Banco
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic Schemas
class LoginRequest(BaseModel):
    usuario: str
    senha: str

class AlunoSchema(BaseModel):
    id: int
    nome: str
    email: str
    plano: str
    class Config:
        from_attributes = True

class AulaSchema(BaseModel):
    id: int
    nome: str
    professor: str
    horario: str
    vagas_maximas: int
    inscritos: int
    class Config:
        from_attributes = True

class NovaAulaSchema(BaseModel):
    id: int
    nome: str
    professor: str
    horario: str
    vagas_maximas: int

# Popular dados iniciais se o banco estiver vazio
def popular_dados_iniciais():
    db = SessionLocal()
    if db.query(AlunoDB).count() == 0:
        db.add_all([
            AlunoDB(id=1, nome="Ana Souza", email="ana@email.com", plano="Mensal - Musculação"),
            AlunoDB(id=2, nome="Carlos Lima", email="carlos@email.com", plano="Anual - Completo"),
            AlunoDB(id=3, nome="Mariana Carvalho", email="mariana@email.com", plano="Trimestral - Cross")
        ])
    if db.query(AulaDB).count() == 0:
        db.add_all([
            AulaDB(id=1, nome="Spinning", professor="Prof. Marcos", horario="Seg/Qua 08:00", vagas_maximas=15, inscritos=12),
            AulaDB(id=2, nome="CrossFit", professor="Profª. Julia", horario="Ter/Qui 10:00", vagas_maximas=10, inscritos=10),
            AulaDB(id=3, nome="Musculação Avançada", professor="Prof. Carlos", horario="Seg a Sex 14:00", vagas_maximas=25, inscritos=18)
        ])
    db.commit()
    db.close()

popular_dados_iniciais()

# Rotas da API
@app.post("/login")
def fazer_login(dados: LoginRequest):
    if dados.usuario == "admin" and dados.senha == "1234":
        return {"perfil": "admin", "nome": "Administrador do Sistema"}
    elif dados.usuario.startswith("aluno") and dados.senha == "1234":
        return {"perfil": "aluno", "nome": "Mariana Carvalho"}
    raise HTTPException(status_code=401, detail="Credenciais inválidas.")

@app.get("/estatisticas")
def estatisticas(db: Session = Depends(get_db)):
    alunos = db.query(AlunoDB).all()
    aulas = db.query(AulaDB).all()
    return {
        "total_alunos": len(alunos),
        "total_aulas": len(aulas),
        "vagas_totais": sum(a.vagas_maximas for a in aulas),
        "vagas_ocupadas": sum(a.inscritos for a in aulas)
    }

@app.get("/alunos", response_model=List[AlunoSchema])
def listar_alunos(db: Session = Depends(get_db)):
    return db.query(AlunoDB).all()

@app.post("/alunos", response_model=AlunoSchema)
def cadastrar_aluno(aluno: AlunoSchema, db: Session = Depends(get_db)):
    existente = db.query(AlunoDB).filter(AlunoDB.id == aluno.id).first()
    if existente:
        raise HTTPException(status_code=400, detail="ID de aluno já cadastrado.")
    novo = AlunoDB(id=aluno.id, nome=aluno.nome, email=aluno.email, plano=aluno.plano)
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo

@app.get("/aulas", response_model=List[AulaSchema])
def listar_aulas(db: Session = Depends(get_db)):
    return db.query(AulaDB).all()

@app.post("/aulas", response_model=AulaSchema)
def criar_aula(aula: NovaAulaSchema, db: Session = Depends(get_db)):
    existente = db.query(AulaDB).filter(AulaDB.id == aula.id).first()
    if existente:
        raise HTTPException(status_code=400, detail="ID de aula já cadastrado.")
    nova = AulaDB(id=aula.id, nome=aula.nome, professor=aula.professor, horario=aula.horario, vagas_maximas=aula.vagas_maximas, inscritos=0)
    db.add(nova)
    db.commit()
    db.refresh(nova)
    return nova

@app.delete("/aulas/{aula_id}")
def remover_aula(aula_id: int, db: Session = Depends(get_db)):
    aula = db.query(AulaDB).filter(AulaDB.id == aula_id).first()
    if not aula:
        raise HTTPException(status_code=404, detail="Aula não encontrada.")
    db.delete(aula)
    db.commit()
    return {"message": "Aula removida com sucesso!"}

@app.post("/aulas/{aula_id}/inscrever")
def inscrever_aula(aula_id: int, db: Session = Depends(get_db)):
    aula = db.query(AulaDB).filter(AulaDB.id == aula_id).first()
    if not aula:
        raise HTTPException(status_code=404, detail="Aula não encontrada.")
    if aula.inscritos < aula.vagas_maximas:
        aula.inscritos += 1
        db.commit()
        return {"message": f"Inscrição realizada com sucesso na aula {aula.nome}!"}
    else:
        raise HTTPException(status_code=400, detail="Esta turma já atingiu o limite máximo de vagas!")

@app.post("/aulas/{aula_id}/cancelar")
def cancelar_inscricao(aula_id: int, db: Session = Depends(get_db)):
    aula = db.query(AulaDB).filter(AulaDB.id == aula_id).first()
    if not aula:
        raise HTTPException(status_code=404, detail="Aula não encontrada.")
    if aula.inscritos > 0:
        aula.inscritos -= 1
        db.commit()
        return {"message": f"Inscrição cancelada com sucesso na aula {aula.nome}!"}
    else:
        raise HTTPException(status_code=400, detail="Não há inscrições ativas nesta aula.")
