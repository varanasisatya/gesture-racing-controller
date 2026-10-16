# Security policy

## Scope

Gesture / Racing includes a public website, browser-side camera and hand tracking, a Windows desktop controller, and an optional loopback input bridge. The bridge can emit keyboard events to the currently focused application, so reports involving unintended input or access to the local bridge are especially important.

## Reporting a vulnerability

Please do not publish exploit details or personal camera footage in a public issue. Contact the repository owner privately through GitHub's security reporting feature when it is enabled, or ask for a private reporting channel before sharing sensitive details.

Include the affected component, steps to reproduce using a safe test setup, expected and actual behavior, and the impact. Do not test against other people's computers, accounts, games, or data.

## Security notes

- The local bridge is intended for one user's local Windows session and binds to `127.0.0.1`.
- The public website is allowlisted by origin; this is not per-device authentication.
- Never commit `.env` files, local `settings.json`, credentials, camera recordings, or generated environments.
- The visual login page is not an authentication system.
