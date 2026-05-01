# ejemplo de api con base de datos sqlite
#primero vamos a instalar dependencias:
#pip install fastapi uvicorn
#creacion del archivo main.py

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List
import sqlite3

app = FastAPI()
app = FastAPI(
    title="API de Agentes de Valorant",
    description="API REST para gestionar agentes y habilidades",
    version="1.0.0",
    openapi_tags=[{"name": "Agentes", "description": "CRUD de agentes"}]
    
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # en producción puedes limitar
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# --- Modelos Pydantic ---
from pydantic import BaseModel
from typing import List

class Habilidad(BaseModel):
    name: str = Field(..., example="Dash")
    description: str = Field(..., example="Se impulsa rápidamente")

class AgenteBase(BaseModel):
    name: str = Field(..., example="Jett")
    rol: str = Field(..., example="Duelista")
    origen: str = Field(..., example="Corea del Sur")

class AgenteCreate(AgenteBase):
    habilidades: List[Habilidad]

class AgenteResponse(AgenteBase):
    id: int
    habilidades: List[Habilidad]
    
# Conexión a base de datos en memoria
conn = sqlite3.connect("agentes.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS agentes (id INTEGER PRIMARY KEY, name TEXT, rol TEXT, origen TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS habilidades ( id INTEGER PRIMARY KEY,name TEXT,description TEXT, agente_id INTEGER, FOREIGN KEY (agente_id) REFERENCES agentes(id))")
cursor.execute("INSERT INTO agentes (name, rol, origen) VALUES ('jett','duelista','Corea Del Sur')")
cursor.execute("INSERT INTO habilidades (name, description, agente_id) VALUES ('Lanzar Cuchillos','Lanza un total de 6 cuchillos','1')")
cursor.execute("INSERT INTO agentes (name, rol, origen) VALUES ('gekko','Iniciador','US')")
cursor.execute("INSERT INTO habilidades (name, description, agente_id) VALUES ('Carnalito','Haces que carnalito plante la spike por ti','2')")
conn.commit()

# --- Endpoints CRUD ---

# Listar todos los agentes
@app.get(
    "/api/v1/agentes",
    response_model=List[AgenteResponse],
    tags=["Agentes"],
    summary="Listar agentes",
    description="Obtiene todos los agentes con sus habilidades"
)
def get_agentes():
    cursor.execute("SELECT * FROM agentes")
    agentes = cursor.fetchall()

    resultado = []

    for ag in agentes:
        cursor.execute(
            "SELECT name, description FROM habilidades WHERE agente_id=?",
            (ag[0],)
        )
        habilidades = cursor.fetchall()

        resultado.append({
            "id": ag[0],
            "name": ag[1],
            "rol": ag[2],
            "origen": ag[3],
            "habilidades": [
                {"name": h[0], "description": h[1]} for h in habilidades
            ]
        })

    return resultado

# Obtener agente por ID
@app.get(
    "/api/v1/agentes/{agente_id}",
    response_model=AgenteResponse,
    tags=["Agentes"],
    summary="Obtener agente por ID",
    responses={404: {"description": "Agente no encontrado"}}
)
def get_agente(agente_id: int):
    cursor.execute("SELECT * FROM agentes WHERE id=?", (agente_id,))
    ag = cursor.fetchone()

    if not ag:
        raise HTTPException(status_code=404, detail="Agente no encontrado")

    cursor.execute(
        "SELECT name, description FROM habilidades WHERE agente_id=?",
        (agente_id,)
    )
    habilidades = cursor.fetchall()

    return {
        "id": ag[0],
        "name": ag[1],
        "rol": ag[2],
        "origen": ag[3],
        "habilidades": [
            {"name": h[0], "description": h[1]} for h in habilidades
        ]
    }

# Crear agente
@app.post("/api/v1/agentes",
    response_model=AgenteResponse,
    status_code=201,
    tags=["Agentes"],
    summary="Crear agente"
)
def add_agente(agente: AgenteCreate):
    cursor.execute("INSERT INTO agentes (name, rol, origen) VALUES (?, ?, ?)",
                   (agente.name, agente.rol, agente.origen))

    agente_id = cursor.lastrowid

    for hab in agente.habilidades:
        cursor.execute("INSERT INTO habilidades (name, description, agente_id) VALUES (?, ?, ?)",
                       (hab.name, hab.description, agente_id))

    conn.commit()

    return {"id": agente_id, **agente.dict()}





# Actualizar agente
@app.put(
    "/api/v1/agentes/{agente_id}",
    response_model=AgenteResponse,
    tags=["Agentes"],
    summary="Actualizar agente"
)

def update_agente(agente_id: int, agente: AgenteCreate):

    # 1. Actualizar agente
    cursor.execute(
        "UPDATE agentes SET name=?, rol=?, origen=? WHERE id=?",
        (agente.name, agente.rol, agente.origen, agente_id)
    )

    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Agente no encontrado")

    # 2. Borrar habilidades anteriores
    cursor.execute("DELETE FROM habilidades WHERE agente_id=?", (agente_id,))

    # 3. Insertar nuevas habilidades
    for hab in agente.habilidades:
        cursor.execute(
            "INSERT INTO habilidades (name, description, agente_id) VALUES (?, ?, ?)",
            (hab.name, hab.description, agente_id)
        )

    conn.commit()

    return {"id": agente_id, **agente.dict()}



# Borrar agente
@app.delete("/api/v1/agentes/{agente_id}",
    status_code=204,
    tags=["Agentes"],
    summary="Eliminar agente")

def delete_agente(agente_id: int):
    cursor.execute("DELETE FROM agentes WHERE id=?", (agente_id,))
    conn.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Agente no encontrado")
    return {"message": f"Agente {agente_id} eliminado"}


#ejecutamos la API
#uvicorn main:app --reload

#la podemosmprobar en el navegador:
#
#http://127.0.0.1:8000/api/v1/agentes → lista todos.
#http://127.0.0.1:8000/api/v1/agentes/1 → obtiene agente por ID.
#POST /api/v1/agentes → crea agente.
#PUT /api/v1/agentes/{id} → actualiza agente.
#DELETE /api/v1/agentes/{id} → elimina agente.

#Documentación automática:
#Swagger UI: http://127.0.0.1:8000/docs
# ReDoc: http://127.0.0.1:8000/redoc