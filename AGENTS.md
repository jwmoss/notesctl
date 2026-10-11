# Agent instructions

Run `make check` for static checks and package validation.
Run `make test` for real Apple Notes reads when database access is available.
Report missing database access as unverified.
Keep only live end-to-end tests and static checks. Do not add unit or mock tests.
Preserve read-only access to Apple Notes. Never write to the source database.
Use feature branches and pull requests.
