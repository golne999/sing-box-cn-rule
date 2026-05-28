# sing-box-cn-rule

A project to generate a unified CN routing rule-set for sing-box by merging the upstream remote `cn.json` domain list with your custom manual list.

## Features

1. **Auto Dot Formatting**: All domains scraped from upstream `cn.json` are formatted to start with a dot `.` (e.g., `baidu.com` -> `.baidu.com`) to match both the domain and its subdomains.
2. **Exclusion Rules**: The following formats are automatically excluded from dot-formatting (they are kept as-is):
   - IP addresses or CIDRs.
   - Domains already starting with a dot `.`.
   - Wildcard domains starting with `*` or `+`.
   - Single-label TLDs / brand domains that do not contain any dots (e.g., `cn`, `taobao`, `baidu`, `alipay`).
3. **Manual Rules**: You can add your custom rules in `source/manual.txt`.
4. **Auto compilation**: Compiles to sing-box binary rule-set format (`.srs`) automatically.

## Directory Structure

* `source/`: Contains raw rule files.
  * `manual.txt`: Place your custom domains/IPs here.
* `sing-box/`: Output directory.
  * `cn.json` / `cn.srs`
* `scripts/`: Conversion utility scripts.
  * `convert.py`: Fetches remote JSON, merges with manual list, formats, and compiles.

## How to use

1. Modify your custom rules in `source/manual.txt`.
2. Run `convert.py` to regenerate outputs:
   ```bash
   python3 scripts/convert.py
   ```
