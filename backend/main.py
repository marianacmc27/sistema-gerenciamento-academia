from fastapi import FastAPI

app = FastAPI(title="Sistema de Gerenciamento de Academia")

@app.get("/")
def home():
    return {"message": "API a funcionar!"}
