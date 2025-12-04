import fs from "fs";
import * as cheerio from "cheerio";
import postcss, { Root, Declaration } from "postcss";
import axios from "axios";
import { safeList } from "./rules";

const filePath = process.argv[2];

if (!filePath) {
  console.error("No file path provided");
  process.exit(1);
}

const htmlContent = fs.readFileSync(filePath, "utf8");
// load file and Cheerio
const $ = cheerio.load(htmlContent);

const errors: string[] = [];
const tasks: Promise<void>[] = []; //store async jobs here

//regex to match url() values

const validateCss = async (cssSource: string, sourceName: string) => {
  try {
    const root = postcss.parse(cssSource);

    // --- A. Check Properties (Synchronous) ---
    root.walkDecls((decl: Declaration) => {
      const property = decl.prop;
      const value = decl.value;

      if (!safeList[property]) {
        errors.push(`Property '${property}' is not allowed in ${sourceName}`);
      } else {
        const allowed = safeList[property];
        if (typeof allowed === "boolean" && allowed === true) {
          return;
        } else if (Array.isArray(allowed)) {
          if (!allowed.includes(value)) {
            errors.push(
              `Value '${value}' is not allowed for '${property}' in ${sourceName}`
            );
          }
        }
      }
    });

    // --- B. Check URLs (Asynchronous) ---
    const urlRegex = /url\((.*?)\)/gi;
    const matches = cssSource.matchAll(urlRegex);

    for (const match of Array.from(matches).values()) {
      let url = match[1]?.trim() ?? match[0].trim();
      url = url.replace(/^['"]|['"]$/g, '').trim();
      await validateUrl(url, sourceName);
    }
  } catch (e) {
    console.error(`Failed to parse CSS from ${sourceName}`);
  }
};

async function validateUrl(url: string, sourceName: string) {
  if (!url) return;

  // 1. Ignore Merge Variables
  if (url.match(/^\{\{[\w.]+\}\}$/)) return;

  // 2. Check Remote URLs
  if (url.startsWith("http://") || url.startsWith("https://")) {
    try {
      const res = await axios.head(url);
      if (res.status !== 200) {
        errors.push(`Error: Resource ${url} returned status ${res.status}`);
      }
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      errors.push(`Network failure checking ${url}: ${msg}`);
    }
  } else {
    // 3. Fail on Local Paths
    errors.push(
      `Local resource '${url}' is not allowed in ${sourceName}`
    );
  }
}

// check <style> tags
$("style").each((index, element) => {
  const css = $(element).html();
  if (css) {
    tasks.push(validateCss(css, `<style> tag #${index + 1}`));
  }
});

// check inline styles
const $selected = $("[style]");
$selected.each((index, element) => {
  const style = $(element).attr("style");
  if (style) {
    tasks.push(validateCss(style, `[style] attribute #${index + 1}`));
  }
});

$("img").each((index, element) => {
  const src = $(element).attr("src");
  if (src) {
    tasks.push(validateUrl(src, `<img src> #${index + 1}`));
  }
});

Promise.all(tasks).then(() => {
  console.log(JSON.stringify(errors));
});
