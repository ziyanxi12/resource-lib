import puppeteer from 'puppeteer';
import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'fs';
import { resolve, basename, join } from 'path';
import { pathToFileURL } from 'url';

const SEMANTIC_TAGS = new Set(['header', 'nav', 'aside', 'footer', 'main', 'section', 'article']);
const SKIP_TAGS = new Set(['HTML', 'BODY', 'HEAD', 'SCRIPT', 'STYLE', 'LINK', 'META', 'TITLE', 'BR', 'NOSCRIPT']);
const ROOT_IDS = new Set(['app', 'root', '__next', '__nuxt']);

function parseArgs() {
  const args = process.argv.slice(2);
  if (args.length < 2) {
    console.error('用法: node split.mjs <html-file> <json-coords|json-file> [output-dir]');
    process.exit(1);
  }
  const htmlPath = resolve(args[0]);
  let jsonCoords;
  try {
    jsonCoords = JSON.parse(args[1]);
  } catch {
    try {
      jsonCoords = JSON.parse(readFileSync(resolve(args[1]), 'utf-8'));
    } catch (e) {
      console.error('JSON 坐标解析失败，请传入 JSON 字符串或 JSON 文件路径');
      process.exit(1);
    }
  }
  if (!Array.isArray(jsonCoords)) {
    console.error('JSON 坐标必须是数组');
    process.exit(1);
  }
  for (let i = 0; i < jsonCoords.length; i++) {
    const c = jsonCoords[i];
    if (typeof c.x !== 'number' || typeof c.y !== 'number' || typeof c.w !== 'number' || typeof c.h !== 'number') {
      console.error(`第 ${i + 1} 项缺少 x/y/w/h 字段`);
      process.exit(1);
    }
  }
  const outputDir = args[2] ? resolve(args[2]) : resolve('./output');
  return { htmlPath, jsonCoords, outputDir };
}

