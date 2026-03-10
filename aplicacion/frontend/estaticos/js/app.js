// Mejora de experiencia y eventos de analitica basicos del cotizador.
document.addEventListener("DOMContentLoaded", () => {
  const contenedorFlujo = document.getElementById("flujo-cotizador");
  const indicadorTexto = document.getElementById("indicador-carga-texto");

  if (!contenedorFlujo) {
    return;
  }

  const registrarEvento = (nombre, metadata = {}) => {
    console.log(`[analytics] ${nombre}`, metadata);
  };

  const obtenerValoresOrigen = () => {
    const params = new URLSearchParams(window.location.search);
    return {
      utm_source: params.get("utm_source") || "",
      utm_medium: params.get("utm_medium") || "",
      utm_campaign: params.get("utm_campaign") || "",
      referrer: document.referrer || "",
      landing_page: window.location.href,
    };
  };

  const aplicarCamposOrigen = (scope = document) => {
    const origen = obtenerValoresOrigen();
    Object.entries(origen).forEach(([campo, valor]) => {
      scope.querySelectorAll(`input[data-origen="${campo}"]`).forEach((input) => {
        if (!input.value) {
          input.value = valor;
        }
      });
    });
  };

  const aplicarLimitesAnio = (scope = document) => {
    const anioActual = String(new Date().getFullYear());
    scope.querySelectorAll("input[name='anio']").forEach((input) => {
      input.setAttribute("max", anioActual);
      input.setAttribute("min", "1990");
    });
  };

  aplicarCamposOrigen(document);
  aplicarLimitesAnio(document);

  let cotizacionInicioRegistrada = false;

  document.body.addEventListener("click", (evento) => {
    const botonConEvento = evento.target.closest("[data-evento]");
    if (!botonConEvento) {
      return;
    }

    const nombreEvento = botonConEvento.getAttribute("data-evento");
    if (nombreEvento) {
      registrarEvento(nombreEvento, { ruta: window.location.pathname });
    }
  });

  document.body.addEventListener("htmx:beforeRequest", (evento) => {
    const elemento = evento.detail.elt;
    const formulario = elemento && elemento.closest ? elemento.closest("form") : null;
    if (!formulario) {
      return;
    }

    const paso = formulario.getAttribute("data-cotizador-step");
    const botonSubmit = formulario.querySelector("button[type='submit']");

    if (botonSubmit) {
      botonSubmit.disabled = true;
      botonSubmit.classList.add("boton-cargando");
    }

    if (indicadorTexto) {
      if (paso === "vehiculo") {
        indicadorTexto.textContent = "Calculando tu cotizacion...";
      } else if (paso === "pre-cotizacion") {
        indicadorTexto.textContent = "Preparando el siguiente paso...";
      } else if (paso === "contacto") {
        indicadorTexto.textContent = "Enviando tus datos...";
      } else {
        indicadorTexto.textContent = "Procesando paso...";
      }
    }

    if (paso === "vehiculo" && !cotizacionInicioRegistrada) {
      cotizacionInicioRegistrada = true;
      registrarEvento("cotizacion_inicio", { ruta: window.location.pathname });
    }
  });

  document.body.addEventListener("htmx:afterRequest", (evento) => {
    const elemento = evento.detail.elt;
    const formulario = elemento && elemento.closest ? elemento.closest("form") : null;
    if (!formulario) {
      return;
    }

    const botonSubmit = formulario.querySelector("button[type='submit']");
    if (botonSubmit) {
      botonSubmit.disabled = false;
      botonSubmit.classList.remove("boton-cargando");
    }
  });

  document.body.addEventListener("htmx:afterSwap", (evento) => {
    if (!evento.detail.target || evento.detail.target.id !== "flujo-cotizador") {
      return;
    }

    aplicarCamposOrigen(evento.detail.target);
    aplicarLimitesAnio(evento.detail.target);

    const pasoResultado = evento.detail.target.querySelector("#paso-resultado");
    if (pasoResultado) {
      registrarEvento("cotizacion_completada", { ruta: window.location.pathname });
    }

    contenedorFlujo.scrollIntoView({ behavior: "smooth", block: "start" });
  });
});
