#!/usr/bin/env python3
"""Descarga archivos Parquet del NYC TLC Trip Record Data para 2024 y 2026.

Descarga los registros de viajes de taxis amarillos (yellow) y verdes (green)
correspondientes a los anios configurados para el laboratorio.

Fuente oficial de los datos:
    https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page

Uso:
    python scripts/download_data.py                 # amarillos y verdes
    python scripts/download_data.py --year 2024
    python scripts/download_data.py --year 2024 2026 --taxi yellow
    python scripts/download_data.py --taxi yellow
    python scripts/download_data.py --taxi green

Los archivos se guardan en:
    data/raw/<tipo>/<anio>/<nombre-original>.parquet

Comportamiento:
  - El script consulta que meses estan publicados en lugar de suponerlos.
  - Un archivo que ya existe localmente no se vuelve a descargar.
  - La descarga se hace sobre un nombre temporal y solo se renombra al
    terminar, de modo que una interrupcion no deja archivos .parquet a medias.
"""

import argparse
import sys
from pathlib import Path

import requests

ANIOS = (2024, 2026)
TIPOS_TAXI = ("yellow", "green")
URL_BASE = "https://d37ci6vzurychx.cloudfront.net/trip-data"
DIR_DESTINO = Path("data/raw")

TIEMPO_ESPERA = 60          # segundos por peticion
INTENTOS = 3                # intentos por archivo antes de darse por vencido
BLOQUE = 1024 * 1024        # 1 MiB por bloque de descarga
SUFIJO_TEMPORAL = ".part"


def construir_nombre(tipo: str, anio: int, mes: int) -> str:
    """Nombre del archivo publicado por la TLC, p. ej. yellow_tripdata_2024-01.parquet."""
    return f"{tipo}_tripdata_{anio}-{mes:02d}.parquet"


def construir_url(tipo: str, anio: int, mes: int) -> str:
    """URL completa del archivo Parquet mensual."""
    return f"{URL_BASE}/{construir_nombre(tipo, anio, mes)}"


def ruta_destino(tipo: str, anio: int, mes: int) -> Path:
    """Ruta local donde se guarda el archivo."""
    return DIR_DESTINO / tipo / str(anio) / construir_nombre(tipo, anio, mes)


def esta_publicado(url: str) -> bool:
    """Indica si el archivo existe en el servidor (sin descargarlo)."""
    ultimo_error = None
    for intento in range(1, INTENTOS + 1):
        try:
            respuesta = requests.head(
                url, timeout=TIEMPO_ESPERA, allow_redirects=True
            )
            # CloudFront responde 403 o 404 para meses aun no publicados.
            if respuesta.status_code in (403, 404):
                return False
            if respuesta.ok:
                return True
            respuesta.raise_for_status()
            raise requests.RequestException(
                f"respuesta HTTP inesperada: {respuesta.status_code}"
            )
        except requests.RequestException as error:
            ultimo_error = error
            if intento < INTENTOS:
                print(
                    f"      consulta HEAD {intento}/{INTENTOS} fallida "
                    f"({error}); reintentando"
                )

    raise requests.RequestException(
        f"no se pudo consultar la disponibilidad de {url}: {ultimo_error}"
    )


def formato_tamanio(n: float) -> str:
    for unidad in ("B", "KiB", "MiB", "GiB"):
        if n < 1024 or unidad == "GiB":
            return f"{n:.1f} {unidad}"
        n /= 1024
    return f"{n:.1f} GiB"


