import { useCallback } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { getErrorMessage } from "../api/client";
import { listDatasets } from "../api/datasets";
import DatasetList from "../components/DatasetList";
import UploadForm from "../components/UploadForm";

export default function DatasetsPage() {
  const queryClient = useQueryClient();
  const datasetsQuery = useQuery({
    queryKey: ["datasets"],
    queryFn: listDatasets,
    // Keep the list fresh while any dataset is still being processed.
    refetchInterval: (query) => (query.state.data?.some((d) => d.status === "processing") ? 1000 : false),
  });

  const refreshList = useCallback(() => queryClient.invalidateQueries({ queryKey: ["datasets"] }), [queryClient]);

  return (
    <div className="stack">
      <div className="page-header">
        <h1>Datasets</h1>
        <p className="muted">Upload a sales CSV; it is cleaned, stored, and ready to explore.</p>
      </div>

      <UploadForm onUploadStarted={refreshList} onUploadFinished={refreshList} />

      <section className="card">
        <h2 className="card__title">Your datasets</h2>
        {datasetsQuery.isPending && <p className="muted">Loading…</p>}
        {datasetsQuery.isError && (
          <p className="alert alert--error" role="alert">
            {getErrorMessage(datasetsQuery.error, "Could not load datasets.")}
          </p>
        )}
        {datasetsQuery.data && <DatasetList datasets={datasetsQuery.data} />}
      </section>
    </div>
  );
}
