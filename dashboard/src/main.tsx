import "@fontsource-variable/geist";
import "@ui-sdk/core/web.css";
import "./styles.css";

import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { App } from "./App";
import { ThemeProvider } from "./lib/theme";

const container = document.getElementById("root");
if (!container) {
  throw new Error("missing #root");
}

createRoot(container).render(
  <StrictMode>
    <ThemeProvider>
      <App />
    </ThemeProvider>
  </StrictMode>,
);
