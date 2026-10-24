from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Table, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from passlib.context import CryptContext

# Configuração de Hash de Senha (RNF01.2 - Segurança)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SQLALCHEMY_DATABASE_URL = "sqlite:///./academia.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

inscricoes_tabela = Table(
    'inscricoes', Base.metadata,
    Column('aluno_id', Integer, ForeignKey('alunos.id'), primary_key=True),
    Column('aula_id', Integer, ForeignKey('aulas.id'), primary_key=True),
    Column('presenca', Boolean, default=False)
)

class AlunoDB(Base):
    __tablename__ = "alunos"
    id = Column(Integer, primary_key=True, index=True)
    usuario = Column(String, unique=True, index=True)
    senha_hash = Column(String) # RNF01.2: Senha protegida por hash
    nome = Column(String)
    email = Column(String, unique=True)
    plano = Column(String)
    status_pagamento = Column(String, default="Quitado")
    vencimento_plano = Column(String, default="2026-12-31")
    
    aulas = relationship("AulaDB", secondary=inscricoes_tabela, back_populates="alunos_inscritos")

class PlanoDB(Base):
    __tablename__ = "planos"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, unique=True, index=True)
    valor = Column(String)
    descricao = Column(String)

class AulaDB(Base):
    __tablename__ = "aulas"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    professor = Column(String)
    horario = Column(String)
    vagas_maximas = Column(Integer)
    
    alunos_inscritos = relationship("AlunoDB", secondary=inscricoes_tabela, back_populates="aulas")

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sistema de Gerenciamento de Academia", version="1.0.0")

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

class LoginRequest(BaseModel):
    usuario: str
    senha: str

class AlunoSchema(BaseModel):
    id: int
    usuario: str
    nome: str
    email: str
    plano: str
    status_pagamento: str
    vencimento_plano: str
    class Config:
        from_attributes = True

class NovoAlunoSchema(BaseModel):
    id: int
    usuario: str
    senha: str
    nome: str
    email: str
    plano: str
    status_pagamento: str = "Quitado"
    vencimento_plano: str = "2026-12-31"

class AtualizarAlunoSchema(BaseModel):
    nome: str
    email: str
    plano: str
    status_pagamento: str
    vencimento_plano: str

class NovaAulaSchema(BaseModel):
    id: int
    nome: str
    professor: str
    horario: str
    vagas_maximas: int

def popular_dados_iniciais():
    db = SessionLocal()
    senha_padrao = pwd_context.hash("1234") # Hash seguro bcrypt
    
    if db.query(AlunoDB).count() == 0:
        db.add_all([
            AlunoDB(id=1, usuario="aluno1", senha_hash=senha_padrao, nome="Ana Souza", email="ana@email.com", plano="Mensal - Musculação", status_pagamento="Quitado", vencimento_plano="2026-06-30"),
            AlunoDB(id=2, usuario="aluno2", senha_hash=senha_padrao, nome="Carlos Lima", email="carlos@email.com", plano="Anual - Completo", status_pagamento="Pendente", vencimento_plano="2025-12-01"),
            AlunoDB(id=3, usuario="aluno3", senha_hash=senha_padrao, nome="Mariana Carvalho", email="mariana@email.com", plano="Trimestral - Cross", status_pagamento="Quitado", vencimento_plano="2026-11-15")
        ])
    if db.query(PlanoDB).count() == 0:
        db.add_all([
            PlanoDB(id=1, nome="Mensal - Musculação", valor="R$ 100,00", descricao="Acesso livre à musculação por 30 dias"),
            PlanoDB(id=2, nome="Trimestral - Cross", valor="R$ 270,00", descricao="Acesso ao CrossFit e Musculação"),
            PlanoDB(id=3, nome="Anual - Completo", valor="R$ 960,00", descricao="Acesso total a todas as modalidades e áreas")
        ])
    if db.query(AulaDB).count() == 0:
        db.add_all([
            AulaDB(id=1, nome="Spinning", professor="Prof. Marcos", horario="Seg/Qua 08:00", vagas_maximas=15),
            AulaDB(id=2, nome="CrossFit", professor="Profª. Julia", horario="Ter/Qui 10:00", vagas_maximas=10),
            AulaDB(id=3, nome="Musculação Avançada", professor="Prof. Carlos", horario="Seg a Sex 14:00", vagas_maximas=25)
        ])
    db.commit()
    db.close()

popular_dados_iniciais()

@app.post("/login")
def fazer_login(dados: LoginRequest, db: Session = Depends(get_db)):
    # Validação do Admin (senha hash simulada ou fixa segura)
    if dados.usuario == "admin" and dados.senha == "1234":
        return {"perfil": "admin", "nome": "Administrador / Funcionário", "usuario": "admin"}
    
    aluno = db.query(AlunoDB).filter(AlunoDB.usuario == dados.usuario).first()
    if aluno and pwd_context.verify(dados.senha, aluno.senha_hash):
        return {"perfil": "aluno", "nome": aluno.nome, "usuario": aluno.usuario, "id": aluno.id}
    
    raise HTTPException(status_code=401, detail="Usuário ou senha inválidos.")

@app.get("/estatisticas")
def estatisticas(db: Session = Depends(get_db)):
    alunos = db.query(AlunoDB).all()
    aulas = db.query(AulaDB).all()
    vagas_totais = sum(a.vagas_maximas for a in aulas)
    vagas_ocupadas = sum(len(a.alunos_inscritos) for a in aulas)
    pendentes = sum(1 for a in alunos if a.status_pagamento == "Pendente")
    return {
        "total_alunos": len(alunos),
        "total_aulas": len(aulas),
        "pagamentos_pendentes": pendentes,
        "vagas_totais": vagas_totais,
        "vagas_ocupadas": vagas_ocupadas
    }

