---
name: iran-web-ingress
description: Ultra-dense runbook for bypassing Iranian CDN geoblocking (*.111.ir.cdn.ir, Downloadly, Soft98) from outside Iran via domestic proxies, IDM split-tunneling, and UWP VPN quota reset.
---

# IRAN WEB INGRESS (HYPER-COMPRESSED)

**1. INGRESS VS OUTBOUND RULES:**
- `[BANS]:` NO Smart DNS (Shecan, 403.online, Begzar) for inbound access; outbound anti-sanction only.
- `[BANS]:` NO generic community VLESS/VMess lists (e.g. V2rayCollector); 99% are NIN egress reverse tunnels. Ingress foreign packets dropped (`503`, `wsarecv: closed`).
- `[BANS]:` NO token handoff; Iranian CDNs (`111.ir.cdn.ir`) validate IP continuity on every chunk.
- `[USE]:` Domestic Iranian ASN proxies (Mokhaberat, Abr Arvan, Asiatech). Raw sub: `https://raw.githubusercontent.com/therealaleph/Iran-configs/main/ir_configs.txt`.

**2. PROXY CONFLICT RESOLUTION:**
- **Chrome PAC Priority:** Chrome extension PAC overrides Windows WinINet. Set extensions to `Direct/Bypass` when using desktop proxies (`127.0.0.1:2080`).
- **Windows curl Invariant:** Always append `--ssl-no-revoke` with `curl.exe` to avoid `CRYPT_E_REVOCATION_OFFLINE`.
- **IDM Proxy Hijack Reset:**
  ```powershell
  Set-ItemProperty 'HKCU:\Software\DownloadManager' -Name UseHttpProxy -Value 0
  Set-ItemProperty 'HKCU:\Software\DownloadManager' -Name UseHttpsProxy -Value 0
  Set-ItemProperty 'HKCU:\Software\DownloadManager' -Name nProxyMode -Value 0
  Set-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings' -Name ProxyEnable -Value 0
  # WinINet flush: InternetSetOptionW(0, 39, 0, 0); InternetSetOptionW(0, 37, 0, 0)
  ```

**3. UWP VPN QUOTA BYPASS (IRAN IP VPN):**
- **Mechanism:** `device_info_plus_windows` binds server quota (`sampad.space`) to `HKLM:\SOFTWARE\Microsoft\Cryptography\MachineGuid`.
- **Reset:** `Set-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Cryptography' -Name MachineGuid -Value ([guid]::NewGuid().ToString())` (Admin).
- **No-Admin Bypass:** Run app on mobile/emulator $\rightarrow$ tether via Every Proxy (`192.168.1.X:8080`) to PC IDM.
- **Direct Cloud Bypass:** Paste final CDN link (`https://edge17.111.ir.cdn.ir/...`) into Seedr/Debrid $\rightarrow$ pull uncapped without Iranian proxy.
