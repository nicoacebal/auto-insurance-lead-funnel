"""Punto de entrada de la aplicacion FastAPI."""

from __future__ import annotations

import asyncio
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .servicio_leads import guardar_lead

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
ANIO_MINIMO = 1990
ANIO_MAXIMO = datetime.now().year
VALOR_COTIZACION_SIMULADA = 47500
WHATSAPP_NUMERO = "549XXXXXXXXX"
EMAIL_REGEX = re.compile(r"^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$", re.IGNORECASE)

app = FastAPI(
    title="Landing de Cotizacion de Seguros de Autos",
    version="0.4.0",
    description="Flujo inicial de cotizador con FastAPI, Jinja2 y HTMX.",
)

# Archivos estaticos de la landing.
app.mount(
    "/estaticos",
    StaticFiles(directory=FRONTEND_DIR / "estaticos"),
    name="estaticos",
)

# Se usa la carpeta frontend como raiz para separar plantillas y componentes.
templates = Jinja2Templates(directory=str(FRONTEND_DIR))


def _limpiar_texto(valor: str) -> str:
    return valor.strip()


def _limpiar_opcional(valor: str | None) -> str | None:
    if valor is None:
        return None
    valor_limpio = valor.strip()
    return valor_limpio or None


def _formatear_moneda(valor: int) -> str:
    return f"${valor:,.0f}".replace(",", ".")


def _correo_es_valido(email: str) -> bool:
    return EMAIL_REGEX.fullmatch(email) is not None


def _extraer_digitos(texto: str) -> str:
    return "".join(caracter for caracter in texto if caracter.isdigit())


def _crear_datos_origen(
    *,
    utm_source: str | None,
    utm_medium: str | None,
    utm_campaign: str | None,
    referrer: str | None,
    landing_page: str | None,
) -> dict[str, str | None]:
    return {
        "utm_source": _limpiar_opcional(utm_source),
        "utm_medium": _limpiar_opcional(utm_medium),
        "utm_campaign": _limpiar_opcional(utm_campaign),
        "referrer": _limpiar_opcional(referrer),
        "landing_page": _limpiar_opcional(landing_page),
    }


def _crear_link_whatsapp(
    *,
    marca: str,
    modelo: str,
    anio: str,
    valor_cotizacion: str,
) -> str:
    mensaje = (
        "Hola, acabo de cotizar un seguro en su sitio.\n\n"
        "Vehiculo:\n"
        f"{marca} {modelo} {anio}\n\n"
        "Precio estimado:\n"
        f"{valor_cotizacion}"
    )
    return f"https://wa.me/{WHATSAPP_NUMERO}?text={quote_plus(mensaje)}"


def _validar_datos_vehiculo(datos_vehiculo: dict[str, str]) -> str | None:
    if not all(datos_vehiculo.values()):
        return "Completa todos los datos del vehiculo para continuar."

    try:
        anio_entero = int(datos_vehiculo["anio"])
    except ValueError:
        return "Ingresa un anio valido para tu vehiculo."

    if anio_entero < ANIO_MINIMO or anio_entero > ANIO_MAXIMO:
        return f"El anio debe estar entre {ANIO_MINIMO} y {ANIO_MAXIMO}."

    return None


def _normalizar_datos_vehiculo(datos_vehiculo: dict[str, str]) -> dict[str, str]:
    datos = {**datos_vehiculo}
    datos["anio"] = str(int(datos["anio"]))
    return datos


@app.get("/", response_class=HTMLResponse, tags=["Landing"])
async def mostrar_landing(request: Request) -> HTMLResponse:
    """Renderiza la pagina principal de captacion."""
    contexto_origen = _crear_datos_origen(
        utm_source=request.query_params.get("utm_source"),
        utm_medium=request.query_params.get("utm_medium"),
        utm_campaign=request.query_params.get("utm_campaign"),
        referrer=request.headers.get("referer"),
        landing_page=str(request.url),
    )
    return templates.TemplateResponse(
        "plantillas/landing.html",
        {"request": request, **contexto_origen},
    )


@app.get("/cotizador/reiniciar", response_class=HTMLResponse, tags=["Cotizador"])
async def reiniciar_cotizador(request: Request) -> HTMLResponse:
    """Reinicia el flujo devolviendo el formulario del vehiculo."""
    return templates.TemplateResponse("componentes/formulario_vehiculo.html", {"request": request})


