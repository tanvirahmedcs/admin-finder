#!/usr/bin/env python3
"""
admins - Admin Panel Finder & Redirect Detector
Usage: python admins.py -d example.com [options]

FOR AUTHORIZED PENETRATION TESTING AND BUG BOUNTY USE ONLY.
Always ensure you have explicit written permission before use.
"""

import argparse
import sys
import time
import socket
import concurrent.futures
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from urllib.parse import urlparse, urljoin

# ─────────────────────────────────────────────
# WORDLIST — common admin panel paths
# ─────────────────────────────────────────────
ADMIN_PATHS = [
    # Generic admin
    "admin", "admin/", "admin/login", "admin/login.php", "admin/login.html",
    "admin/index.php", "admin/index.html", "admin/dashboard", "admin/panel",
    "admin/control", "admin/cp", "admin/account", "admin/manage",
    "admin/admin", "admin/admin.php", "admin/admin.html",
    "admin_area", "admin_area/", "admin_area/login.php",
    "admin_panel", "admin_panel/", "admin_panel/login.php",
    "administration", "administration/", "administration/login.php",
    "administrator", "administrator/", "administrator/login.php",
    "administrator/index.php", "administrator/admin.php",

    # Login pages
    "login", "login/", "login.php", "login.html", "login.asp", "login.aspx",
    "signin", "sign-in", "sign_in",
    "auth", "auth/", "auth/login", "authenticate",
    "user/login", "users/login", "account/login", "accounts/login",
    "member/login", "members/login", "member-login",
    "panel", "panel/", "panel/login", "cpanel", "cpanel/",
    "controlpanel", "control-panel", "control_panel",

    # Dashboard variants
    "dashboard", "dashboard/", "dashboard/login",
    "backend", "backend/", "backend/login",
    "backoffice", "back-office", "backoffice/login",
    "manage", "manage/", "management", "management/login",
    "portal", "portal/", "portal/login",
    "secure", "secure/", "secure/login",
    "private", "private/", "private/login",

    # CMS & Framework specific
    "wp-admin", "wp-admin/", "wp-login.php",                      # WordPress
    "wp-admin/admin-ajax.php",
    "joomla/administrator", "administrator/index.php",             # Joomla
    "drupal/user/login", "user/login",                             # Drupal
    "magento/admin", "index.php/admin",                            # Magento
    "phpmyadmin", "phpmyadmin/", "phpMyAdmin", "phpMyAdmin/",      # phpMyAdmin
    "pma", "pma/",
    "phppgadmin", "phpPgAdmin",
    "adminer", "adminer.php",
    "laravel-admin", "nova", "horizon", "telescope",               # Laravel
    "django-admin", "admin/doc",                                    # Django
    "rails/admin", "rails_admin",                                   # Rails
    "console", "rails/console",

    # Server admin panels
    "webmin", "webmin/", ":10000",
    "plesk", "plesk/",
    "directadmin", "directadmin/",
    "whm", "whm/",
    "kloxo", "kloxo/",
    "zpanel", "zpanel/",
    "centos-webpanel", "cwp",
    "virtualmin", "virtualmin/",

    # API & misc
    "api/admin", "api/v1/admin", "api/v2/admin",
    "rest/admin",
    "moderator", "moderator/login",
    "mod", "mod/login",
    "staff", "staff/login",
    "superadmin", "superadmin/",
    "sysadmin", "sysadmin/",
    "root", "root/login",
    "webmaster", "webmaster/",
    "config", "config/",
    "setup", "setup/",
    "install", "install/",
    "maintenance",
]

# HTTP status code descriptions
STATUS_LABELS = {
    200: "OK ✓",
    201: "Created",
    301: "Moved Permanently →",
    302: "Found (Redirect) →",
    303: "See Other →",
    307: "Temporary Redirect →",
    308: "Permanent Redirect →",
    400: "Bad Request",
    401: "Unauthorized 🔒",
    403: "Forbidden 🚫",
    404: "Not Found",
    405: "Method Not Allowed",
    429: "Too Many Requests",
    500: "Server Error",
    503: "Service Unavailable",
}

