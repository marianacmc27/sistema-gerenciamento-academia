from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

app = FastAPI(title="Sistema de Gerenciamento de Academia", version="1.0.0")

# Habilitar CORS para o frontend comunicar com o backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos de Dados (Pydantic)
class Aluno(BaseModel):
    id: int
    nome: str
    email: str
    plano: str

class Aula(BaseModel):
    id: int
    nome: str
    vagas_maximas: int
    inscritos: int

# Banco de Dados em Memória (para fins do MVP leve)
db_alunos = [
    Aluno(id=1, nome="Ana Souza", email="ana@email.com", plano="Mensal - Musculação"),
    Aluno(id=2, nome="Carlos Lima", email="carlos@email.com", plano="Anual - Completo")
]

db_aulas = [
    Aula(id=1, nome="Spinning", vagas_maximas=15, inscritos=12),
    Aula(id=2, nome="CrossFit", vagas_maximas=10, inscritos=10) # Lotada
]

@app.get("/")
def home():
    return {"message": "API do Sistema de Gerenciamento de Academia ativa!"}

@app.get("/alunos", response_model=List[Aluno])
def listar_alunos():
    return db_alunos

@app.post("/alunos", response_model=Aluno)
def cadastrar_aluno(aluno: Aluno):
    for a in db_alunos:
        if a.id == aluno.id:
            raise HTTPException(status_code=400, detail="ID de aluno já cadastrado.")
    db_alunos.append(aluno)
    return aluno

@app.get("/aulas", response_model=List[Aula])
def listar_aulas():
    return db_aulas

@app.post("/aulas/{aula_id}/inscrever")
def inscrever_aula(aula_id: int):
    for aula in db_aulas:
        if aula.id == aula_id:
            if aula.inscritos < aula.vagas_maximas:
                aula.inscritos += 1
                return {"message": f"Inscrição realizada com sucesso na aula {aula.nome}!", "vagas_restantes": aula.vagas_maximas - aula.inscritos}
            else:
                raise HTTPException(status_code=400, detail="Atenção: Esta aula já atingiu o limite máximo de vagas!")
    raise HTTPException(status_code=404, detail="Aula não encontrada.")
