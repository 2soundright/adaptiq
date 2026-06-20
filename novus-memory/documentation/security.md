# Security and Safety Features

## Security Architecture

AdaptIQ includes multiple layers of security to protect against misuse:

### Content Safety
- **LLM-based safety classifier** screens every query before processing
- Detects toxic language, harmful requests, jailbreak attempts, and prompt injection
- Blocked queries receive a polite refusal message in the user's language
- All safety blocks are logged to the encrypted audit trail with the original query and reason

### Prompt Injection Defense
- Known injection patterns (e.g., 'ignore previous instructions', 'system:', 'you are now') are stripped at the query transformation stage
- A regex-based filter removes injection phrases before they reach the retrieval system
- The safety classifier provides a second line of defense at the LLM level

### Encrypted Audit Logging
- All sensitive events are logged with **Fernet symmetric encryption**
- Payloads are encrypted before storage and decrypted only when viewed by admins
- Includes event type, user ID, toxic flag, timestamp, and full query details

### Authentication Security
- Passwords hashed with **bcrypt** (12 rounds)
- Company-scoped user isolation — users in different companies cannot access each other's data
- Role-based access control enforced at both the UI and data layer