async function splitHTML() {
  const { htmlPath, jsonCoords, outputDir } = parseArgs();

  if (!existsSync(htmlPath)) {
    console.error(`HTML 文件不存在: ${htmlPath}`);
    process.exit(1);
  }

  if (!existsSync(outputDir)) {
    mkdirSync(outputDir, { recursive: true });
  }

  console.log(`\n=== HTML 区块拆分 ===`);
  console.log(`HTML 文件: ${htmlPath}`);
  console.log(`区块数量: ${jsonCoords.length}`);
  console.log(`输出目录: ${outputDir}\n`);

  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  try {
    const page = await browser.newPage();
    await page.setViewport({ width: 1920, height: 1080 });

    const fileUrl = pathToFileURL(htmlPath).href;
    await page.goto(fileUrl, { waitUntil: 'networkidle0', timeout: 30000 });

    await new Promise(r => setTimeout(r, 2000));

    const pageW = await page.evaluate(() => document.documentElement.scrollWidth);
    const pageH = await page.evaluate(() => document.documentElement.scrollHeight);
    console.log(`页面尺寸: ${pageW}×${pageH}\n`);

    const results = await page.evaluate(async (coords) => {
      const SEMANTIC_TAGS = new Set(['header', 'nav', 'aside', 'footer', 'main', 'section', 'article']);
      const SKIP_TAGS = new Set(['HTML', 'BODY', 'HEAD', 'SCRIPT', 'STYLE', 'LINK', 'META', 'TITLE', 'BR', 'NOSCRIPT']);
      const ROOT_IDS = new Set(['app', 'root', '__next', '__nuxt']);

      function isSkipElement(el) {
        if (SKIP_TAGS.has(el.tagName)) return true;
        if (ROOT_IDS.has(el.id)) return true;
        const rect = el.getBoundingClientRect();
        if (rect.width === 0 && rect.height === 0) return true;
        return false;
      }

      function findElementCandidatesByCoordinates(doc, x, y, w, h) {
        const centerX = x + w / 2;
        const targetArea = w * h;
        const candidates = [];

        const allElements = doc.querySelectorAll('*');
        for (const el of allElements) {
          if (isSkipElement(el)) continue;

          const rect = el.getBoundingClientRect();
          const elArea = rect.width * rect.height;

          const overlapX = Math.max(0, Math.min(rect.right, x + w) - Math.max(rect.left, x));
          const overlapY = Math.max(0, Math.min(rect.bottom, y + h) - Math.max(rect.top, y));
          const overlapArea = overlapX * overlapY;

          if (overlapArea <= 0) continue;

          const coverageOfTarget = overlapArea / targetArea;
          const coverageOfElement = overlapArea / elArea;

          if (coverageOfTarget < 0.1 && coverageOfElement < 0.4) continue;

          const sizeSimilarity = Math.min(targetArea, elArea) / Math.max(targetArea, elArea);

          let score = coverageOfTarget * 0.5 + coverageOfElement * 0.3 + sizeSimilarity * 0.2;

          if (coverageOfTarget < 0.15) {
            score *= (coverageOfTarget / 0.15);
          }

          if (coverageOfElement >= 0.95) {
            score += 0.1;
          }

          candidates.push({
            el,
            rect,
            score,
            coverageOfTarget,
            coverageOfElement,
            sizeSimilarity
          });
        }

        const probeY = Math.min(y + h * 0.15, doc.defaultView.innerHeight - 10);
        const probeX = Math.min(Math.max(centerX, 10), doc.defaultView.innerWidth - 10);
        const probeEl = doc.elementFromPoint(probeX, probeY);
        if (probeEl) {
          let walker = probeEl;
          let blockAncestor = null;
          while (walker && !isSkipElement(walker)) {
            if (SEMANTIC_TAGS.has(walker.tagName.toLowerCase())) {
              blockAncestor = walker;
              break;
            }
            walker = walker.parentElement;
          }
          if (!blockAncestor) {
            blockAncestor = probeEl;
          }
          const found = candidates.find(c => c.el === blockAncestor);
          if (found) {
            found.score += 0.15;
          }
        }

        candidates.sort((a, b) => b.score - a.score);

        if (candidates.length > 0) {
          return candidates;
        }

        const centerY = y + h / 2;
        const centerEl = doc.elementFromPoint(
          Math.min(Math.max(centerX, 10), doc.defaultView.innerWidth - 10),
          Math.min(Math.max(centerY, 10), doc.defaultView.innerHeight - 10)
        );
        if (centerEl && !isSkipElement(centerEl)) {
          return [{
            el: centerEl,
            rect: centerEl.getBoundingClientRect(),
            score: 0,
            coverageOfTarget: 0,
            coverageOfElement: 0,
            sizeSimilarity: 0,
            fallback: true
          }];
        }

        return [];
      }

      function extractStyles(doc) {
        return Array.from(doc.querySelectorAll('head style')).map(s => s.outerHTML).join('\n');
      }

      function extractLinks(doc) {
        return Array.from(doc.querySelectorAll('head link[rel="stylesheet"]')).map(l => l.outerHTML).join('\n');
      }

      function extractHeadScripts(doc) {
        return Array.from(doc.querySelectorAll('head script[src]')).map(s => s.outerHTML).join('\n');
      }

      function buildStandaloneHTML(blockElement, doc) {
        const styles = extractStyles(doc);
        const links = extractLinks(doc);
        const headScripts = extractHeadScripts(doc);
        const bodyHTML = blockElement.outerHTML;
        const bodyScripts = Array.from(doc.querySelectorAll('body script')).map(s => s.outerHTML).join('\n');

        return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
${links}
${styles}
</head>
<body>
${bodyHTML}
${headScripts}
${bodyScripts}
</body>
</html>`;
      }

      const doc = document;
      const results = [];
      const usedElements = new Set();

      for (let i = 0; i < coords.length; i++) {
        const coord = coords[i];
        const candidates = findElementCandidatesByCoordinates(doc, coord.x, coord.y, coord.w, coord.h);

        let matchedEl = null;
        let matchedScore = 0;
        for (const candidate of candidates) {
          if (!usedElements.has(candidate.el)) {
            matchedEl = candidate.el;
            matchedScore = candidate.score;
            break;
          }
        }

        if (matchedEl) {
          usedElements.add(matchedEl);
          const html = buildStandaloneHTML(matchedEl, doc);
          const tag = matchedEl.tagName.toLowerCase();
          const cls = (matchedEl.className || '').toString().substring(0, 60);
          results.push({
            index: i,
            label: coord.name || coord.label || `区块 ${i + 1}`,
            matched: true,
            tag: tag,
            className: cls,
            score: Math.round(matchedScore * 1000) / 1000,
            x: coord.x,
            y: coord.y,
            w: coord.w,
            h: coord.h,
            html: html
          });
        } else {
          results.push({
            index: i,
            label: (coord.name || coord.label || `区块 ${i + 1}`) + ' (未匹配)',
            matched: false,
            tag: null,
            className: null,
            score: 0,
            x: coord.x,
            y: coord.y,
            w: coord.w,
            h: coord.h,
            html: ''
          });
        }
      }

      return results;
    }, jsonCoords);

    let successCount = 0;
    for (const result of results) {
      const safeName = (result.label || `block-${result.index}`).replace(/[^\w\u4e00-\u9fa5-]/g, '_');
      const fileName = `block-${result.index}-${safeName}.html`;
      const filePath = join(outputDir, fileName);

      if (result.matched) {
        writeFileSync(filePath, result.html, 'utf-8');
        successCount++;
        console.log(`  ✅ [${result.index}] ${result.label}`);
        console.log(`     匹配: <${result.tag}> .${result.className || ''}  (score: ${result.score})`);
        console.log(`     坐标: x:${result.x} y:${result.y} w:${result.w} h:${result.h}`);
        console.log(`     输出: ${fileName}`);
      } else {
        console.log(`  ❌ [${result.index}] ${result.label}`);
        console.log(`     坐标: x:${result.x} y:${result.y} w:${result.w} h:${result.h}`);
        console.log(`     未匹配到任何 DOM 元素`);
      }
      console.log('');
    }

    console.log(`=== 完成 ===`);
    console.log(`成功: ${successCount}/${results.length} 个区块`);
    console.log(`输出目录: ${outputDir}`);

    if (successCount < results.length) {
      process.exitCode = 1;
    }

  } finally {
    await browser.close();
  }
}

splitHTML().catch(err => {
  console.error('执行失败:', err.message);
  process.exit(1);
});
