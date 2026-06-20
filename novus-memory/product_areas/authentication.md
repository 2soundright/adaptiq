# Authentication

Handles user login, registration, and session management. Users authenticate with email and password, and are associated with a specific company. The system supports three roles (user, worker, admin) which determine access to different features and content collections. Passwords are securely hashed with bcrypt. On first launch, a default admin and regular user account are seeded automatically.

## Key Features

- Email and password login with bcrypt-hashed credential verification
- Self-service registration with role selection (user or worker)
- Role-based access control: user, worker, and admin roles
- Company-scoped authentication — users belong to a specific company
- Automatic session management with login persistence and logout
- Default admin and user accounts seeded on first database initialization
