#!/usr/bin/env python3
"""
Descarga robusta de archivos de fuente.

Dos trampas que ya nos costaron un workflow en rojo desde julio de 2026:

1. Los runners de GitHub Actions no tienen ruta IPv6: si el host resuelve a una
   AAAA, urllib intenta esa dirección y muere con [Errno 101] Network is
   unreachable. Forzamos resolución IPv4 mientras dura la descarga.

2. dataverse.nl está detrás de Anubis (desafío proof-of-work), que desafía a
   todo User-Agent que diga "Mozilla" y deja pasar al resto. Un UA de navegador
   devuelve 200 con una página HTML en vez del archivo. Por eso el UA NO debe
   imitar a un navegador, y por eso validamos los primeros bytes del archivo en
   vez de confiar en el código de estado.
"""
import os, socket, time, urllib.request

UA = "POPULI-datos/1.0 (+https://populi.org.bo)"  # sin "Mozilla": ver nota 2

_getaddrinfo_original = socket.getaddrinfo


def _solo_ipv4(host, port, family=0, type=0, proto=0, flags=0):
    return _getaddrinfo_original(host, port, socket.AF_INET, type, proto, flags)


def descargar(url, destino, magic=None, minimo=1024, intentos=3, espera=5):
    """Baja `url` a `destino` (escritura atómica). Devuelve la ruta.

    `magic`: bytes con que debe empezar el archivo (p. ej. b"PK\x03\x04" para
    un .xlsx). Si no coinciden, la respuesta no es el archivo aunque diga 200.
    """
    if magic is None and destino.lower().endswith((".xlsx", ".zip", ".docx")):
        magic = b"PK\x03\x04"
    socket.getaddrinfo = _solo_ipv4
    try:
        pedido = urllib.request.Request(url, headers={"User-Agent": UA})
        ultimo = None
        for intento in range(1, intentos + 1):
            try:
                with urllib.request.urlopen(pedido, timeout=180) as r:
                    contenido = r.read()
                if len(contenido) < minimo:
                    raise OSError(f"respuesta de {len(contenido)} bytes, muy corta")
                if magic and not contenido.startswith(magic):
                    raise OSError(
                        f"la respuesta no es el archivo esperado "
                        f"(empieza con {contenido[:16]!r}); "
                        f"¿la fuente puso un muro anti-bot delante?"
                    )
                tmp = destino + ".parcial"
                with open(tmp, "wb") as f:
                    f.write(contenido)
                os.replace(tmp, destino)
                print(f"  descargado: {len(contenido) // 1024} KB")
                return destino
            except Exception as e:
                ultimo = e
                print(f"  intento {intento}/{intentos} falló: {e}")
                if intento < intentos:
                    time.sleep(espera * intento)
        raise ultimo
    finally:
        socket.getaddrinfo = _getaddrinfo_original
