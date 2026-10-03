import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./app/App";
import { Providers } from "./app/providers";
import { applyAppearance } from "./telegram/webapp";
import "./style.css";
applyAppearance();
createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <Providers>
      <App />
    </Providers>
  </StrictMode>,
);
