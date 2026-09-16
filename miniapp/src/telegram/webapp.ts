export function telegram() {
  return window.Telegram?.WebApp;
}
export function initializeTelegram() {
  const app = telegram();
  app?.ready();
  app?.expand();
  const theme = () => {
    document.documentElement.dataset.theme =
      app?.colorScheme ??
      (window.matchMedia("(prefers-color-scheme: dark)").matches
        ? "dark"
        : "light");
  };
  theme();
  app?.onEvent("themeChanged", theme);
  return () => app?.offEvent("themeChanged", theme);
}
