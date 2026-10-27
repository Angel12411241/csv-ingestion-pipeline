import { Suspense, lazy } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import Layout from "./components/Layout";
import ProtectedRoute from "./components/ProtectedRoute";
import AuthPage from "./pages/AuthPage";
import DatasetsPage from "./pages/DatasetsPage";

// The detail page pulls in the charting library; load it only when needed.
const DatasetDetailPage = lazy(() => import("./pages/DatasetDetailPage"));

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<AuthPage mode="login" />} />
      <Route path="/register" element={<AuthPage mode="register" />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<Layout />}>
          <Route index element={<DatasetsPage />} />
          <Route
            path="/datasets/:id"
            element={
              <Suspense fallback={<p className="muted">Loading…</p>}>
                <DatasetDetailPage />
              </Suspense>
            }
          />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
