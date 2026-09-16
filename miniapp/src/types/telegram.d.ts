export {};
declare global {
  interface Window {
    Telegram?: {
      WebApp: {
        ready(): void;
        expand(): void;
        initData: string;
        colorScheme: "light" | "dark";
        onEvent(event: string, callback: () => void): void;
        offEvent(event: string, callback: () => void): void;
        BackButton: {
          show(): void;
          hide(): void;
          onClick(callback: () => void): void;
          offClick(callback: () => void): void;
        };
      };
    };
  }
  interface ImportMetaEnv {
    readonly VITE_API_URL?: string;
    readonly VITE_DEV_AUTH?: string;
    readonly DEV: boolean;
  }
  interface ImportMeta {
    readonly env: ImportMetaEnv;
  }
}
