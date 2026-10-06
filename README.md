# Lab 8 - DuckDB

Repositorio base del laboratorio 8 del curso **CC3084 - Data Science**
(Universidad del Valle de Guatemala, Ciclo 2, 2026).

Este es el repositorio **proporcionado por el docente**. Contiene la estructura
del proyecto, el ambiente de ejecucion basado en Docker y un script que descarga
los datos de **2026**. Todo lo demas debe ser construido por cada equipo.

## Trabajo con fork

El laboratorio se desarrolla y se entrega sobre un **fork** de este repositorio.
No se trabaja directamente sobre el repositorio del docente.

1. Realice un fork de este repositorio:
   <https://github.com/menene/duckdb>

2. Clone **su propio fork** (no el del docente):

   ```bash
   git clone https://github.com/<su-usuario>/duckdb.git
   cd duckdb
   ```

3. Opcional, para recibir correcciones publicadas por el docente:

   ```bash
   git remote add upstream https://github.com/menene/duckdb.git
   git fetch upstream
   ```

Realice commits frecuentes y descriptivos: el historial del repositorio es parte
de la evaluacion. **La entrega del laboratorio es la URL de su fork.**

## Estructura

```text
duckdb/
|
+-- data/
|   +-- raw/
|   +-- processed/
|
+-- notebooks/
|
+-- scripts/
|
+-- sql/
|
+-- docs/
|
+-- Dockerfile
+-- metabase.Dockerfile
+-- docker-compose.yml
+-- README.md
```

## Requisitos

- Docker, con Docker Compose
- Git

La primera construccion del ambiente descarga varios cientos de MB y puede
tardar algunos minutos.

Considere el espacio en disco: las imagenes de Docker ocupan unos 3 GB y los
datos de los tres anios del laboratorio superan 1.5 GB, a los que se suma la
base materializada del Ejercicio 6. Se recomienda tener al menos 10 GB libres.

## Datos

El repositorio incluye `scripts/download_data.py`, que descarga los archivos
Yellow y Green publicados por la TLC para 2024 y 2026 (`--help` muestra las
opciones disponibles). Los archivos se guardan en
`data/raw/<tipo>/<anio>/`.

La TLC publica cada mes con varias semanas de atraso, por lo que los ultimos
meses de 2026 todavia no existen. El script consulta al servidor que meses estan
publicados, de modo que vuelve a ejecutarse sin problema conforme aparezcan
nuevos archivos.

Los datos descargados **no deben incluirse en el repositorio Git**. El archivo
`.gitignore` ya esta configurado para evitarlo.

Fuente de datos: NYC TLC Trip Record Data
<https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page>

Dentro de los contenedores, la carpeta `data/` del proyecto esta montada en
`/workspace/data`. Esa es la ruta que deben usar las herramientas que corren
dentro del ambiente, no la ruta de su computadora.

> **Nota sobre DuckDB:** un archivo `.duckdb` admite un solo proceso con permiso
> de escritura a la vez. Si conecta una herramienta externa a su base de datos,
> use el modo de solo lectura (`read_only`) en esa conexion; de lo contrario los
> demas procesos no podran abrir el archivo.

## Material a entregar

Al finalizar, su fork debe contener:

- el codigo fuente modificado y los scripts de descarga;
- las consultas SQL desarrolladas;
- el notebook o notebooks utilizados;
- la documentacion de las consultas;
- los scripts utilizados para los benchmarks;
- el codigo de los indicadores y visualizaciones;
- el tablero o la evidencia del tablero desarrollado;
- este `README.md`, completado segun la siguiente seccion.

Los archivos de datos descargados **no** deben incluirse.

---

# Documentacion del equipo

Las siguientes secciones deben ser completadas por cada equipo. El README final
debe permitir que una persona que no participo en el desarrollo pueda levantar el
ambiente, descargar los datos, ejecutar el analisis, reproducir los benchmarks y
generar los resultados principales.

## Como levantar el ambiente

Desde la raiz del repositorio, construya las imagenes e inicie los servicios:

```bash
docker compose up --build -d
```

La primera construccion descarga las imagenes base y las dependencias, por lo
que puede tardar varios minutos. Para comprobar el estado de los contenedores:

```bash
docker compose ps
```

Ambos servicios deben aparecer como `running` (o `Up`):

- **JupyterLab**: <http://localhost:8888>. Permite trabajar con notebooks y
  scripts Python dentro del contenedor `lab`.
- **Metabase**: <http://localhost:3000>. En el primer inicio, complete la
  configuracion inicial de Metabase para acceder a su interfaz y configurar
  las consultas y visualizaciones.

