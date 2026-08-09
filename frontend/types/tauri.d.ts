declare module "@tauri-apps/plugin-notification" {
  export interface NotificationOptions {
    title: string;
    body: string;
    icon?: string;
  }
  export function sendNotification(options: NotificationOptions): void;
  export function isPermissionGranted(): Promise<boolean>;
  export function requestPermission(): Promise<"granted" | "denied" | "default">;
}
