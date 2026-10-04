---
name: iran-web-ingress
description: >-
  Workflows, diagnostics, and protocol rules for accessing and downloading from
  geo-blocked Iranian websites (Downloadly, Soft98, P30Download, bank/gov portals)
  and Iranian CDNs (*.111.ir.cdn.ir, ArvanCloud) from outside Iran.
---

# Iranian Web Inbound Access & Geo-Fencing Runbook

## 1. Fundamental Distinction: Inbound vs. Outbound
- **Anti-Sanction Smart DNS (Shecan, 403.online, Begzar, Electro):**
  * ONLY works for outbound traffic from inside Iran to Western sites (Adobe, Docker, Google Cloud).
  * Does NOT grant a foreign user an Iranian IP address. Useless for accessing Iranian domestic sites from abroad.
- **Community V2Ray/VLESS Lists (e.g., V2rayCollector):**
  * 99% of public Iranian VLESS nodes are reverse-tunnels for people inside Iran to reach Europe/US.
  * Inbound connections from foreign IPs to these nodes are actively dropped by Iran's National Information Network (NIN) firewall (`503 Service Unavailable`, `wsarecv: forcibly closed`).
- **Domestic Iranian Proxies (Mokhaberat, Abr Arvan, Asiatech):**
  * Require dedicated nodes terminating inside Iranian ASNs.
  * Iranian CDNs validate IP continuity on every chunk; tokens cannot be handed off to foreign IPs.

## 2. Proxy Architecture & Isolation
- **Chrome Extension vs. System Proxy:**
  * Chrome extensions implementing `chrome.proxy` PAC scripts completely override Windows System Proxy (`127.0.0.1:2080`). Ensure extensions are set to `Direct / Bypass` when using desktop VPN/proxy clients.
- **Quota Bypass on UWP Iranian VPN Clients:**
  * Clients using `device_info_plus_windows` bind trial quotas to the Windows `MachineGuid` (`HKLM:\SOFTWARE\Microsoft\Cryptography\MachineGuid`).
  * Clearing local AppData/SQLite is insufficient if the server identifies the machine GUID. Use mobile tethering/Every Proxy bridge or cloud fetchers (Seedr) for unlimited high-volume downloads.
