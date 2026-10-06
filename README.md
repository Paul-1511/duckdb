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

El repositorio incluye `scripts/download_data.py`, que descarga los archivos de
2026 publicados por la TLC (`--help` muestra las opciones disponibles). Los
archivos se guardan en `data/raw/<tipo>/<anio>/`.

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
taxis amarillos (`yellow`) y verdes (`green`) publicados por la TLC para 2026.
Desde la raiz del repositorio, ejecute ambos tipos:

```bash
docker compose exec lab python scripts/download_data.py
```

Tambien puede solicitar un solo tipo:

```bash
docker compose exec lab python scripts/download_data.py --taxi yellow
docker compose exec lab python scripts/download_data.py --taxi green
```

El script revisa los 12 meses de cada tipo en la fuente TLC y descarga solo
aquellos que estan publicados. Los archivos se guardan como
`data/raw/<tipo>/2026/<tipo>_tripdata_2026-MM.parquet`. Si un archivo no vacio
ya existe en esa ruta, se omite; las descargas nuevas se escriben primero a un
archivo temporal y se renombran al terminar. Se comprueba que la cantidad de
bytes recibida coincida con el `Content-Length` anunciado por el servidor cuando
este encabezado esta disponible. Los errores de conexion y descarga se muestran
en el resumen y hacen que el proceso termine con codigo distinto de cero.

Los cambios realizados al script limitan el alcance a Yellow y Green de 2026,
construyen los nombres y rutas por mes, consultan cuales archivos estan
publicados en vez de asumir que el año esta completo y evitan volver a
descargar archivos locales existentes. Ademas, distinguen los meses no
publicados de los errores de conexion, reintentan las consultas y verifican el
tamaño de cada descarga cuando el servidor anuncia el `Content-Length`.

La completitud se determina comparando los 12 meses posibles de cada tipo con
la disponibilidad reportada por la fuente TLC y confirmando que todos los
meses publicados aparecen como descargados o ya existentes en el resumen, sin
fallos. En la ejecucion del 6 de octubre de 2026, la fuente respondio que estaban
publicados enero a agosto para ambos tipos: se esperaban 16 archivos. Los meses
de septiembre a diciembre aun no estaban publicados; vuelva a ejecutar el
script para incorporar los nuevos meses cuando la TLC los publique. Los
archivos descargados se mantienen localmente y no se incluyen en Git.

## Como ejecutar el analisis

<!-- TODO -->

## Como reproducir los benchmarks

<!-- TODO (Ejercicio 6) -->

## Como generar los resultados principales

<!-- TODO -->
