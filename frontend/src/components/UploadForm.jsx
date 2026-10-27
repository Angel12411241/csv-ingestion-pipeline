import { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { getErrorMessage } from "../api/client";
import { getDatasetStatus, uploadDataset } from "../api/datasets";
import ProgressBar from "./ProgressBar";

const POLL_INTERVAL_MS = 500;

const isCsv = (file) => file.name.toLowerCase().endsWith(".csv");

/**
 * Upload a CSV, then poll the processing status until the backend finishes.
 * Phases: idle -> uploading -> processing -> done | error.
 */
export default function UploadForm({ onUploadStarted, onUploadFinished }) {
  const inputRef = useRef(null);
  const [file, setFile] = useState(null);
  const [phase, setPhase] = useState("idle");
  const [uploadProgress, setUploadProgress] = useState(0);
  const [datasetId, setDatasetId] = useState(null);
  const [error, setError] = useState(null);
  const [isDragging, setIsDragging] = useState(false);

  const statusQuery = useQuery({
    queryKey: ["dataset-status", datasetId],
    queryFn: () => getDatasetStatus(datasetId),
    enabled: phase === "processing" && datasetId != null,
    refetchInterval: (query) => (query.state.data?.status === "processing" ? POLL_INTERVAL_MS : false),
  });

  useEffect(() => {
    if (phase !== "processing") return;
    if (statusQuery.error) {
      setPhase("error");
      setError(getErrorMessage(statusQuery.error, "Lost track of the processing job."));
      return;
    }
    const status = statusQuery.data;
    if (status?.status === "completed") {
      setPhase("done");
      onUploadFinished?.(status.id);
    } else if (status?.status === "failed") {
      setPhase("error");
      setError(status.error_message || "Processing failed.");
      onUploadFinished?.(status.id);
    }
  }, [phase, statusQuery.data, statusQuery.error, onUploadFinished]);

  const busy = phase === "uploading" || phase === "processing";

  function selectFile(selected) {
    setError(null);
    setPhase("idle");
    if (selected && !isCsv(selected)) {
      setFile(null);
      setError("Please choose a .csv file.");
      return;
    }
    setFile(selected ?? null);
  }

  function handleDrop(event) {
    event.preventDefault();
    setIsDragging(false);
    if (!busy) selectFile(event.dataTransfer.files?.[0]);
  }

  async function handleSubmit(event) {
    event.preventDefault();
    if (!file || busy) return;
    setError(null);
    setUploadProgress(0);
    setPhase("uploading");
    try {
      const result = await uploadDataset(file, { onUploadProgress: setUploadProgress });
      setDatasetId(result.dataset_id);
      onUploadStarted?.(result.dataset_id);
      if (result.status === "completed") {
        setPhase("done");
        onUploadFinished?.(result.dataset_id);
      } else {
        setPhase("processing");
      }
    } catch (err) {
      setPhase("error");
      setError(getErrorMessage(err, "Upload failed."));
    }
  }

  function reset() {
    setFile(null);
    setPhase("idle");
    setDatasetId(null);
    setError(null);
    if (inputRef.current) inputRef.current.value = "";
  }

  return (
    <form className="card upload" onSubmit={handleSubmit} aria-label="Upload CSV">
      <h2 className="card__title">Upload sales CSV</h2>

      <label
        className={`dropzone${isDragging ? " dropzone--active" : ""}${busy ? " dropzone--disabled" : ""}`}
        onDragOver={(event) => {
          event.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".csv,text/csv"
          className="visually-hidden"
          aria-label="CSV file"
          disabled={busy}
          onChange={(event) => selectFile(event.target.files?.[0])}
        />
        <span className="dropzone__primary">{file ? file.name : "Choose a file or drag it here"}</span>
        <span className="dropzone__secondary">
          {file ? `${(file.size / 1024).toFixed(1)} KB` : "e.g. sales_data_sample.csv from Kaggle"}
        </span>
      </label>

      {phase === "uploading" && <ProgressBar value={uploadProgress} label="Uploading" />}
      {phase === "processing" && <ProgressBar value={statusQuery.data?.progress ?? 10} label="Processing" />}

      {phase === "done" && (
        <p className="alert alert--success" role="status">
          File processed successfully. <Link to={`/datasets/${datasetId}`}>View dataset →</Link>
        </p>
      )}
      {error && (
        <p className="alert alert--error" role="alert">
          {error}
        </p>
      )}

      <div className="upload__actions">
        {phase === "done" || phase === "error" ? (
          <button type="button" className="button button--secondary" onClick={reset}>
            Upload another
          </button>
        ) : null}
        <button type="submit" className="button" disabled={!file || busy || phase === "done"}>
          {busy ? "Working…" : "Upload"}
        </button>
      </div>
    </form>
  );
}
