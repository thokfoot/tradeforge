"use client";

import { useEffect } from "react";
import { initTauriNotifications } from "@/lib/tauri-notify";

export default function TauriNotifyInit() {
  useEffect(() => {
    initTauriNotifications();
  }, []);
  return null;
}
