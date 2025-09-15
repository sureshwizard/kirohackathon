// src/App.tsx
import React from "react";
import { Routes, Route } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import Home from "./pages/Home";
import Dashboard from "./pages/Dashboard";
import Reports from "./pages/Reports";
import ImportPage from "./pages/Import";
import Users from "./pages/Users";
import Settings from "./pages/Settings";
import Chat from "./pages/Chat";
import UploadPreview from "./pages/UploadPreview";
import "./styles.css";

export default function App(): JSX.Element {
  return (
    <div className="app">
      <Sidebar />
      <main className="content">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/import" element={<ImportPage />} />
          <Route path="/users" element={<Users />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/upload" element={<UploadPreview />} />
        </Routes>
      </main>
    </div>
  );
}