def descargar_archivo(url: str, destino: Path) -> int:
    """Descarga `url` en `destino`. Devuelve la cantidad de bytes escritos."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporal = destino.with_name(destino.name + SUFIJO_TEMPORAL)

    ultimo_error = None
    for intento in range(1, INTENTOS + 1):
        try:
            with requests.get(url, stream=True, timeout=TIEMPO_ESPERA) as respuesta:
                respuesta.raise_for_status()
                encabezado_longitud = respuesta.headers.get("Content-Length")
                longitud_esperada = None
                if encabezado_longitud is not None:
                    try:
                        longitud_esperada = int(encabezado_longitud)
                    except ValueError as error:
                        raise requests.RequestException(
                            f"Content-Length invalido: {encabezado_longitud}"
                        ) from error
                escritos = 0
                with temporal.open("wb") as archivo:
                    for bloque in respuesta.iter_content(chunk_size=BLOQUE):
                        if bloque:
                            archivo.write(bloque)
                            escritos += len(bloque)
            if escritos == 0:
                raise requests.RequestException("el servidor devolvio un archivo vacio")
            if longitud_esperada is not None and escritos != longitud_esperada:
                raise requests.RequestException(
                    f"descarga incompleta: se esperaban {longitud_esperada} bytes "
                    f"y se recibieron {escritos}"
                )
            temporal.replace(destino)
            return escritos
        except requests.RequestException as error:
            ultimo_error = error
            temporal.unlink(missing_ok=True)
            if intento < INTENTOS:
                print(f"      intento {intento}/{INTENTOS} fallido ({error}); reintentando")

    raise requests.RequestException(f"no se pudo descargar {url}: {ultimo_error}")


def descargar(tipo: str, anio: int) -> dict:
    """Descarga todos los meses publicados de un tipo de taxi para un año."""
    print(f"\n=== {tipo.upper()} {anio} ===")
    resumen = {"descargados": 0, "omitidos": 0, "no_publicados": [], "fallidos": []}

    for mes in range(1, 13):
        etiqueta = f"{anio}-{mes:02d}"
        destino = ruta_destino(tipo, anio, mes)

        if destino.exists() and destino.stat().st_size > 0:
            print(f"  {etiqueta}  ya existe, se omite")
            resumen["omitidos"] += 1
            continue

        url = construir_url(tipo, anio, mes)
        try:
            publicado = esta_publicado(url)
        except requests.RequestException as error:
            print(f"  {etiqueta}  ERROR al consultar disponibilidad: {error}")
            resumen["fallidos"].append(etiqueta)
            continue

        if not publicado:
            print(f"  {etiqueta}  aun no publicado por la TLC")
            resumen["no_publicados"].append(etiqueta)
            continue

        print(f"  {etiqueta}  descargando...")
        try:
            escritos = descargar_archivo(url, destino)
        except requests.RequestException as error:
            print(f"  {etiqueta}  ERROR: {error}")
            resumen["fallidos"].append(etiqueta)
        else:
            print(f"  {etiqueta}  listo ({formato_tamanio(escritos)}) -> {destino}")
            resumen["descargados"] += 1

    return resumen


def main() -> int:
    parser = argparse.ArgumentParser(
        description=f"Descarga los datos de taxis de {', '.join(map(str, ANIOS))} del NYC TLC."
    )
    parser.add_argument(
        "--year", type=int, choices=ANIOS, nargs="+", default=ANIOS,
        help="año(s) a descargar (por defecto: 2024 y 2026)",
    )
    parser.add_argument(
        "--taxi", choices=(*TIPOS_TAXI, "all"), default="all",
        help="tipo de taxi a descargar (por defecto: all)",
    )
    argumentos = parser.parse_args()

    tipos = TIPOS_TAXI if argumentos.taxi == "all" else (argumentos.taxi,)

    total = {"descargados": 0, "omitidos": 0, "no_publicados": [], "fallidos": []}
    for anio in argumentos.year:
        for tipo in tipos:
            resumen = descargar(tipo, anio)
            total["descargados"] += resumen["descargados"]
            total["omitidos"] += resumen["omitidos"]
            total["no_publicados"] += [
                f"{tipo} {m}" for m in resumen["no_publicados"]
            ]
            total["fallidos"] += [
                f"{tipo} {m}" for m in resumen["fallidos"]
            ]

    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    print(f"  descargados   : {total['descargados']}")
    print(f"  ya existian   : {total['omitidos']}")
    print(f"  no publicados : {len(total['no_publicados'])}")
    if total["no_publicados"]:
        print(f"      {', '.join(total['no_publicados'])}")
    print(f"  fallidos      : {len(total['fallidos'])}")
    if total["fallidos"]:
        print(f"      {', '.join(total['fallidos'])}")
    print("=" * 60)

    return 1 if total["fallidos"] else 0


if __name__ == "__main__":
    sys.exit(main())