@app.post("/cotizador/paso-1", response_class=HTMLResponse, tags=["Cotizador"])
async def procesar_paso_vehiculo(
    request: Request,
    marca: str = Form(...),
    modelo: str = Form(...),
    anio: str = Form(...),
    version: str = Form(...),
    utm_source: str | None = Form(default=None),
    utm_medium: str | None = Form(default=None),
    utm_campaign: str | None = Form(default=None),
    referrer: str | None = Form(default=None),
    landing_page: str | None = Form(default=None),
) -> HTMLResponse:
    """Valida vehiculo y devuelve una pre-cotizacion estimada."""
    datos_vehiculo = {
        "marca": _limpiar_texto(marca),
        "modelo": _limpiar_texto(modelo),
        "anio": _limpiar_texto(anio),
        "version": _limpiar_texto(version),
    }
    datos_origen = _crear_datos_origen(
        utm_source=utm_source,
        utm_medium=utm_medium,
        utm_campaign=utm_campaign,
        referrer=referrer,
        landing_page=landing_page,
    )

    error = _validar_datos_vehiculo(datos_vehiculo)
    if error:
        return templates.TemplateResponse(
            "componentes/formulario_vehiculo.html",
            {
                "request": request,
                **datos_vehiculo,
                **datos_origen,
                "error": error,
            },
        )

    datos_vehiculo = _normalizar_datos_vehiculo(datos_vehiculo)

    # Simula calculo previo para mejorar percepcion de pre-cotizacion.
    await asyncio.sleep(1)

    return templates.TemplateResponse(
        "componentes/pre-cotizacion.html",
        {
            "request": request,
            **datos_vehiculo,
            **datos_origen,
            "valor_cotizacion": _formatear_moneda(VALOR_COTIZACION_SIMULADA),
        },
    )


@app.post("/cotizador/paso-1/contacto", response_class=HTMLResponse, tags=["Cotizador"])
async def avanzar_a_contacto(
    request: Request,
    marca: str = Form(...),
    modelo: str = Form(...),
    anio: str = Form(...),
    version: str = Form(...),
    utm_source: str | None = Form(default=None),
    utm_medium: str | None = Form(default=None),
    utm_campaign: str | None = Form(default=None),
    referrer: str | None = Form(default=None),
    landing_page: str | None = Form(default=None),
) -> HTMLResponse:
    """Pasa de la pre-cotizacion al formulario de contacto."""
    datos_vehiculo = {
        "marca": _limpiar_texto(marca),
        "modelo": _limpiar_texto(modelo),
        "anio": _limpiar_texto(anio),
        "version": _limpiar_texto(version),
    }
    datos_origen = _crear_datos_origen(
        utm_source=utm_source,
        utm_medium=utm_medium,
        utm_campaign=utm_campaign,
        referrer=referrer,
        landing_page=landing_page,
    )

    error = _validar_datos_vehiculo(datos_vehiculo)
    if error:
        return templates.TemplateResponse(
            "componentes/formulario_vehiculo.html",
            {
                "request": request,
                **datos_vehiculo,
                **datos_origen,
                "error": error,
            },
        )

    datos_vehiculo = _normalizar_datos_vehiculo(datos_vehiculo)

    return templates.TemplateResponse(
        "componentes/formulario_contacto.html",
        {
            "request": request,
            **datos_vehiculo,
            **datos_origen,
            "valor_cotizacion": _formatear_moneda(VALOR_COTIZACION_SIMULADA),
        },
    )


