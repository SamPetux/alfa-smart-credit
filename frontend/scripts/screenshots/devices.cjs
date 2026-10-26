// Эмуляция устройств в Chromium (Playwright). Реальных устройств и других браузеров здесь нет:
// размер экрана, плотность пикселей, touch и user agent совпадают с профилями Playwright.
const { devices } = require("playwright");

const phone = (d) => ({ userAgent: devices[d].userAgent, mobile: true });

module.exports = {
  desktop: { dir: "desktop-1440x900", label: "Десктоп 1440×900", viewport: { width: 1440, height: 900 }, dpr: 1, tier: "full" },
  laptop: { dir: "laptop-1280x720", label: "Ноутбук 1280×720", viewport: { width: 1280, height: 720 }, dpr: 1, tier: "core" },
  ipad: {
    dir: "tablet-ipad-768x1024",
    label: "Планшет iPad, портрет 768×1024",
    viewport: { width: 768, height: 1024 },
    dpr: 2,
    tier: "full",
    ...phone("iPad (gen 7)"),
  },
  "ipad-landscape": {
    dir: "tablet-ipad-landscape-1024x768",
    label: "Планшет iPad, ландшафт 1024×768",
    viewport: { width: 1024, height: 768 },
    dpr: 2,
    tier: "core",
    ...phone("iPad (gen 7) landscape"),
  },
  iphone: {
    dir: "phone-iphone-390x844",
    label: "Телефон iPhone 390×844",
    viewport: { width: 390, height: 844 },
    dpr: 2,
    tier: "full",
    ...phone("iPhone 14"),
  },
  android: {
    dir: "phone-android-412x915",
    label: "Телефон Android (Pixel) 412×915",
    viewport: { width: 412, height: 915 },
    dpr: 2,
    tier: "core",
    ...phone("Pixel 7"),
  },
  "android-small": {
    dir: "phone-android-small-360x640",
    label: "Небольшой Android 360×640",
    viewport: { width: 360, height: 640 },
    dpr: 2,
    tier: "core",
    ...phone("Galaxy S5"),
  },
};
