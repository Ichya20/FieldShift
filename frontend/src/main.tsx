import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "@fontsource-variable/libre-franklin/index.css";
import "./styles/base.css";
import "./styles/hero.css";
import "./styles/sections.css";
import "./styles/scenario.css";
import "./styles/compare.css";
import "./styles/drawer.css";
import { App } from "./App";

createRoot(document.getElementById("root") as HTMLElement).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
