import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import "./utils/axiosConfig"; // Initialize axios interceptors
import App from "./App.jsx";

// Note: StrictMode causes double-rendering in development to detect side effects
// All initialization guards (useRef) prevent duplicate API calls
console.log(
  "[MAIN] React StrictMode enabled - components will mount twice in dev",
);

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
