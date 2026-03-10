// Mejora de experiencia: luego de cada cambio HTMX, posiciona el flujo en pantalla.
document.addEventListener("DOMContentLoaded", () => {
  const contenedorFlujo = document.getElementById("flujo-cotizador");

  if (!contenedorFlujo) {
    return;
  }

  document.body.addEventListener("htmx:afterSwap", (evento) => {
    if (evento.detail.target && evento.detail.target.id === "flujo-cotizador") {
      contenedorFlujo.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  });
});
