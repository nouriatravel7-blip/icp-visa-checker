import puppeteer from "@cloudflare/puppeteer";

const ICP_URL =
  "https://smartservices.icp.gov.ae/echannels/web/client/default.html#/fileValidity";

const STEALTH_JS = `
  Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
  Object.defineProperty(navigator, 'plugins', { get: () => ({ length: 3 }) });
  Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
  window.chrome = { runtime: {}, loadTimes: function(){}, csi: function(){}, app: {} };
`;

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

export default {
  async fetch(request, env) {
    if (request.method !== "POST") {
      return Response.json({ error: "POST required" }, { status: 405 });
    }

    let body;
    try {
      body = await request.json();
    } catch {
      return Response.json({ error: "Invalid JSON body" }, { status: 400 });
    }

    const fileNo = (body.fileNo || "").trim();
    const dob = (body.dob || "").trim();

    if (!fileNo) {
      return Response.json({ error: "fileNo is required" }, { status: 400 });
    }

    let browser;
    try {
      browser = await puppeteer.launch(env.MYBROWSER);
      const page = await browser.newPage();

      await page.setUserAgent(
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
      );
      await page.setViewport({ width: 1366, height: 768 });
      await page.evaluateOnNewDocument(STEALTH_JS);

      // Navigate to ICP portal
      await page.goto(ICP_URL, { waitUntil: "domcontentloaded", timeout: 30000 });
      await page.waitForSelector("input[type='radio']", { timeout: 20000 });
      await sleep(2000);

      // Select "Emirate Unified Number" search mode
      const labels = await page.$$("label");
      for (const label of labels) {
        const text = await label.evaluate((el) => (el.innerText || "").toLowerCase());
        if (text.includes("emirate unified") || text.includes("unified number")) {
          await label.click();
          await sleep(1000);
          break;
        }
      }

      // Intercept the ICP API response
      let apiResponse = null;
      page.on("response", async (response) => {
        if (
          response.url().includes("fileValidityNew") &&
          response.status() === 200
        ) {
          try {
            apiResponse = await response.json();
          } catch (_) {}
        }
      });

      // Fill UID (the input without dd/mm placeholder)
      const inputs = await page.$$("input[type='text']");
      for (const input of inputs) {
        const visible = await input.evaluate((el) => {
          const s = window.getComputedStyle(el);
          return s.display !== "none" && s.visibility !== "hidden";
        });
        if (!visible) continue;
        const ph = await input.evaluate((el) =>
          (el.placeholder || "").toLowerCase()
        );
        if (!ph.includes("dd/") && !ph.includes("mm/")) {
          await input.click({ clickCount: 3 });
          await input.type(fileNo);
          break;
        }
      }

      // Fill DOB if provided
      if (dob) {
        const dobInputs = await page.$$("input[type='text']");
        for (const input of dobInputs) {
          const visible = await input.evaluate((el) => {
            const s = window.getComputedStyle(el);
            return s.display !== "none" && s.visibility !== "hidden";
          });
          if (!visible) continue;
          const ph = await input.evaluate((el) =>
            (el.placeholder || "").toLowerCase()
          );
          if (ph.includes("dd/") || ph.includes("mm/")) {
            await input.click({ clickCount: 3 });
            await input.type(dob);
            break;
          }
        }
      }

      await sleep(1000);

      // Click Search button
      const buttons = await page.$$("button");
      for (const btn of buttons) {
        const visible = await btn.evaluate((el) => {
          const s = window.getComputedStyle(el);
          return s.display !== "none" && s.visibility !== "hidden";
        });
        if (!visible) continue;
        const text = await btn.evaluate((el) =>
          (el.innerText || "").toLowerCase()
        );
        if (text.includes("search")) {
          await btn.click();
          break;
        }
      }

      // Wait up to 20s for ICP API response
      for (let i = 0; i < 20; i++) {
        if (apiResponse) break;
        await sleep(1000);
      }

      await browser.close();
      browser = null;

      if (!apiResponse) {
        return Response.json(
          { error: "Timeout: no response from ICP API", fileNo },
          { status: 504 }
        );
      }

      return Response.json(apiResponse);
    } catch (err) {
      if (browser) {
        await browser.close().catch(() => {});
      }
      return Response.json(
        { error: err.message || "Worker error", fileNo },
        { status: 500 }
      );
    }
  },
};
