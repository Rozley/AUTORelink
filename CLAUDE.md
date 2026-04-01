# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AUTORelink is a Tsinghua University campus network auto-reconnect tool for Windows. It monitors network connectivity and automatically re-authenticates when disconnected from the campus network (Srun4000 authentication).

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run monitoring (command-line mode)
python main.py

# Setup autostart via Task Scheduler (requires admin)
python setup_autostart.py install
python setup_autostart.py status
python setup_autostart.py remove

# Detect ac_id value (run when logged out of campus network)
python test_ac_id.py

# Test x_encode algorithm
python x_encode.py

# Run individual module tests
python campus_net.py   # Test login
python detector.py     # Test network detection
```

## Architecture

```
main.py           # Entry point, monitoring loop
campus_net.py     # CampusNetLogin class - core Srun authentication protocol
detector.py       # Network connectivity detection (ping, HTTP, TCP)
x_encode.py       # Srun4000 encryption algorithm (TEA variant)
config.py         # Configuration (credentials, servers, intervals)
setup_autostart.py# Task Scheduler autostart setup CLI
test_ac_id.py     # Utility to detect ac_id from redirect URLs
```

## Key Implementation Details

### Srun Authentication Flow
1. `detect_server_config()` - Detect auth server and ac_id from redirect
2. `get_challenge_with_ip()` - Fetch challenge token and server-visible IP
3. `_encrypt_password()` - HMAC-MD5 password encryption
4. `_calc_info()` - x_encode + custom Base64 encryption of login payload
5. `_calc_chksum()` - SHA1 checksum of authentication parameters
6. Login request to `/cgi-bin/srun_portal` with all parameters

### x_encode Algorithm (x_encode.py)
- TEA-like cipher implementation translated from JavaScript
- Key fixes: unsigned right shift (`>>>`), operator precedence, character encoding
- Custom Base64 alphabet: `LVoJPiCN2R8G90yg+hmFHuacZ1OWMnrsSTXkYpUq/3dlbfKwv6xztjI7DeBE45QA`

### Network Detection (detector.py)
- Primary: HTTP requests to CHECK_URL and baidu.com
- Secondary: ICMP ping to configurable hosts
- Tertiary: TCP port checks to auth servers
- `is_campus_net_connected()` - Distinguishes "needs re-login" vs "network down"

### Configuration (config.py)
- Credentials stored directly (no env var support)
- `AUTH_SERVER=None` enables auto-detection
- `AC_ID` must be set manually (found in redirect URL after login)

## Dependencies

- `requests>=2.28.0` - HTTP client
- `pywin32>=305` - Task Scheduler support
