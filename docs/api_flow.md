# API Flow

Core flow under construction:

1. User submits vehicle data
2. Backend validates and enriches inputs
3. Mercantil integrations resolve catalog, usos and coverages
4. Quote result is persisted and dispatched to operational channels

Current Mercantil integration entrypoint:

- `backend/integrations/mercantil_client.py`
