# 🥧 Lob Linter (Raspberry Pi Edition)

## Project Overview
This tool essentially "pre-flights" HTML to ensure that it is Lob-ready, highlighting styling inconsistencies or abnormalities that will break in our older legacy rendering engine as well as calling out any missing or incorrect asset links that will cause HTML to fail to render entirely.

## 🏗️ Tech Stack
* **Hardware:** Raspberry Pi 5 (8GB)
* **Backend:** Python 3 (Flask)
* **Linter Engine:** Node.js + TypeScript (PostCSS, Cheerio, Axios)
* **Persistence:** Systemd

## ⚡ Features
* **Strict CSS 2.1 Compliance:** Blocks modern CSS (Flexbox, Grid) that breaks legacy rendering engines.
* **Asset Validation:**
    * ✅ Blocks local file paths (e.g., `./image.png`).
    * ✅ Checks remote URLs (`http://...`) for 200 OK status.
    * ✅ Ignores Merge Variables in URLs (e.g., `{{name}}`).
* **API-First:** Simple REST API endpoint for easy integration.

## 🛠️ Installation

### 1. Prerequisites
Ensure you have `git`, `python3`, and `nvm` installed on your Raspberry Pi.

### 2. Setup
```bash
# Clone the repository
git clone https://github.com/lobstertroy/lob-linter.git
cd lob-linter

# Setup Python Environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Setup Node Environment
npm install
npx tsc  # Compile TypeScript worker
