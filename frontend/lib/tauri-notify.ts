import type { AlertNotification } from "./api";

let _ready = false;

async function tauriSend(title: string, body: string) {
  try {
    const { sendNotification } = await import("@tauri-apps/plugin-notification");
    sendNotification({ title, body });
  } catch {
    /* notifications unavailable */
  }
}

export async function initTauriNotifications() {
  if (_ready) return;
  _ready = true;
  try {
    const mod = await import("@tauri-apps/plugin-notification");
    const granted = await mod.isPermissionGranted();
    if (!granted) {
      const perm = await mod.requestPermission();
      if (perm !== "granted") return;
    }
  } catch {
    /* not in Tauri */
  }
}

export async function notifyAlert(n: AlertNotification) {
  await tauriSend(`Trade Forge Alert: ${n.symbol}`, n.message);
}

export async function notifyGeneric(title: string, body: string) {
  await tauriSend(title, body);
}
