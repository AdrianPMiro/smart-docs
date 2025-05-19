import React, { useState } from "react";
import "./App.css";

export default function App() {
  const [dataFile, setDataFile] = useState(null);
  const [tplFile, setTplFile] = useState(null);
  const [processing, setProcessing] = useState(false);

  const API = "http://localhost:8000";

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!dataFile || !tplFile) return alert("Selecciona DATA y PLANTILLA");

    const fd = new FormData();
    fd.append("data_file", dataFile);
    fd.append("tpl_file", tplFile);

    setProcessing(true);
    try {
      const r = await fetch(`${API}/api/process`, { method: "POST", body: fd });
      if (!r.ok) throw new Error((await r.json()).detail);

      // Obtener nombre de archivo desde headers
      const contentDisposition = r.headers.get('Content-Disposition');
      const filename = contentDisposition
        ? contentDisposition.split('filename=')[1].replace(/"/g, '')
        : `resultado${tplFile.name.slice(-5)}`; // Usar extensión de plantilla

      const blob = await r.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      alert(err.message || "Error");
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div className="container">
      <h1>
        <span className="gradient-text">Smart Docs Generator</span>
      </h1>

      <form onSubmit={handleSubmit} className="form">
        <div className="input-group">
          <label className="file-box">
            <input
              type="file"
              accept=".pdf,.xls,.xlsx,.docx"
              onChange={(e) => setDataFile(e.target.files[0] || null)}
            />
            <div className="custom-input">
              <span className="icon">📄</span>
              <span className="title">Seleccionar DATA</span>
              {dataFile && <span className="file-name">{dataFile.name}</span>}
            </div>
          </label>

          <label className="file-box">
            <input
              type="file"
              accept=".docx, .xlsx"
              onChange={(e) => setTplFile(e.target.files[0] || null)}
            />
            <div className="custom-input">
              <span className="icon">📁</span>
              <span className="title">Seleccionar PLANTILLA</span>
              {tplFile && (
                <span className="file-name">
                  {tplFile.name} ({tplFile.name.endsWith('.xlsx') ? 'Excel' : 'Word'})
                </span>
              )}
            </div>
          </label>
        </div>

        <button className="generate-btn" disabled={processing}>
          {processing ? (
            <div className="loader"></div>
          ) : (
            "GENERAR DOCUMENTO"
          )}
        </button>
      </form>
    </div>
  );
}