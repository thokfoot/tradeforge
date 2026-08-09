"use client";

import { useEffect } from "react";

export default function PwaRegister() {
  useEffect(() => {
    if ("serviceWorker" in navigator) {
      // In development: unregister any existing service workers to prevent caching
      if (process.env.NODE_ENV !== "production") {
        navigator.serviceWorker.getRegistrations().then(async (registrations) => {
          await Promise.all(registrations.map((registration) => registration.unregister()));
          if ("caches" in window) {
            const keys = await caches.keys();
            await Promise.all(keys.map((key) => caches.delete(key)));
          }
          if (registrations.length > 0 && !sessionStorage.getItem("tf_dev_sw_cleared")) {
            sessionStorage.setItem("tf_dev_sw_cleared", "1");
            window.location.reload();
          }
        });
        return;
      }
      navigator.serviceWorker.register("/sw.js").catch(() => {
        /* offline registration not supported (e.g. dev) */
      });
    }
  }, []);
  return null;
}
