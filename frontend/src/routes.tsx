import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Chat from "./pages/Chat";
import UploadPreview from "./pages/UploadPreview";

export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Chat />} />
        <Route path="/upload" element={<UploadPreview />} />
      </Routes>
    </Router>
  );
}
