import React, { useState, useCallback, useEffect } from "react";
import "./App.css";

export default function App() {
  const [dataFile, setDataFile]   = useState(null);
  const [tplFile,  setTplFile]    = useState(null);
  const [processing, setProcessing] = useState(false);
  const [isDraggingData, setIsDraggingData] = useState(false);
  const [isDraggingTpl,  setIsDraggingTpl]  = useState(false);

  const API = "http://127.0.0.1:8000";

  /* ---------- anti-brillo pegado ---------- */
  useEffect(() => {
    const clear = () => { setIsDraggingData(false); setIsDraggingTpl(false); };
    window.addEventListener("dragend", clear);
    window.addEventListener("drop",    clear);
    window.addEventListener("dragleave", clear);
    return () => {
      window.removeEventListener("dragend", clear);
      window.removeEventListener("drop",    clear);
      window.removeEventListener("dragleave", clear);
    };
  }, []);

  /* ---------- drag’n’drop ---------- */
  const handleDragOver = (e, t) => {
    e.preventDefault(); e.stopPropagation();
    if (t==="data"){ setIsDraggingData(true);  setIsDraggingTpl(false); }
    if (t==="tpl") { setIsDraggingTpl(true);   setIsDraggingData(false); }
  };
  const handleDragLeave = e => {
    e.preventDefault(); e.stopPropagation();
    setIsDraggingData(false); setIsDraggingTpl(false);
  };
  const handleDrop = useCallback((e,t)=>{
    e.preventDefault(); e.stopPropagation();
    const f=e.dataTransfer.files; if(!f.length) return;
    const file=f[0];
    const allowed = t==="data"
      ? ["application/pdf"]
      : ["application/vnd.openxmlformats-officedocument.wordprocessingml.document",
         "application/vnd.ms-excel"];
    if(!allowed.includes(file.type)){
      alert(`Formato no válido para ${t==="data"?"DATA":"PLANTILLA"}`);
      setIsDraggingData(false); setIsDraggingTpl(false);
      return;
    }
    t==="data"?setDataFile(file):setTplFile(file);
    setIsDraggingData(false); setIsDraggingTpl(false);
  },[]);

  /* ---------- submit ---------- */
const handleSubmit = async e => {
  e.preventDefault();
  console.log("[React] → handleSubmit disparado, dataFile:", dataFile?.name, "tplFile:", tplFile?.name);

  if (!dataFile || !tplFile) return alert("Selecciona DATA y PLANTILLA");
  const fd = new FormData();
  fd.append("data_file", dataFile);
  fd.append("tpl_file",  tplFile);

  setProcessing(true);
  try {
    console.log("[React] → A punto de hacer fetch a http://127.0.0.1:8000/api/process");
    const r = await fetch(`${API}/api/process`, { method:"POST", body:fd });
    console.log("[React] ← Fetch finalizado, r.ok=", r.ok);
    if (!r.ok) {
      const err = await r.json();
      throw new Error(err.detail || "Error servidor");
    }
    // … resto del código para descarga
    const disposition = r.headers.get('Content-Disposition');
    const filename = disposition
      ? disposition.split('filename=')[1].replace(/"/g, '')
      : `resultado${tplFile.name.slice(-5)}`;

    const blob = await r.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  } catch(err) {
    console.error("[React] → Error en fetch:", err);
    alert(err.message || "Error");
  } finally {
    setProcessing(false);
  }
};

  return(
    <div className="container">
      <h1><span className="gradient-text">Smart Docs Generator</span></h1>

      <form onSubmit={handleSubmit} className="form">
        <div className="file-upload-group">

          {/* DATA */}
          <label
            className={`file-upload-card ${isDraggingData?"dragging":""}`}
            onDragOver={e=>handleDragOver(e,"data")}
            onDragLeave={handleDragLeave}
            onDrop={e=>handleDrop(e,"data")}
            style={{cursor:"pointer"}}
            tabIndex={0}
          >
            {/* Por el momento solo se permite subir archivos .pdf para DATA */}
            <input
              type="file"
              accept=".pdf"
              style={{display:"none"}}
              onChange={e=>setDataFile(e.target.files[0]||null)}
            />
            <div className="file-upload-icon file-data">📄</div>
            <div className="file-upload-content">
              <span className="file-upload-title">DATA</span>
              {/* TODO: Añadir más archivos soportados: · .xls · .xlsx · .docx */}
              <span className="file-upload-badge">.pdf</span>
              <span className="file-upload-action">
                {isDraggingData?"Suelta el archivo aquí":"Seleccionar o arrastrar archivo"}
              </span>
              {dataFile&&<span className="file-upload-filename">{dataFile.name}</span>}
            </div>
          </label>

          {/* PLANTILLA */}
          <label
            className={`file-upload-card ${isDraggingTpl?"dragging":""}`}
            onDragOver={e=>handleDragOver(e,"tpl")}
            onDragLeave={handleDragLeave}
            onDrop={e=>handleDrop(e,"tpl")}
            style={{cursor:"pointer"}}
            tabIndex={0}
          >
            <input
              type="file"
              accept=".docx,.xls"
              style={{display:"none"}}
              onChange={e=>setTplFile(e.target.files[0]||null)}
            />
            <div className="file-upload-icon file-tpl">📁</div>
            <div className="file-upload-content">
              <span className="file-upload-title">PLANTILLA</span>
              <span className="file-upload-badge">.docx · .xls</span>
              <span className="file-upload-action">
                {isDraggingTpl?"Suelta el archivo aquí":"Seleccionar o arrastrar archivo"}
              </span>
              {tplFile&&<span className="file-upload-filename">{tplFile.name}</span>}
            </div>
          </label>
        </div>

        <button className="generate-btn" disabled={processing||!dataFile||!tplFile}>
          {processing?<div className="loader"></div>:"GENERAR DOCUMENTO"}
        </button>
      </form>
    </div>
  );
}
