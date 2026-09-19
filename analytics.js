// GA4 frontend tracking for GitHub Pages.
//
// Set the real Measurement ID in window.GA4_MEASUREMENT_ID before deployment.
// The placeholder intentionally sends no analytics data.

(() => {
  const id = window.GA4_MEASUREMENT_ID;
  if (!id || !/^G-[A-Z0-9]+$/i.test(id) || id === "G-XXXXXXXXXX") return;

  const script = document.createElement("script");
  script.async = true;
  script.src = `https://www.googletagmanager.com/gtag/js?id=${encodeURIComponent(id)}`;
  document.head.appendChild(script);

  window.dataLayer = window.dataLayer || [];
  window.gtag = function () { window.dataLayer.push(arguments); };
  window.gtag("js", new Date());
  window.gtag("config", id);

  window.track = function (eventName, params = {}) {
    window.gtag("event", eventName, params);
  };
})();
