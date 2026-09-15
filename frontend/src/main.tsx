import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import { FieldProvider } from "./state/FieldContext";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <FieldProvider>
        <App />
      </FieldProvider>
    </BrowserRouter>
  </React.StrictMode>
);
