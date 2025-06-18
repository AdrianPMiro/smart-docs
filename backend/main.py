# backend/main.py

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import tempfile, shutil, io

from backend.services.arch_orchestrator import arch_orchestrator

app = FastAPI(title="Smart-Docs API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"status": "API OK"}

@app.post("/api/process")
async def process(
    data_file: UploadFile = File(...),
    tpl_file:  UploadFile = File(...)
):
    # -------------------------------------------------
    # 1) PRINT DE DEPURACIÓN: confirmar llegada de la petición
    print("\n[DEBUG] → LLEGÓ PETICIÓN A /api/process")
    print(f"[DEBUG] → data_file.filename = '{data_file.filename}'")
    print(f"[DEBUG] → tpl_file.filename  = '{tpl_file.filename}'")
    # -------------------------------------------------

    # Validar extensiones
    data_ext = Path(data_file.filename).suffix.lower()
    tpl_ext  = Path(tpl_file.filename).suffix.lower()
    if tpl_ext not in (".docx",):
        raise HTTPException(400, "La PLANTILLA debe ser .docx")
    if data_ext not in (".pdf",):
        raise HTTPException(400, "DATA debe ser .pdf")

    # Guardar en carpeta temporal
    with tempfile.TemporaryDirectory() as td:
        td_path   = Path(td)
        tpl_path  = td_path / tpl_file.filename
        data_path = td_path / data_file.filename
        out_path  = td_path / f"resultado{tpl_ext}"

        print("[DEBUG] → Tempdir:", td_path)
        print("[DEBUG] → tpl_path:", tpl_path)
        print("[DEBUG] → data_path:", data_path)

        for up_file, dest in ((tpl_file, tpl_path), (data_file, data_path)):
            print(f"[DEBUG] → Guardando '{up_file.filename}' en '{dest}'")
            with open(dest, "wb") as f:
                shutil.copyfileobj(up_file.file, f)
            await up_file.close()

        print("[DEBUG] → After save exists:", data_path.exists(), tpl_path.exists())
        if not data_path.exists() or not tpl_path.exists():
            raise HTTPException(500, "Error al guardar archivos temporales")

        # Llamar al orquestador
        try:
            print(f"[DEBUG] → llamando arch_orchestrator(datos='{data_path.name}', tpl='{tpl_path.name}', out='{out_path.name}')")
            result = arch_orchestrator(data_path, tpl_path, out_path)
            print("[DEBUG] ← arch_orchestrator devolvió:", result)
        except Exception as e:
            import traceback
            traceback.print_exc()
            # 2) Devuelve el mensaje completo al cliente (solo para depuración)
            raise HTTPException(500, f"Error interno (trace): {repr(e)}")
            print(f"[DEBUG] !!! arch_orchestrator lanzando excepción: {e}")
            raise HTTPException(500, f"Error interno: {e}")

        print("[DEBUG] → Compruebo if out_path existe:", out_path.exists())
        if not out_path.exists():
            raise HTTPException(500, "No se generó el archivo de salida")

        result_bytes = out_path.read_bytes()

    mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    print("[DEBUG] → Envío StreamingResponse con archivo:", out_path.name)
    return StreamingResponse(
        io.BytesIO(result_bytes),
        media_type=mime_type,
        headers={"Content-Disposition": f"attachment; filename={out_path.name}"}
    )
