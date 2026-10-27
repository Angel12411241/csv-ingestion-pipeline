import client from "./client";

export async function listDatasets() {
  const { data } = await client.get("/datasets");
  return data;
}

export async function getDataset(id, params) {
  const { data } = await client.get(`/datasets/${id}`, { params });
  return data;
}

export async function getDatasetStatus(id) {
  const { data } = await client.get(`/datasets/${id}/status`);
  return data;
}

/** Upload a CSV for background processing; resolves with `{ dataset_id, status, ... }`. */
export async function uploadDataset(file, { onUploadProgress } = {}) {
  const body = new FormData();
  body.append("file", file);
  const { data } = await client.post("/upload", body, {
    params: { async: true },
    onUploadProgress: (event) => {
      if (onUploadProgress && event.total) onUploadProgress(Math.round((event.loaded / event.total) * 100));
    },
  });
  return data;
}
