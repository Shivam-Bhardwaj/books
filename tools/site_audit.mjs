#!/usr/bin/env node
/**
 * LLM-friendly site audit:
 * - starts a static server for `site/`
 * - renders key pages in Chromium (desktop + mobile)
 * - writes screenshots + a small JSON/MD report to `artifacts/site-audit/`
 */

import { spawn } from "node:child_process";
import { mkdir, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import process from "node:process";
import { chromium } from "playwright";

const ROOT = resolve(process.cwd());
const OUT_DIR = resolve(ROOT, "artifacts", "site-audit");
const BASE_URL = process.env.E2E_BASE_URL || "http://127.0.0.1:8788";

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

function startServer() {
  const child = spawn("python3", ["-m", "http.server", "8788", "--directory", "site"], {
    cwd: ROOT,
    stdio: "ignore",
  });

  const stop = async () => {
    if (child.killed) return;
    child.kill("SIGTERM");
    await sleep(150);
    child.kill("SIGKILL");
  };

  return { child, stop };
}

async function probePage(page, { name, path }) {
  const url = new URL(path, BASE_URL).toString();
  const warnings = [];

  const resp = await page.goto(url, { waitUntil: "domcontentloaded" });
  const status = resp?.status() ?? null;
  if (status && status >= 400) warnings.push(`HTTP ${status}`);

  await page.waitForLoadState("networkidle");

  const data = await page.evaluate(async () => {
    await document.fonts.ready;

    const title = document.title;
    const stylesheetHrefs = Array.from(document.querySelectorAll('link[rel="stylesheet"]')).map(
      (n) => n.getAttribute("href") || "",
    );
    const hasNovelCss = stylesheetHrefs.some((h) => h.includes("novel.css"));

    const fonts = {
      literata: document.fonts.check('12px "Literata"'),
      spaceGrotesk: document.fonts.check('12px "Space Grotesk"'),
    };

    const body = document.body;
    const cs = body ? getComputedStyle(body) : null;

    const links = Array.from(document.querySelectorAll("a"))
      .slice(0, 200)
      .map((a) => ({
        text: (a.textContent || "").trim().replace(/\s+/g, " ").slice(0, 120),
        href: a.getAttribute("href") || "",
      }));

    return {
      title,
      stylesheetHrefs,
      hasNovelCss,
      fonts,
      styles: cs
        ? {
            backgroundColor: cs.backgroundColor,
            color: cs.color,
            fontFamily: cs.fontFamily,
          }
        : null,
      links,
    };
  });

  if (!data.hasNovelCss && path.startsWith("/books/")) {
    warnings.push("novel.css not detected");
  }
  if (path === "/books/butterfly-effect/" || path === "/books/butterfly-effect") {
    if (!data.links.some((l) => l.href === "/#books")) warnings.push("Missing /#books link");
    if (!data.links.some((l) => l.href === "https://too.foo/")) warnings.push("Missing too.foo link");
  }
  if (data.fonts && (!data.fonts.literata || !data.fonts.spaceGrotesk)) {
    warnings.push("Fonts not loaded (Literata/Space Grotesk)");
  }

  return { name, path, url, status, ...data, warnings };
}

async function screenshot(page, outPath) {
  await page.screenshot({ path: outPath, fullPage: true });
}

async function main() {
  await mkdir(OUT_DIR, { recursive: true });

  const server = startServer();

  const audit = {
    baseUrl: BASE_URL,
    timestamp: new Date().toISOString(),
    pages: [],
    warnings: [],
  };

  try {
    const browser = await chromium.launch();
    try {
      const targets = [
        { name: "Home", path: "/" },
        { name: "Book (redirect)", path: "/butterfly-effect/" },
        { name: "TOC", path: "/books/butterfly-effect/" },
        { name: "Chapter 1", path: "/books/butterfly-effect/manuscript/arc-1/chapter-01.html" },
      ];

      const viewports = [
        { id: "desktop", viewport: { width: 1280, height: 720 } },
        { id: "mobile", viewport: { width: 390, height: 844 }, isMobile: true },
      ];

      const schemes = [
        { id: "light", colorScheme: "light" },
        { id: "dark", colorScheme: "dark" },
      ];

      for (const scheme of schemes) {
        for (const vp of viewports) {
          const context = await browser.newContext({
            viewport: vp.viewport,
            isMobile: Boolean(vp.isMobile),
            deviceScaleFactor: 2,
            colorScheme: scheme.colorScheme,
          });
          const page = await context.newPage();

          for (const t of targets) {
            const result = await probePage(page, t);
            const baseName = `${t.name.toLowerCase().replace(/[^a-z0-9]+/g, "-")}-${vp.id}-${scheme.id}`;
            const shotPath = resolve(OUT_DIR, `${baseName}.png`);
            await screenshot(page, shotPath);
            result.screenshots = result.screenshots || {};
            result.screenshots[`${vp.id}-${scheme.id}`] = shotPath;
            audit.pages.push({ viewport: vp.id, scheme: scheme.id, ...result });
            audit.warnings.push(
              ...result.warnings.map((w) => `${scheme.id}:${vp.id}:${t.path}: ${w}`),
            );
          }

          await context.close();
        }
      }
    } finally {
      await browser.close();
    }
  } catch (e) {
    audit.warnings.push(`Audit failed: ${String(e)}`);
  } finally {
    await server.stop();
  }

  const jsonPath = resolve(OUT_DIR, "site-audit.json");
  await writeFile(jsonPath, JSON.stringify(audit, null, 2), "utf-8");

  const mdLines = [];
  mdLines.push(`# Site Audit`);
  mdLines.push(``);
  mdLines.push(`- Timestamp: ${audit.timestamp}`);
  mdLines.push(`- Base URL: ${audit.baseUrl}`);
  mdLines.push(``);

  if (audit.warnings.length) {
    mdLines.push(`## Warnings`);
    for (const w of audit.warnings) mdLines.push(`- ${w}`);
    mdLines.push(``);
  }

  mdLines.push(`## Pages`);
  for (const p of audit.pages) {
    mdLines.push(`### ${p.name} (${p.viewport}, ${p.scheme})`);
    mdLines.push(`- Path: \`${p.path}\``);
    mdLines.push(`- Title: ${p.title ? `\`${p.title}\`` : "(none)"}`);
    mdLines.push(`- novel.css detected: ${p.hasNovelCss ? "yes" : "no"}`);
    mdLines.push(
      `- Fonts: Literata=${p.fonts?.literata ? "yes" : "no"}, SpaceGrotesk=${p.fonts?.spaceGrotesk ? "yes" : "no"}`,
    );
    mdLines.push(`- Body: bg=${p.styles?.backgroundColor || "?"}, fg=${p.styles?.color || "?"}`);

    const shot = p.screenshots?.[`${p.viewport}-${p.scheme}`];
    if (shot) {
      const rel = shot.replace(ROOT + "/", "");
      mdLines.push(``);
      mdLines.push(`![](${rel})`);
    }
    mdLines.push(``);
  }

  const mdPath = resolve(OUT_DIR, "site-audit.md");
  await writeFile(mdPath, mdLines.join("\n"), "utf-8");

  process.stdout.write(`Wrote ${mdPath.replace(ROOT + "/", "")}\n`);
  process.stdout.write(`Wrote ${jsonPath.replace(ROOT + "/", "")}\n`);
  if (audit.warnings.length) process.stdout.write(`Warnings: ${audit.warnings.length}\n`);
}

main().catch((e) => {
  process.stderr.write(String(e) + "\n");
  process.exit(1);
});