@app.post("/cotizador/paso-2", response_class=HTMLResponse, tags=["Cotizador"])
async def procesar_paso_contacto(
    request: Request,
    marca: str = Form(...),
    modelo: str = Form(...),
    anio: str = Form(...),
    version: str = Form(...),
    nombre: str = Form(...),
    telefono: str = Form(...),
    email: str = Form(...),
    utm_source: str | None = Form(default=None),
    utm_medium: str | None = Form(default=None),
    utm_campaign: str | None = Form(default=None),
    referrer: str | None = Form(default=None),
    landing_page: str | None = Form(default=None),
) -> HTMLResponse:
    """Valida contacto, guarda lead y muestra confirmacion final."""
    datos_vehiculo = {
        "marca": _limpiar_texto(marca),
        "modelo": _limpiar_texto(modelo),
        "anio": _limpiar_texto(anio),
        "version": _limpiar_texto(version),
    }
    datos_contacto = {
        "nombre": _limpiar_texto(nombre),
        "telefono": _limpiar_texto(telefono),
        "email": _limpiar_texto(email),
    }
    datos_origen = _crear_datos_origen(
        utm_source=utm_source,
        utm_medium=utm_medium,
        utm_campaign=utm_campaign,
        referrer=referrer,
        landing_page=landing_page,
    )

    error_vehiculo = _validar_datos_vehiculo(datos_vehiculo)
    if error_vehiculo:
        return templates.TemplateResponse(
            "componentes/formulario_vehiculo.html",
            {
                "request": request,
                **datos_vehiculo,
                **datos_origen,
                "error": error_vehiculo,
            },
        )

    if not all(datos_contacto.values()):
        return templates.TemplateResponse(
            "componentes/formulario_contacto.html",
            {
                "request": request,
                **_normalizar_datos_vehiculo(datos_vehiculo),
                **datos_contacto,
                **datos_origen,
                "valor_cotizacion": _formatear_moneda(VALOR_COTIZACION_SIMULADA),
                "error": "Completa todos tus datos de contacto.",
            },
        )

    if not _correo_es_valido(datos_contacto["email"]):
        return templates.TemplateResponse(
            "componentes/formulario_contacto.html",
            {
                "request": request,
                **_normalizar_datos_vehiculo(datos_vehiculo),
                **datos_contacto,
                **datos_origen,
                "valor_cotizacion": _formatear_moneda(VALOR_COTIZACION_SIMULADA),
                "error": "Ingresa un correo electronico valido.",
            },
        )

    if len(_extraer_digitos(datos_contacto["telefono"])) < 8:
        return templates.TemplateResponse(
            "componentes/formulario_contacto.html",
            {
                "request": request,
                **_normalizar_datos_vehiculo(datos_vehiculo),
                **datos_contacto,
                **datos_origen,
                "valor_cotizacion": _formatear_moneda(VALOR_COTIZACION_SIMULADA),
                "error": "Ingresa un telefono valido de al menos 8 digitos.",
            },
        )

    datos_vehiculo = _normalizar_datos_vehiculo(datos_vehiculo)
    anio_cotizado = int(datos_vehiculo["anio"])
    valor_cotizacion = _formatear_moneda(VALOR_COTIZACION_SIMULADA)

    ip_address = request.client.host if request.client else None
    user_agent = _limpiar_opcional(request.headers.get("user-agent"))

    # Se guarda el lead unicamente cuando el usuario completa sus datos de contacto.
    resultado_guardado = guardar_lead(
        nombre=datos_contacto["nombre"],
        telefono=datos_contacto["telefono"],
        email=datos_contacto["email"],
        marca=datos_vehiculo["marca"],
        modelo=datos_vehiculo["modelo"],
        anio=anio_cotizado,
        version=datos_vehiculo["version"],
        precio_cotizado=VALOR_COTIZACION_SIMULADA,
        utm_source=datos_origen["utm_source"],
        utm_medium=datos_origen["utm_medium"],
        utm_campaign=datos_origen["utm_campaign"],
        referrer=datos_origen["referrer"],
        landing_page=datos_origen["landing_page"],
        ip_address=_limpiar_opcional(ip_address),
        user_agent=user_agent,
    )

    contexto_respuesta = {
        "request": request,
        **datos_vehiculo,
        **datos_contacto,
        **datos_origen,
        "valor_cotizacion": valor_cotizacion,
        "whatsapp_url": _crear_link_whatsapp(
            marca=datos_vehiculo["marca"],
            modelo=datos_vehiculo["modelo"],
            anio=str(anio_cotizado),
            valor_cotizacion=valor_cotizacion,
        ),
    }
    if not resultado_guardado.exito and resultado_guardado.mensaje:
        contexto_respuesta["aviso_guardado"] = resultado_guardado.mensaje

    return templates.TemplateResponse(
        "componentes/resultado_cotizacion.html",
        contexto_respuesta,
    )


@app.get("/salud", tags=["Sistema"])
async def salud() -> dict[str, str]:
    """Endpoint simple para verificar disponibilidad."""
    return {"estado": "ok"}
