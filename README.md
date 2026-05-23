# admins — Admin Panel Finder & Redirect Detector

```
 █████╗ ██████╗ ███╗   ███╗██╗███╗   ██╗███████╗
██╔══██╗██╔══██╗████╗ ████║██║████╗  ██║██╔════╝
███████║██║  ██║██╔████╔██║██║██╔██╗ ██║███████╗
██╔══██║██║  ██║██║╚██╔╝██║██║██║╚██╗██║╚════██║
██║  ██║██████╔╝██║ ╚═╝ ██║██║██║ ╚████║███████║
╚═╝  ╚═╝╚═════╝ ╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚══════╝
        Admin Panel Finder & Redirect Detector
```

> **For authorized penetration testing and bug bounty use only.**
> Always obtain explicit written permission before scanning any target.

---

## What is `admins`?

`admins` is a fast, lightweight Python CLI tool that discovers exposed admin panels and login pages on a target domain. It probes hundreds of common paths and reports:

- **Accessible panels** — pages that return `200 OK`
- **Admin redirections** — paths that redirect (3xx) and where they lead
- **Protected endpoints** — pages returning `401 Unauthorized` or `403 Forbidden`
- **Server fingerprints** — detected web server headers

No external libraries required — runs on pure Python 3 stdlib.

---

## Requirements

- Python 3.6 or higher
- No external dependencies (uses `urllib`, `socket`, `concurrent.futures`)

---

## Installation

### Clone or download

```bash
https://github.com/tanvirahmedcs/admin-finder.git
cd admin-finder
```

### Make it a global command (Linux / macOS)

```bash
chmod +x admins.py
sudo cp admins.py /usr/local/bin/admins
```

Now you can run it from anywhere:

```bash
admins -d example.com
```

### Windows

```cmd
python admins.py -d example.com
```

---

## Usage

```
admins -d <domain> [options]
```

### Basic Examples

```bash
# Scan over HTTP (default)
python admins.py -d example.com

# Scan over HTTPS
python admins.py -d example.com --https

# Scan both HTTP and HTTPS
python admins.py -d example.com --both

# Save report to a file
python admins.py -d example.com --output report.txt

# Use a custom wordlist
python admins.py -d example.com -w wordlist.txt

# Faster scan with more threads
python admins.py -d example.com --threads 20

# Stealthy/slow scan (evade rate limiting)
python admins.py -d example.com --delay 1.0 --threads 3

# Show all results including 404s
python admins.py -d example.com --show-all
```

---

## Options

| Flag | Short | Default | Description |
|---|---|---|---|
| `--domain` | `-d` | *(required)* | Target domain, e.g. `example.com` |
| `--https` | | `False` | Use HTTPS instead of HTTP |
| `--both` | | `False` | Scan both HTTP and HTTPS |
| `--threads` | `-t` | `10` | Number of concurrent threads |
| `--timeout` | | `8` | Request timeout in seconds |
| `--delay` | | `0` | Delay between requests (seconds) |
| `--show-all` | | `False` | Show all results including 404s |
| `--output` | `-o` | None | Save report to a text file |
| `--wordlist` | `-w` | None | Custom wordlist (one path per line) |
| `--no-banner` | | `False` | Suppress the ASCII banner |

---

## Output Colour Key

| Colour | Meaning | Status Codes |
|---|---|---|
| 🟢 **Green** | Accessible admin panel | `200`, `201` |
| 🟡 **Yellow** | Redirect detected | `301`, `302`, `303`, `307`, `308` |
| 🔵 **Cyan** | Protected / auth required | `401`, `403` |
| 🔴 **Red** | Server errors or unexpected | `500`, `503`, etc. |
| ⬛ **Dim** | Not found | `404` |

---

## Redirect Detection

When a path responds with a 3xx redirect, `admins` captures the `Location` header and displays:

```
[302]  http://example.com/admin      → http://example.com/login?next=/admin
```

This is useful for:
- Mapping authentication flows
- Identifying login portals for exposed admin routes
- Detecting open redirects chained through admin paths

