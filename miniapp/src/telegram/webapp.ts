export function telegram() {
  return window.Telegram?.WebApp;
}

export type Appearance = "telegram" | "light" | "dark";
const appearanceKey = "hisobchi-appearance";

export function getAppearance(): Appearance {
  try {
    const saved = window.localStorage.getItem(appearanceKey);
    return saved === "telegram" || saved === "dark" ? saved : "light";
  } catch {
    return "light";
  }
}

export function applyAppearance() {
  const preference = getAppearance();
  document.documentElement.dataset.theme =
    preference === "telegram"
      ? (telegram()?.colorScheme ??
        (window.matchMedia("(prefers-color-scheme: dark)").matches
          ? "dark"
          : "light"))
      : preference;
}

export function setAppearance(value: Appearance) {
  try {
    window.localStorage.setItem(appearanceKey, value);
  } catch {
    // Private browsing can disable storage; keep the selected theme for this view.
    document.documentElement.dataset.theme =
      value === "telegram" ? "light" : value;
    return;
  }
  applyAppearance();
}

export function initializeTelegram() {
  const app = telegram();
  app?.ready();
  app?.expand();
  const media = window.matchMedia("(prefers-color-scheme: dark)");
  applyAppearance();
  app?.onEvent("themeChanged", applyAppearance);
  media.addEventListener("change", applyAppearance);
  return () => {
    app?.offEvent("themeChanged", applyAppearance);
    media.removeEventListener("change", applyAppearance);
  };
}
