from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="Sistema de Gerenciamento de Academia - ECOT11A", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos de Dados (Alinhados ao Diagrama de Classes)
class LoginRequest(BaseModel):
    usuario: str
    senha: str

class Aluno(BaseModel):
    id: int
    nome: str
    email: str
    plano: str

class Aula(BaseModel):
    id: int
    nome: str
    professor: str
    horario: str
    vagas_maximas: int
    inscritos: int

# Repositório em Memória (Mock do Banco de Dados relacional)
db_alunos = [
    Aluno(id=1, nome="Ana Souza", email="ana@email.com", plano="Mensal - Musculação"),
    Aluno(id=2, nome="Carlos Lima", email="carlos@email.com", plano="Anual - Completo"),
    Aluno(id=3, nome="Mariana Carvalho", email="mariana@email.com", plano="Trimestral - Cross")
]

db_aulas = [
    Aula(id=1, nome="Spinning", professor="Prof. Marcos", horario="Seg/Qua 08:00", vagas_maximas=15, inscritos=12),
    Aula(id=2, nome="CrossFit", professor="Profª. Julia", horario="Ter/Qui 10:00", vagas_maximas=10, inscritos=10),
    Aula(id=3, nome="Musculação Avançada", professor="Prof. Carlos", horario="Seg a Sex 14:00", vagas_maximas=25, inscritos=18)
]

# Autenticação baseada em Perfis (Requisito de Acesso)
@app.post("/login")
def fazer_login(dados: LoginRequest):
    if dados.usuario == "admin" and dados.senha == "1234":
        return {"perfil": "admin", "nome": "Administrador do Sistema"}
    elif dados.usuario.startswith("aluno") and dados.senha == "1234":
        return {"perfil": "aluno", "nome": "Aluno Cadastrado"}
    raise HTTPException(status_code=401, detail="Usuário ou senha inválidos. (Use admin/1234 ou aluno/1234)")

# Estatísticas (Dashboard)
@app.get("/estatisticas")
def estatisticas():
    return {
        "total_alunos": len(db_alunos),
        "total_aulas": len(db_aulas),
        "vagas_totais": sum(a.vagas_maximas for a in db_aulas),
        "vagas_ocupadas": sum(a.inscritos for a in db_aulas)
    }

# Gestão de Alunos
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

# Gestão de Aulas e Inscrições (Regra de Vagas)
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
                raise HTTPException(status_code=400, detail="Atenção: Esta turma já atingiu o limite máximo de vagas!")
    raise HTTPException(status_code=404, detail="Aula não encontrada.")
