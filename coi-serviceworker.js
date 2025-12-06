/*! coi-serviceworker v0.1.7 - Guido Zuidhof, licensed under MIT */
let coepCredentialless = false;
if (typeof window === 'undefined') {
  self.addEventListener("install", () => self.skipWaiting());
  self.addEventListener("activate", (event) => event.waitUntil(self.clients.claim()));

  self.addEventListener("message", (ev) => {
    if (!ev.data) {
      return;
    } else if (ev.data.type === "deregister") {
      self.registration.unregister();
    } else if (ev.data.type === "coepCredentialless") {
      coepCredentialless = ev.data.value;
    }
  });

  self.addEventListener("fetch", function (event) {
    const r = event.request;
    if (r.cache === "only-if-cached" && r.mode !== "same-origin") {
      return;
    }

    const request = (coepCredentialless && r.mode === "no-cors" && r.destination === "image")
      ? new Request(r, {
        credentials: "omit",
      })
      : r;
    event.respondWith(
      fetch(request)
        .then((response) => {
          if (response.status === 0) {
            return response;
          }

          const newHeaders = new Headers(response.headers);
          newHeaders.set("Cross-Origin-Embedder-Policy",
            coepCredentialless ? "credentialless" : "require-corp"
          );
          if (!coepCredentialless) {
             newHeaders.set("Cross-Origin-Resource-Policy", "cross-origin");
          }
          newHeaders.set("Cross-Origin-Opener-Policy", "same-origin");

          return new Response(response.body, {
            status: response.status,
            statusText: response.statusText,
            headers: newHeaders,
          });
        })
        .catch((e) => console.error(e))
    );
  });
} else {
  (() => {
    const reloadedBySelf = window.sessionStorage.getItem("coiReloadedBySelf");
    window.sessionStorage.removeItem("coiReloadedBySelf");
    const coepDegrading = (reloadedBySelf == "true");

    if (window.crossOriginIsolated) return;

    const script = document.querySelector('script[src*="coi-serviceworker"]');
    const src = script ? script.src : "coi-serviceworker.js";

    if ("serviceWorker" in navigator) {
      navigator.serviceWorker.register(src).then(
        (registration) => {
          console.log("COI Service Worker registered");
          registration.addEventListener("updatefound", () => {
            console.log("Reloading because COI Service Worker update found.");
            window.sessionStorage.setItem("coiReloadedBySelf", "true");
            window.location.reload();
          });

          if (registration.active && !navigator.serviceWorker.controller) {
            console.log("Reloading because COI Service Worker installed.");
            window.sessionStorage.setItem("coiReloadedBySelf", "true");
            window.location.reload();
          }
        },
        (err) => {
          console.error("COI Service Worker failed to register: ", err);
        }
      );
    }
  })();
}
