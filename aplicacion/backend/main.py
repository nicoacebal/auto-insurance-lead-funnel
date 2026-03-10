"""Punto de entrada de la aplicacion FastAPI."""

from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .servicio_leads import guardar_lead

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
ANIO_MINIMO = 1980
ANIO_MAXIMO = 2035
VALOR_COTIZACION_SIMULADA = 47500

app = FastAPI(
    title="Landing de Cotizacion de Seguros de Autos",
    version="0.2.0",
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


def _formatear_moneda(valor: int) -> str:
    return f"${valor:,.0f}".replace(",", ".")


@app.get("/", response_class=HTMLResponse, tags=["Landing"])
async def mostrar_landing(request: Request) -> HTMLResponse:
    """Renderiza la pagina principal de captacion."""
    return templates.TemplateResponse("plantillas/landing.html", {"request": request})


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
) -> HTMLResponse:
    """Valida el paso de vehiculo y avanza al formulario de contacto."""
    datos_vehiculo = {
        "marca": _limpiar_texto(marca),
        "modelo": _limpiar_texto(modelo),
        "anio": _limpiar_texto(anio),
        "version": _limpiar_texto(version),
    }

    if not all(datos_vehiculo.values()):
        return templates.TemplateResponse(
            "componentes/formulario_vehiculo.html",
            {
                "request": request,
                **datos_vehiculo,
                "error": "Completa todos los datos del vehiculo para continuar.",
            },
        )

    try:
        anio_entero = int(datos_vehiculo["anio"])
    except ValueError:
        return templates.TemplateResponse(
            "componentes/formulario_vehiculo.html",
            {
                "request": request,
                **datos_vehiculo,
                "error": "El anio debe ser numerico.",
            },
        )

    if anio_entero < ANIO_MINIMO or anio_entero > ANIO_MAXIMO:
        return templates.TemplateResponse(
            "componentes/formulario_vehiculo.html",
            {
                "request": request,
                **datos_vehiculo,
                "error": f"El anio debe estar entre {ANIO_MINIMO} y {ANIO_MAXIMO}.",
            },
        )

    datos_vehiculo["anio"] = str(anio_entero)
    return templates.TemplateResponse(
        "componentes/formulario_contacto.html",
        {"request": request, **datos_vehiculo},
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
) -> HTMLResponse:
    """Valida contacto, guarda lead y devuelve cotizacion simulada."""
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

    if not all(datos_contacto.values()):
        return templates.TemplateResponse(
            "componentes/formulario_contacto.html",
            {
                "request": request,
                **datos_vehiculo,
                **datos_contacto,
                "error": "Completa todos tus datos de contacto.",
            },
        )

    if "@" not in datos_contacto["email"] or "." not in datos_contacto["email"]:
        return templates.TemplateResponse(
            "componentes/formulario_contacto.html",
            {
                "request": request,
                **datos_vehiculo,
                **datos_contacto,
                "error": "Ingresa un correo electronico valido.",
            },
        )

    precio_cotizado = VALOR_COTIZACION_SIMULADA
    try:
        anio_cotizado = int(datos_vehiculo["anio"])
    except ValueError:
        anio_cotizado = datos_vehiculo["anio"]

    # Si falla base de datos, el flujo continua y se muestra la cotizacion igualmente.
    resultado_guardado = guardar_lead(
        nombre=datos_contacto["nombre"],
        telefono=datos_contacto["telefono"],
        email=datos_contacto["email"],
        marca=datos_vehiculo["marca"],
        modelo=datos_vehiculo["modelo"],
        anio=anio_cotizado,
        version=datos_vehiculo["version"],
        precio_cotizado=precio_cotizado,
    )

    contexto_respuesta = {
        "request": request,
        **datos_vehiculo,
        **datos_contacto,
        "valor_cotizacion": _formatear_moneda(precio_cotizado),
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
