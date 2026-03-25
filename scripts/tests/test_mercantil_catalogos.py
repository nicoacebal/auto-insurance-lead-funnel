import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))
from backend.integrations.mercantil_client import MercantilClient

client = MercantilClient()

print("\n=== USOS ===")
print(client.obtener_usos())

print("\n=== MARCAS ===")
print(client.obtener_marcas())

print("\n=== ZONAS ===")
print(client.obtener_zonas())