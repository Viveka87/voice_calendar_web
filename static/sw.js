const CACHE_NAME = "voice-app-v1";

self.addEventListener("install", event => {
  console.log("Service Worker Installed");
});

self.addEventListener("fetch", event => {
  // basic fetch (no cache needed now)
});