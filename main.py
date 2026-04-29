# ejemplo de api con base de datos sqlite
#primero vamos a instalar dependencias:
#pip install fastapi uvicorn
#creacion del archivo main.py


from fastapi import FastAPI, HTTPException
import sqlite3

app = FastAPI()
# --- Modelos Pydantic ---
from pydantic import BaseModel
from typing import List

class Habilidad(BaseModel):
    name: str
    description: str

class Agente(BaseModel):
    name: str
    rol: str
    origen: str
    habilidades: List[Habilidad]
    
# Conexión a base de datos en memoria
conn = sqlite3.connect(":memory:", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("CREATE TABLE agentes (id INTEGER PRIMARY KEY, name TEXT, rol TEXT, origen TEXT)")
cursor.execute("CREATE TABLE habilidades ( id INTEGER PRIMARY KEY,name TEXT,description TEXT, agente_id INTEGER, FOREIGN KEY (agente_id) REFERENCES agentes(id))")
cursor.execute("INSERT INTO agentes (name, rol, origen) VALUES ('jett','duelista','Corea Del Sur')")
cursor.execute("INSERT INTO habilidades (name, description, agente_id) VALUES ('Lanzar Cuchillos','Lanza un total de 6 cuchillos','1')")
cursor.execute("INSERT INTO agentes (name, rol, origen) VALUES ('gekko','Iniciador','US')")
cursor.execute("INSERT INTO habilidades (name, description, agente_id) VALUES ('Carnalito','Haces que carnalito plante la spike por ti','2')")
conn.commit()

# --- Endpoints CRUD ---

# Listar todos los agentes
@app.get("/agentes")
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
@app.get("/agentes/{agente_id}")
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
@app.post("/agentes")
def add_agente(agente: Agente):
    cursor.execute("INSERT INTO agentes (name, rol, origen) VALUES (?, ?, ?)", (agente.name, agente.rol, agente.origen))
    
    agente_id = cursor.lastrowid
    for habilidad in agente.habilidades:
        cursor.execute("INSERT INTO habilidades (name, description, agente_id) VALUES (?, ?, ?)", (habilidad.name, habilidad.description, agente_id))
    conn.commit()
    return {"id": agente_id,**agente.dict()}

# Actualizar agente
@app.put("/agentes/{agente_id}")
def update_agente(agente_id: int, agente: Agente):

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
@app.delete("/agentes/{agente_id}")
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
#http://127.0.0.1:8000/agentes → lista todos.
#http://127.0.0.1:8000/agentes/1 → obtiene agente por ID.
#POST /agentes → crea agente.
#PUT /agentes/{id} → actualiza agente.
#DELETE /agentes/{id} → elimina agente.

#Documentación automática:
#Swagger UI: http://127.0.0.1:8000/docs
# ReDoc: http://127.0.0.1:8000/redoc