---

## Built-in Wordlist Coverage

The default wordlist contains **260+ paths** covering:

| Category | Examples |
|---|---|
| Generic admin | `/admin`, `/administrator`, `/admin_panel`, `/admin_area` |
| Login pages | `/login`, `/signin`, `/auth`, `/user/login` |
| Dashboards | `/dashboard`, `/backend`, `/backoffice`, `/portal` |
| WordPress | `/wp-admin`, `/wp-login.php` |
| Joomla | `/administrator/index.php` |
| Drupal | `/user/login` |
| Magento | `/index.php/admin` |
| Laravel | `/nova`, `/horizon`, `/telescope`, `/laravel-admin` |
| Django | `/django-admin`, `/admin/doc` |
| phpMyAdmin | `/phpmyadmin`, `/pma`, `/adminer.php` |
| Server panels | `/webmin`, `/cpanel`, `/plesk`, `/directadmin`, `/whm` |
| API endpoints | `/api/admin`, `/api/v1/admin`, `/rest/admin` |
| Misc | `/moderator`, `/staff`, `/superadmin`, `/config`, `/setup` |

---

## Custom Wordlist Format

Create a plain text file with one path per line. Lines starting with `#` are treated as comments and ignored.

```
# My custom wordlist
admin
admin/login
secret-admin
internal/dashboard
staff/panel
```

Run with:

```bash
python admins.py -d example.com -w my_wordlist.txt
```

---

## Sample Output

```
[*] Target   : http://example.com
[*] Paths    : 264
[*] Threads  : 10
[*] Timeout  : 8s
[*] Started  : 2024-11-01 14:32:00

──────────────────────────────────────────────────────────────────────
  STATUS   URL                                                INFO
──────────────────────────────────────────────────────────────────────
  200      http://example.com/admin/login.php                Server: Apache
  302      http://example.com/wp-admin                       → /wp-login.php
  403      http://example.com/phpmyadmin                     Forbidden 🚫
  401      http://example.com/admin/dashboard                Unauthorized 🔒

══════════════════════════════════════════════════════════════════════
  SCAN SUMMARY — example.com
══════════════════════════════════════════════════════════════════════

  [+] ACCESSIBLE ADMIN PANELS (1)
      ✓  [200]  http://example.com/admin/login.php

  [→] ADMIN REDIRECTIONS (1)
      →  [302]  http://example.com/wp-admin
           redirects to: http://example.com/wp-login.php

  [🔒] PROTECTED / AUTH REQUIRED (2)
      🔒  [403]  http://example.com/phpmyadmin
      🔒  [401]  http://example.com/admin/dashboard

  Total interesting findings: 4
  Finished: 2024-11-01 14:32:47
══════════════════════════════════════════════════════════════════════
```

---

## Performance Tips

| Goal | Recommended Settings |
|---|---|
| Fast internal scan | `--threads 30 --timeout 5` |
| Stealthy / evade WAF | `--threads 3 --delay 1.5` |
| Thorough external recon | `--threads 10 --timeout 10 --both` |
| Full visibility | `--show-all` |

---

## Use Cases

- **Bug bounty recon** — quickly map all admin surfaces in scope
- **Penetration testing** — identify authentication entry points
- **Security audits** — verify admin panels are not exposed publicly
- **CTF / lab environments** — locate hidden admin interfaces

---

## Legal Disclaimer

> This tool is provided for **educational and authorized security testing purposes only**.
>
> - Only use against targets you own or have **explicit written authorization** to test.
> - Unauthorized scanning is illegal under laws including the Computer Fraud and Abuse Act (CFAA), the Computer Misuse Act (CMA), and equivalents in your jurisdiction.
> - The author assumes no liability for misuse of this tool.
> - Always operate within the scope defined by your bug bounty program or penetration testing contract.

---

## Contributing

Pull requests are welcome. To add paths to the wordlist, edit the `ADMIN_PATHS` list in `admins.py` or submit a PR with a new category.

---

## License

MIT License — see `LICENSE` for details.