@app.get("/alunos", response_model=List[AlunoSchema])
def listar_alunos(db: Session = Depends(get_db)):
    return db.query(AlunoDB).all()

@app.post("/alunos", response_model=AlunoSchema)
def cadastrar_aluno(aluno: NovoAlunoSchema, db: Session = Depends(get_db)):
    existente = db.query(AlunoDB).filter((AlunoDB.id == aluno.id) | (AlunoDB.usuario == aluno.usuario)).first()
    if existente:
        raise HTTPException(status_code=400, detail="ID ou usuário já cadastrado no sistema.")
    
    novo = AlunoDB(
        id=aluno.id,
        usuario=aluno.usuario,
        senha_hash=pwd_context.hash(aluno.senha), # Criptografa a senha com bcrypt
        nome=aluno.nome,
        email=aluno.email,
        plano=aluno.plano,
        status_pagamento=aluno.status_pagamento,
        vencimento_plano=aluno.vencimento_plano
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo

@app.put("/alunos/{aluno_id}")
def atualizar_aluno(aluno_id: int, dados: AtualizarAlunoSchema, db: Session = Depends(get_db)):
    aluno = db.query(AlunoDB).filter(AlunoDB.id == aluno_id).first()
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno não encontrado.")
    aluno.nome = dados.nome
    aluno.email = dados.email
    aluno.plano = dados.plano
    aluno.status_pagamento = dados.status_pagamento
    aluno.vencimento_plano = dados.vencimento_plano
    db.commit()
    return aluno

@app.get("/alunos/{usuario}", response_model=AlunoSchema)
def consultar_aluno_especifico(usuario: str, db: Session = Depends(get_db)):
    aluno = db.query(AlunoDB).filter(AlunoDB.usuario == usuario).first()
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno não encontrado.")
    return aluno

@app.get("/planos")
def listar_planos(db: Session = Depends(get_db)):
    return db.query(PlanoDB).all()

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

@app.post("/aulas", response_model=AulaSchema)
def criar_aula(aula: NovaAulaSchema, db: Session = Depends(get_db)):
    existente = db.query(AulaDB).filter(AulaDB.id == aula.id).first()
    if existente:
        raise HTTPException(status_code=400, detail="ID de aula já cadastrado.")
    nova = AulaDB(**aula.dict())
    db.add(nova)
    db.commit()
    db.refresh(nova)
    return {"id": nova.id, "nome": nova.nome, "professor": nova.professor, "horario": nova.horario, "vagas_maximas": nova.vagas_maximas, "inscritos": 0}

@app.put("/aulas/{aula_id}")
def atualizar_aula(aula_id: int, dados: NovaAulaSchema, db: Session = Depends(get_db)):
    aula = db.query(AulaDB).filter(AulaDB.id == aula_id).first()
    if not aula:
        raise HTTPException(status_code=404, detail="Aula não encontrada.")
    aula.nome = dados.nome
    aula.professor = dados.professor
    aula.horario = dados.horario
    aula.vagas_maximas = dados.vagas_maximas
    db.commit()
    return {"message": "Programação da aula atualizada com sucesso!"}

@app.delete("/aulas/{aula_id}")
def remover_aula(aula_id: int, db: Session = Depends(get_db)):
    aula = db.query(AulaDB).filter(AulaDB.id == aula_id).first()
    if not aula:
        raise HTTPException(status_code=404, detail="Aula não encontrada.")
    db.delete(aula)
    db.commit()
    return {"message": "Aula removida com sucesso!"}

@app.post("/aulas/{aula_id}/inscrever")
def inscrever_aula(aula_id: int, aluno_usuario: str, db: Session = Depends(get_db)):
    aula = db.query(AulaDB).filter(AulaDB.id == aula_id).first()
    aluno = db.query(AlunoDB).filter(AlunoDB.usuario == aluno_usuario).first()
    
    if not aula or not aluno:
        raise HTTPException(status_code=404, detail="Aula ou Aluno não encontrados.")
    
    if aluno.status_pagamento != "Quitado":
        raise HTTPException(status_code=400, detail="Inscrição bloqueada: O aluno possui pagamento pendente ou plano vencido.")
    
    if aluno in aula.alunos_inscritos:
        raise HTTPException(status_code=400, detail="Você já está inscrito nesta aula!")
        
    if len(aula.alunos_inscritos) < aula.vagas_maximas:
        aula.alunos_inscritos.append(aluno)
        db.commit()
        return {"message": f"Inscrição realizada com sucesso na aula {aula.nome}!"}
    else:
        raise HTTPException(status_code=400, detail="Esta turma já atingiu o limite máximo de vagas!")

@app.post("/aulas/{aula_id}/cancelar")
def cancelar_inscricao(aula_id: int, aluno_usuario: str, db: Session = Depends(get_db)):
    aula = db.query(AulaDB).filter(AulaDB.id == aula_id).first()
    aluno = db.query(AlunoDB).filter(AlunoDB.usuario == aluno_usuario).first()
    
    if not aula or not aluno:
        raise HTTPException(status_code=404, detail="Aula ou Aluno não encontrados.")
        
    if aluno in aula.alunos_inscritos:
        aula.alunos_inscritos.remove(aluno)
        db.commit()
        return {"message": f"Inscrição cancelada com sucesso na aula {aula.nome}!"}
    else:
        raise HTTPException(status_code=400, detail="Você não possui inscrição ativa nesta aula para poder cancelar.")