# Colour codes (ANSI)
RED     = "\033[91m"
GREEN   = "\033[92m"
YELLOW  = "\033[93m"
CYAN    = "\033[96m"
BLUE    = "\033[94m"
MAGENTA = "\033[95m"
BOLD    = "\033[1m"
DIM     = "\033[2m"
RESET   = "\033[0m"


def color_status(code):
    if code in (200, 201):
        return f"{GREEN}{BOLD}{code}{RESET}"
    elif code in (301, 302, 303, 307, 308):
        return f"{YELLOW}{BOLD}{code}{RESET}"
    elif code in (401, 403):
        return f"{CYAN}{BOLD}{code}{RESET}"
    elif code == 404:
        return f"{DIM}{code}{RESET}"
    else:
        return f"{RED}{code}{RESET}"


def banner():
    print(f"""
{RED}{BOLD}
 █████╗ ██████╗ ███╗   ███╗██╗███╗   ██╗███████╗
██╔══██╗██╔══██╗████╗ ████║██║████╗  ██║██╔════╝
███████║██║  ██║██╔████╔██║██║██╔██╗ ██║███████╗
██╔══██║██║  ██║██║╚██╔╝██║██║██║╚██╗██║╚════██║
██║  ██║██████╔╝██║ ╚═╝ ██║██║██║ ╚████║███████║
╚═╝  ╚═╝╚═════╝ ╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚══════╝
{RESET}{CYAN}        Admin Panel Finder & Redirect Detector{RESET}
{DIM}        For authorized penetration testing only{RESET}
""")


def print_legal_warning():
    print(f"{YELLOW}{'─'*60}{RESET}")
    print(f"{YELLOW}{BOLD}  ⚠  LEGAL WARNING{RESET}")
    print(f"{YELLOW}{'─'*60}{RESET}")
    print(f"  This tool is for AUTHORIZED use only.")
    print(f"  Only run against targets you have EXPLICIT written")
    print(f"  permission to test (bug bounty scope / pentest contracts).")
    print(f"  Unauthorized use is illegal and unethical.")
    print(f"{YELLOW}{'─'*60}{RESET}\n")


def resolve_domain(domain):
    try:
        ip = socket.gethostbyname(domain)
        return ip
    except socket.gaierror:
        return None


