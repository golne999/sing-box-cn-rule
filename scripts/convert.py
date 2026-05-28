#!/usr/bin/env python3
"""
Fetch remote geosite cn.json from MetaCubeX repository,
format domain suffixes to prepend a dot '.' (with exclusions),
merge with manual domains from source/manual.txt,
and output/compile sing-box ruleset files.
"""

import json
import subprocess
import sys
import ipaddress
import urllib.request
from pathlib import Path

REMOTE_URL = "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/sing/geo/geosite/cn.json"


def fetch_remote_rules():
    """Fetch remote geosite cn.json."""
    print(f"Fetching remote rules from {REMOTE_URL} ...")
    try:
        req = urllib.request.Request(
            REMOTE_URL, 
            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as e:
        print(f"❌ Error fetching remote rules: {e}")
        sys.exit(1)


def format_domain(domain):
    """Format domain suffix to prepend dot '.' unless it matches exclusions."""
    domain = domain.strip()
    if not domain:
        return None

    # 1. Already starts with a dot
    if domain.startswith('.'):
        return domain

    # 2. Wildcard domain starting with * or +
    if domain.startswith('*') or domain.startswith('+'):
        return domain

    # 3. IP address or CIDR
    try:
        ipaddress.ip_network(domain, strict=False)
        return domain
    except ValueError:
        pass

    # 4. Single-label TLD / brand domain (no dots at all)
    if '.' not in domain:
        return domain

    # Default: prepend dot
    return f".{domain}"


def parse_manual_line(line):
    """Parse a single line from manual.txt."""
    line = line.strip()
    if not line or line.startswith('#'):
        return None, None

    # Check if IP address or CIDR
    try:
        net = ipaddress.ip_network(line, strict=False)
        return "ip_cidr", str(net)
    except ValueError:
        pass

    # Check if suffix wildcard prefix
    if line.startswith('*.'):
        return "domain_suffix", line[2:]
    elif line.startswith('+.'):
        return "domain_suffix", line[2:]
    elif line.startswith('.'):
        return "domain_suffix", line
    else:
        return "domain", line


def load_manual_rules(path):
    """Load and parse manual rules from file."""
    result = {
        "domain": set(),
        "domain_suffix": set(),
        "ip_cidr": set()
    }
    if not path.exists():
        print(f"  ⚠️  Manual file not found at {path}, skipping")
        return result

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            category, val = parse_manual_line(line)
            if category:
                result[category].add(val)

    return result


def compile_singbox_srs(json_path, srs_path):
    """Compile sing-box JSON to binary SRS via sing-box CLI."""
    try:
        subprocess.run(
            ["sing-box", "rule-set", "compile", str(json_path), "-o", str(srs_path)],
            check=True, capture_output=True, text=True
        )
        print(f"  📦 Compiled: {srs_path}")
        return True
    except FileNotFoundError:
        print("  ⚠️  sing-box CLI not found, skipping .srs compilation")
        return False
    except subprocess.CalledProcessError as e:
        print(f"  ❌ sing-box compile error: {e.stderr.strip()}")
        return False


def main():
    root_dir = Path(__file__).resolve().parent.parent
    source_dir = root_dir / "source"
    singbox_dir = root_dir / "sing-box"
    singbox_dir.mkdir(exist_ok=True)

    # 1. Fetch remote rules
    remote_data = fetch_remote_rules()
    remote_suffixes = set()
    
    # Extract domain_suffix rules from fetched JSON
    for rule in remote_data.get("rules", []):
        for suffix in rule.get("domain_suffix", []):
            formatted = format_domain(suffix)
            if formatted:
                remote_suffixes.add(formatted)

    print(f"  Loaded {len(remote_suffixes)} remote domains (formatted)")

    # 2. Load manual rules
    manual_path = source_dir / "manual.txt"
    manual_rules = load_manual_rules(manual_path)
    print(f"  Loaded manual rules: {len(manual_rules['domain'])} domains, "
          f"{len(manual_rules['domain_suffix'])} suffixes, {len(manual_rules['ip_cidr'])} IPs")

    # 3. Merge rules
    merged_suffixes = remote_suffixes.union(manual_rules["domain_suffix"])
    merged_domains = manual_rules["domain"]
    merged_ips = manual_rules["ip_cidr"]

    # Build final sing-box ruleset structure
    rule = {}
    if merged_domains:
        rule["domain"] = sorted(list(merged_domains))
    if merged_suffixes:
        rule["domain_suffix"] = sorted(list(merged_suffixes))
    if merged_ips:
        rule["ip_cidr"] = sorted(list(merged_ips))

    ruleset = {
        "version": 2,
        "rules": [rule]
    }

    # 4. Write sing-box JSON
    out_json = singbox_dir / "cn.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(ruleset, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"  📄 Written: {out_json}")

    # 5. Compile to SRS
    out_srs = singbox_dir / "cn.srs"
    compile_singbox_srs(out_json, out_srs)

    print("\n✅ Rules generation completed successfully.")


if __name__ == "__main__":
    main()
