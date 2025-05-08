"""
Backend FastAPI – acepta
  • DATA  →  .pdf | .xls | .xlsx | .docx
  • PLANTILLA →  .docx   (Word con placeholders)

Llama al arch_orchestrator y devuelve el DOCX/PDF resultante.
"""
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import tempfile, shutil, io, os

from backend.services.arch_orchestrator import arch_orchestrator   # ← ya lo tienes

app = FastAPI(title="Smart-Docs API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],   # React dev-server
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():       # sanity-check
    return {"status": "API OK"}

@app.post("/api/process")
async def process(
        data_file : UploadFile = File(...),         # Excel / PDF / DOCX
        tpl_file  : UploadFile = File(...)):        # DOCX plantilla
    #  1. Validaciones de extensión
    data_ext = Path(data_file.filename).suffix.lower()
    tpl_ext  = Path(tpl_file .filename).suffix.lower()

    if tpl_ext not in ( ".docx", ".xlsx"):
        raise HTTPException(400, "La PLANTILLA debe ser un .docx o .xlsx")

    if data_ext not in (".xls", ".xlsx", ".pdf", ".docx"):
        raise HTTPException(400, "DATA debe ser .xls, .xlsx, .pdf o .docx")

    # Guardar ambos en un dir temporal y generar salida
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)

        tpl_path  = td_path / tpl_file .filename
        data_path = td_path / data_file.filename
        out_path  = td_path / f"resultado{tpl_ext}"   # mismo sufijo que plantilla (.docx)

        for up, dest in ((tpl_file, tpl_path), (data_file, data_path)):
            with open(dest, "wb") as f: shutil.copyfileobj(up.file, f)
            await up.close()

        # orquestador ➜ genera out_path
        try:
            arch_orchestrator(tpl_path, data_path, out_path)
        except ValueError   as e: raise HTTPException(400,  str(e))
        except RuntimeError as e: raise HTTPException(500,  str(e))
        except Exception    as e:
            print("ERROR arch_orchestrator:", e)
            raise HTTPException(500, "Fallo interno al generar documento")

        if not out_path.exists():
            raise HTTPException(500, "El orquestador no generó salida")

        result_bytes = out_path.read_bytes()

    # envia resultado
    mime = ("application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            if tpl_ext == ".docx" else "application/pdf")

    return StreamingResponse(
        io.BytesIO(result_bytes),
        media_type=mime,
        headers={"Content-Disposition": f"attachment; filename=resultado{tpl_ext}"}
    )
