import requests

url = "https://productos.mercantilandina.com.ar/api_integracion_productos/vehiculos/marca-modelo"

headers = {
    "Authorization": "Bearer eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJrdWZCUUlJM24zbDczR1ZOQmRLNDRfTUsyLTlOWms3SmdZUEtqdHFZRDZVIn0.eyJleHAiOjE3NzM0NjEyNTQsImlhdCI6MTc3MzQ2MDk1NCwianRpIjoiODFjNDUyM2YtODUwMi00OGU5LWE4NmUtOGQ0ZTJmNjFkYzI1IiwiaXNzIjoiaHR0cHM6Ly9pZG0ubWVyY2FudGlsYW5kaW5hLmNvbS5hci9hdXRoL3JlYWxtcy9tZXJhbiIsImF1ZCI6ImFjY291bnQiLCJzdWIiOiJmOjVkZTllMWEzLTFmYmMtNDZhNC04ZjU2LTVhMWJkY2RkMzI1NjpESUVaREFOIiwidHlwIjoiQmVhcmVyIiwiYXpwIjoic2lnbWEiLCJzaWQiOiJiMDI1NjgxMy1hMjgzLTRjYjQtYjk0NC0yOTNmMGQ5MmE0NTQiLCJhY3IiOiIxIiwiYWxsb3dlZC1vcmlnaW5zIjpbImh0dHA6Ly9sb2NhbGhvc3Q6ODA4MCIsImh0dHA6Ly9iYWlzd2FzZDI6OTA4MCIsImh0dHA6Ly9sb2NhbGhvc3Q6OTA4MC8qIiwiaHR0cHM6Ly9zZXJ2aWNpb3MubWVyY2FudGlsYW5kaW5hLmNvbS5hciIsImh0dHA6Ly9iYWlzd2FzZDI6OTA4MC8qIl0sInJlYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJvZmZsaW5lX2FjY2VzcyIsImFzZWd1cmFkbyIsInByb3ZlZWRvciIsInVtYV9hdXRob3JpemF0aW9uIiwicHJvZHVjdG9yIl19LCJyZXNvdXJjZV9hY2Nlc3MiOnsiYWNjb3VudCI6eyJyb2xlcyI6WyJtYW5hZ2UtYWNjb3VudCIsIm1hbmFnZS1hY2NvdW50LWxpbmtzIiwidmlldy1wcm9maWxlIl19fSwic2NvcGUiOiJvcGVuaWQgcHJvZmlsZSBlbWFpbCIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJuaWNrbmFtZSI6IkRJRVpEQU4iLCJuYW1lIjoiREFOSUVMIFJPQkVSVE8gRElFWiIsInByZWZlcnJlZF91c2VybmFtZSI6IkRJRVpEQU4iLCJlbWFpbCI6IkRJRVouT1JHQU5JWkFDSU9OQEdNQUlMLkNPTSJ9.bpxtTpAQ6OExBjT2D6ItVmhNq-heiM771yHV9ubwom6GOdpAt5cvHbeDU2Xozjw8sKQy8Lmv--bDx94S3R_IMrES9AfM9Xb5KqE8IiTh3c5MJ3JmQOyTsIMVRLVVw39Q4nkqX3OlPWU6wgVdOGSGSV5iyU3XWWT2_FfEzrOdoNFVHOJj1N8oT_bulx1wtyxhPEaklaB4wofPuLjZ6J8GdV6214loewMsR6HcXNSJUJnGQVWSeTIVjJlbJvFX2X4N1Vijk7uht75F0LlY1jZ_yAgipGntoyeUCjT-rj8vz1rou6f2AfqjckEKbwKTqNkG6fziFkbdGWb770j_vVVX-Q",
    "Ocp-Apim-Subscription-Key": "8cb15b592fe74272bb73ac1cd5cc3d2e",
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://servicios.mercantilandina.com.ar",
    "Referer": "https://servicios.mercantilandina.com.ar/",
    "User-Agent": "Mozilla/5.0"
}

params = {
    "descripcion": "VOL",
    "fabricado": "2025",
    "page": 0,
    "size": 5000,
    "tipo": "1;2;3;8;9;21;4;5;6;17",
    "conValor": "false"
}

r = requests.get(url, headers=headers, params=params)

print("STATUS:", r.status_code)
print(r.text[:500])
