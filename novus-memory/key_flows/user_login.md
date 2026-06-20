# User Login

Existing users authenticate with their email and password to access the chat interface. The system validates credentials against the company-scoped user database.

**Persona:** All Users

1. User navigates to the AdaptIQ home page and sees the login form
2. User enters their email address and password
3. User clicks 'Log in'
4. System validates credentials against the company's user database (bcrypt hash comparison)
5. On success, user is redirected to the Chat page with sidebar navigation
6. On failure, an error message is displayed (e.g., 'Invalid email or password')