Las carpetas `data/`, `notebooks/`, `scripts/`, `sql/` y `docs/` del repositorio
se montan en `/workspace/` dentro de `lab`, por lo que los cambios en ellas se
conservan en la computadora anfitriona. Metabase tambien puede acceder a
`data/`, montada en `/workspace/data`.

El ambiente incluye Python 3.11 con JupyterLab, DuckDB, pandas, PyArrow,
Matplotlib y Requests; Metabase incluye el driver de DuckDB. Las versiones de
los paquetes Python estan fijadas en `requirements.txt`, y las versiones de
Metabase y su driver se definen en `metabase.Dockerfile`.

Para ver los registros de inicio o detener los servicios:

```bash
docker compose logs
docker compose down
```

`docker compose down` detiene y elimina los contenedores, pero conserva el
volumen de datos de Metabase y los archivos del proyecto montados desde el
anfitrion. Para volver a iniciar el ambiente sin reconstruir las imagenes,
ejecute `docker compose up -d`.

Un ambiente reproducible es importante porque permite que las personas del
equipo ejecuten el analisis con las mismas versiones de las herramientas y la
misma configuracion, reduciendo diferencias causadas por instalaciones locales.
Asi se pueden repetir y verificar las consultas y los resultados, colaborar con
menos problemas de compatibilidad y mantener un registro claro de como se
produjeron los resultados. En este proyecto tambien facilita reconstruir el
entorno sin versionar los grandes archivos de datos.

## Como descargar los datos

El script `scripts/download_data.py` obtiene los archivos Parquet mensuales de
taxis amarillos (`yellow`) y verdes (`green`) publicados por la TLC para 2024
y 2026. Por defecto procesa ambos años y ambos tipos:

```bash
docker compose exec lab python scripts/download_data.py
```

Para seleccionar años o tipos específicos:

```bash
docker compose exec lab python scripts/download_data.py --year 2024
docker compose exec lab python scripts/download_data.py --year 2024 2026 --taxi yellow
docker compose exec lab python scripts/download_data.py --taxi yellow
docker compose exec lab python scripts/download_data.py --taxi green
```

El script revisa los 12 meses por año/tipo y descarga solo los que estan
publicados. Los archivos se guardan como
`data/raw/<tipo>/<anio>/<tipo>_tripdata_<anio>-MM.parquet`. Si un archivo no
vacio ya existe, se conserva y se omite; las descargas nuevas se escriben a un
temporal, verifican su tamaño cuando el servidor informa `Content-Length` y
solo entonces se renombran. Los errores de conexion y descarga se muestran en
el resumen y hacen que el proceso termine con codigo distinto de cero.

En la ejecucion del 6 de octubre de 2026, se descargaron para 2024 los 24
archivos (12 por tipo). Para 2026 estaban publicados enero a agosto (16
archivos); los meses de septiembre a diciembre todavia no estaban publicados.
Volver a ejecutar el script incorpora archivos publicados recientemente y
omite los que ya existen. Los datos se mantienen localmente y no se incluyen
en Git.

## Ejercicio 3: exploracion directa de Parquet

La documentacion, las consultas ejecutables, los resultados observados y las
decisiones de los puntos 3.1–3.9 estan centralizados en el notebook
[`notebooks/duck.ipynb`](./notebooks/duck.ipynb). Abra el archivo con JupyterLab
o VS Code y ejecute las celdas en orden para repetir la exploracion directamente
sobre los Parquet descargados.

## Ejercicio 5: ampliar el analisis a 2024

Para incorporar los datos 2024 y validar las consultas multi-anio, siga las
secciones 5.1–5.9 de [`notebooks/duck.ipynb`](./notebooks/duck.ipynb). El
notebook contiene la consulta conjunta, conteos por año/tipo, validacion del
esquema, resultados y la explicacion de los ajustes necesarios a patrones y
filtros de las consultas existentes.

## Como ejecutar el analisis

Inicie los servicios si aun no estan activos y abra JupyterLab en
<http://localhost:8888>:

```bash
docker compose up -d
```

En JupyterLab, abra `notebooks/duck.ipynb` y ejecute las celdas en orden. El
notebook contiene los Ejercicios 3, 4 y 5: exploracion y analisis de los datos,
comparacion de años, consultas DuckDB, resultados, graficas y hallazgos. Las
consultas leen directamente los Parquet bajo `data/raw/`; si
todavia no los ha descargado, siga primero la seccion [Como descargar los
datos](#como-descargar-los-datos). Puede volver a ejecutar
`scripts/download_data.py` para incorporar meses TLC recientemente publicados;
al reejecutar las celdas, los conteos y graficas se actualizaran con los
archivos locales disponibles.

## Como reproducir los benchmarks

<!-- TODO (Ejercicio 6) -->

## Como generar los resultados principales

<!-- TODO -->
