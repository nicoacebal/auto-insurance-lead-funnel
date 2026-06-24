import os

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

print("SUPABASE_URL:", SUPABASE_URL)
print("KEY loaded:", bool(SUPABASE_KEY))

print("Creando cliente...")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("Probando query simple...")

try:
    res = supabase.table("vehicle_catalog").select("id").limit(1).execute()

    print("Consulta OK")
    print(res)

except Exception as e:
    import traceback

    print("ERROR DE CONEXION")
    traceback.print_exc()
