# User Registration

New users create an account by providing their email, password, and selecting a role (user or worker). After registration, they are automatically logged in and redirected to chat.

**Persona:** New User

1. User clicks 'Register' link on the login page
2. Registration form appears with email, password, and role selection fields
3. User enters email, sets a password (minimum 6 characters), and selects role (user or worker)
4. User clicks 'Create account'
5. System creates the account with bcrypt-hashed password
6. User is automatically logged in and redirected to the Chat page