def probe_url(url, timeout=8, follow_redirects=False):
    """
    Returns (status_code, final_url, redirect_chain, content_length, server_header)
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; AdminFinder/1.0; Bug-Bounty-Authorized)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    redirect_chain = []
    current_url = url

    try:
        req = Request(current_url, headers=headers)

        if follow_redirects:
            # Follow up to 5 redirects manually to capture chain
            for _ in range(5):
                try:
                    resp = urlopen(req, timeout=timeout)
                    final_url = resp.geturl()
                    content_length = resp.headers.get("Content-Length", "?")
                    server = resp.headers.get("Server", "")
                    return resp.status, final_url, redirect_chain, content_length, server
                except HTTPError as e:
                    return e.code, current_url, redirect_chain, "?", ""
        else:
            # Single probe, no redirect follow
            import urllib.request
            old_opener = urllib.request.build_opener(urllib.request.HTTPRedirectHandler())

            class NoRedirect(urllib.request.HTTPRedirectHandler):
                def redirect_request(self, req, fp, code, msg, headers, newurl):
                    redirect_chain.append(newurl)
                    return None  # Stop redirect

            opener = urllib.request.build_opener(NoRedirect())
            try:
                resp = opener.open(req, timeout=timeout)
                final_url = resp.geturl()
                content_length = resp.headers.get("Content-Length", "?")
                server = resp.headers.get("Server", "")
                return resp.status, final_url, redirect_chain, content_length, server
            except HTTPError as e:
                location = e.headers.get("Location", "")
                if location:
                    redirect_chain.append(location)
                return e.code, current_url, redirect_chain, "?", e.headers.get("Server", "")

    except URLError:
        return None, url, [], "?", ""
    except Exception:
        return None, url, [], "?", ""


def scan_target(domain, scheme, paths, threads, timeout, show_all, delay):
    results = {
        "found":     [],   # 200, 201
        "redirect":  [],   # 3xx
        "protected": [],   # 401, 403
        "other":     [],   # everything else non-404
        "errors":    [],
    }

    base = f"{scheme}://{domain}"
    total = len(paths)

    print(f"\n{BOLD}[*] Target   :{RESET} {CYAN}{base}{RESET}")
    print(f"{BOLD}[*] Paths    :{RESET} {total}")
    print(f"{BOLD}[*] Threads  :{RESET} {threads}")
    print(f"{BOLD}[*] Timeout  :{RESET} {timeout}s")
    print(f"{BOLD}[*] Started  :{RESET} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    print(f"{'─'*70}")
    print(f"  {'STATUS':<8} {'URL':<50} {'INFO'}")
    print(f"{'─'*70}")

    scanned = 0

    def check(path):
        url = f"{base}/{path.lstrip('/')}"
        code, final_url, chain, length, server = probe_url(url, timeout=timeout)
        return path, url, code, final_url, chain, length, server

    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        futures = {executor.submit(check, p): p for p in paths}
        for future in concurrent.futures.as_completed(futures):
            path, url, code, final_url, chain, length, server = future.result()
            scanned += 1

            if code is None:
                if show_all:
                    print(f"  {DIM}{'ERR':<8} {url}{RESET}")
                results["errors"].append(url)
                continue

            label = STATUS_LABELS.get(code, "")
            status_str = color_status(code)

            # Build info string
            info_parts = []
            if server:
                info_parts.append(f"Server: {server}")
            if length and length != "?":
                info_parts.append(f"Size: {length}B")
            if chain:
                info_parts.append(f"→ {chain[0]}")
            info = " | ".join(info_parts)

            url_display = url[:50] if len(url) > 50 else url

            if code in (200, 201):
                print(f"  {status_str:<17} {GREEN}{url_display:<50}{RESET} {info}")
                results["found"].append({"url": url, "code": code, "info": info, "redirect": chain})

            elif code in (301, 302, 303, 307, 308):
                redir_to = chain[0] if chain else final_url
                print(f"  {status_str:<17} {YELLOW}{url_display:<50}{RESET} → {redir_to}")
                results["redirect"].append({"url": url, "code": code, "redirect_to": redir_to, "chain": chain})

            elif code in (401, 403):
                print(f"  {status_str:<17} {CYAN}{url_display:<50}{RESET} {label}")
                results["protected"].append({"url": url, "code": code, "info": info})

            elif code != 404:
                if show_all:
                    print(f"  {status_str:<17} {url_display:<50} {label}")
                results["other"].append({"url": url, "code": code})

            else:
                if show_all:
                    print(f"  {DIM}{'404':<8} {url_display}{RESET}")

            if delay > 0:
                time.sleep(delay)

    return results


def print_summary(results, domain, output_file=None):
    lines = []

    lines.append(f"\n{'═'*70}")
    lines.append(f"  {BOLD}SCAN SUMMARY — {domain}{RESET}")
    lines.append(f"{'═'*70}")

    if results["found"]:
        lines.append(f"\n  {GREEN}{BOLD}[+] ACCESSIBLE ADMIN PANELS ({len(results['found'])}){RESET}")
        for r in results["found"]:
            lines.append(f"      {GREEN}✓{RESET}  [{r['code']}]  {r['url']}")

    if results["redirect"]:
        lines.append(f"\n  {YELLOW}{BOLD}[→] ADMIN REDIRECTIONS ({len(results['redirect'])}){RESET}")
        for r in results["redirect"]:
            lines.append(f"      {YELLOW}→{RESET}  [{r['code']}]  {r['url']}")
            lines.append(f"           redirects to: {r['redirect_to']}")

    if results["protected"]:
        lines.append(f"\n  {CYAN}{BOLD}[🔒] PROTECTED / AUTH REQUIRED ({len(results['protected'])}){RESET}")
        for r in results["protected"]:
            lines.append(f"      {CYAN}🔒{RESET}  [{r['code']}]  {r['url']}")

    if not results["found"] and not results["redirect"] and not results["protected"]:
        lines.append(f"\n  {DIM}No admin panels found.{RESET}")

    total_interesting = len(results["found"]) + len(results["redirect"]) + len(results["protected"])
    lines.append(f"\n  Total interesting findings: {BOLD}{total_interesting}{RESET}")
    lines.append(f"  Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"{'═'*70}\n")

    output = "\n".join(lines)
    print(output)

    if output_file:
        # Strip ANSI for file output
        import re
        clean = re.sub(r'\033\[[0-9;]*m', '', output)
        with open(output_file, "w") as f:
            f.write(f"admins scan — {domain}\n")
            f.write(f"Generated: {datetime.now()}\n\n")
            f.write(clean)
        print(f"  {GREEN}Report saved to:{RESET} {output_file}\n")


def main():
    parser = argparse.ArgumentParser(
        prog="admins",
        description="Admin Panel Finder & Redirect Detector — For authorized pentest/bug bounty use only",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""Examples:
  python admins.py -d example.com
  python admins.py -d example.com --https --threads 20
  python admins.py -d example.com --show-all --output report.txt
  python admins.py -d example.com --delay 0.5 --timeout 10
"""
    )
    parser.add_argument("-d", "--domain",   required=True,  help="Target domain (e.g. example.com)")
    parser.add_argument("--https",          action="store_true", default=False, help="Use HTTPS (default: HTTP)")
    parser.add_argument("--both",           action="store_true", default=False, help="Try both HTTP and HTTPS")
    parser.add_argument("--threads", "-t",  type=int, default=10,   help="Concurrent threads (default: 10)")
    parser.add_argument("--timeout",        type=int, default=8,    help="Request timeout in seconds (default: 8)")
    parser.add_argument("--delay",          type=float, default=0,  help="Delay between requests in seconds (default: 0)")
    parser.add_argument("--show-all",       action="store_true",    help="Show all results including 404s")
    parser.add_argument("--output", "-o",   type=str, default=None, help="Save report to file")
    parser.add_argument("--wordlist", "-w", type=str, default=None, help="Custom wordlist file (one path per line)")
    parser.add_argument("--no-banner",      action="store_true",    help="Suppress banner")

    args = parser.parse_args()

    if not args.no_banner:
        banner()

    print_legal_warning()

    # Resolve domain
    domain = args.domain.strip().lstrip("http://").lstrip("https://").rstrip("/")
    ip = resolve_domain(domain)
    if ip:
        print(f"  {DIM}Resolved {domain} → {ip}{RESET}")
    else:
        print(f"  {RED}[!] Could not resolve '{domain}' — check the domain and try again.{RESET}")
        sys.exit(1)

    # Load wordlist
    paths = list(ADMIN_PATHS)
    if args.wordlist:
        try:
            with open(args.wordlist) as f:
                custom = [line.strip() for line in f if line.strip() and not line.startswith("#")]
            paths = custom
            print(f"  {CYAN}[*] Custom wordlist loaded: {len(paths)} paths{RESET}")
        except FileNotFoundError:
            print(f"  {RED}[!] Wordlist file not found: {args.wordlist}{RESET}")
            sys.exit(1)

    # Determine schemes
    if args.both:
        schemes = ["http", "https"]
    elif args.https:
        schemes = ["https"]
    else:
        schemes = ["http"]

    all_results = {"found": [], "redirect": [], "protected": [], "other": [], "errors": []}

    for scheme in schemes:
        r = scan_target(
            domain=domain,
            scheme=scheme,
            paths=paths,
            threads=args.threads,
            timeout=args.timeout,
            show_all=args.show_all,
            delay=args.delay,
        )
        for k in all_results:
            all_results[k].extend(r[k])

    print_summary(all_results, domain, output_file=args.output)


if __name__ == "__main__":
    main()
