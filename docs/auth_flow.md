# Auth Flow

Mercantil authentication is managed through Keycloak OAuth2.

Current lifecycle:

1. Use `MA_TOKEN` if available
2. On `401`, try `MA_REFRESH_TOKEN`
3. If refresh fails, login with `MA_USERNAME` + `MA_PASSWORD`

Implementation:

- `backend/integrations/auth/mercantil_auth.py`
