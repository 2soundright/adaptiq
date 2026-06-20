# Audit Logs

An admin-only security monitoring area that displays encrypted audit log entries. All sensitive events — particularly safety blocks on toxic or malicious queries — are logged with encrypted payloads using Fernet symmetric encryption. Admins can view decrypted log entries to monitor system security, review blocked queries, and identify problematic usage patterns.

## Key Features

- Last 20 audit log entries displayed with decrypted payloads
- Toxic/safe status badges for each log entry (red TOXIC vs green OK)
- Fernet-encrypted payload storage for security compliance
- Event type classification (e.g., safety_block events)
- User ID and timestamp tracking for each audit event
- Expandable detail view with full JSON payload for each entry
