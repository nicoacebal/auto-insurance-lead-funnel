import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from backend.integrations.mercantil_client import MercantilClient


print("Inicializando cliente Mercantil...")

client = MercantilClient()

print("Consultando usos de vehículos...")

usos = client.obtener_usos()

print("\nRespuesta recibida:\n")

for u in usos[:10]:
    print(u)