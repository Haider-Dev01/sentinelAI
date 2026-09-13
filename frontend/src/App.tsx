import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { EvaluationPage } from "./pages/EvaluationPage";
import { ScanDetailPage } from "./pages/ScanDetailPage";
import { ScanListPage } from "./pages/ScanListPage";
import { TrendsPage } from "./pages/TrendsPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<EvaluationPage />} />
          <Route path="scans" element={<ScanListPage />} />
          <Route path="scans/:scanId" element={<ScanDetailPage />} />
          <Route path="trends" element={<TrendsPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
