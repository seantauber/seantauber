# OAuth Setup Guide

## Adding Test Users

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Select the project
3. Go to "APIs & Services" > "OAuth consent screen"
4. Under "Test users" click "ADD USERS"
5. Enter the email address: {username}@gmail.com
6. Click "SAVE"

## Testing Configuration

The app should be in "Testing" mode with the following settings:

- Publishing status: Testing
- User Type: External
- Test users: {username}@gmail.com

## Local Development Setup

When running tests locally:
1. The system will try to use port 8029 for the OAuth callback
2. If port 8029 is in use, it will automatically try alternative ports (8030, 8031, etc.)
3. Configure the following redirect URIs in the OAuth consent screen:
   - http://localhost:8029
   - http://localhost:8030
   - http://localhost:8031
   - http://localhost:8032
   - http://localhost:8033
4. Use the test user account ({username}@gmail.com) when authenticating

## Port Conflict Resolution

If you encounter port conflicts:
1. The system will automatically try alternative ports
2. Make sure you've added the corresponding redirect URIs in Google Cloud Console
3. If all ports are in use, ensure no other OAuth flows are running
4. You may need to wait a few minutes for ports to be released

## Token Management

The system requires a refresh token for offline access. To ensure you get a refresh token:
1. Log out of all Google accounts before starting the OAuth flow
2. When prompted, ensure you see and accept the consent screen
3. If you still don't get a refresh token, delete the token file and try again

## Troubleshooting

If you see "Access blocked: Gmail Tool for LLM Assistant has not completed the Google verification process":
1. Ensure you're logged in with the test user account
2. The app must be in "Testing" mode
3. The test user must be added to the allowed test users list

If you see "You can't sign in to this app because it doesn't comply with Google's OAuth 2.0 policy":
1. Ensure the redirect URI shown in the error message matches one of the URIs configured in Google Cloud Console
2. If using an alternative port, make sure that port's redirect URI is configured
3. Check that you're using the correct OAuth 2.0 Client ID credentials
4. Verify that the application is properly configured in Testing mode

If you see "Address already in use":
1. The system will automatically try alternative ports
2. If all ports are exhausted, check for and close any running OAuth flows
3. Wait a few minutes and try again
4. Ensure the port range 8029-8033 is not being used by other applications
