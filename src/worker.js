"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const fs_1 = __importDefault(require("fs"));
const cheerio = __importStar(require("cheerio"));
const postcss_1 = __importDefault(require("postcss"));
const axios_1 = __importDefault(require("axios"));
const rules_1 = require("./rules");
const filePath = process.argv[2];
if (!filePath) {
    console.error("No file path provided");
    process.exit(1);
}
const htmlContent = fs_1.default.readFileSync(filePath, "utf8");
// load file and Cheerio
const $ = cheerio.load(htmlContent);
const errors = [];
const tasks = []; //store async jobs here
//regex to match url() values
const validateCss = async (cssSource, sourceName) => {
    try {
        const root = postcss_1.default.parse(cssSource);
        // --- A. Check Properties (Synchronous) ---
        root.walkDecls((decl) => {
            const property = decl.prop;
            const value = decl.value;
            if (!rules_1.safeList[property]) {
                errors.push(`Property '${property}' is not allowed in ${sourceName}`);
            }
            else {
                const allowed = rules_1.safeList[property];
                if (typeof allowed === "boolean" && allowed === true) {
                    return;
                }
                else if (Array.isArray(allowed)) {
                    if (!allowed.includes(value)) {
                        errors.push(`Value '${value}' is not allowed for '${property}' in ${sourceName}`);
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
    }
    catch (e) {
        console.error(`Failed to parse CSS from ${sourceName}`);
    }
};
async function validateUrl(url, sourceName) {
    if (!url)
        return;
    // 1. Ignore Merge Variables
    if (url.match(/^\{\{[\w.]+\}\}$/))
        return;
    // 2. Check Remote URLs
    if (url.startsWith("http://") || url.startsWith("https://")) {
        try {
            const res = await axios_1.default.head(url);
            if (res.status !== 200) {
                errors.push(`Error: Resource ${url} returned status ${res.status}`);
            }
        }
        catch (e) {
            const msg = e instanceof Error ? e.message : String(e);
            errors.push(`Network failure checking ${url}: ${msg}`);
        }
    }
    else {
        // 3. Fail on Local Paths
        errors.push(`Local resource '${url}' is not allowed in ${sourceName}`);
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
//# sourceMappingURL=worker.js.map