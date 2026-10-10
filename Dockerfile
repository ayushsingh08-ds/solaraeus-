# CPU-only container for SOLARAEUS.
#
# Deliberately excludes CuPy/CUDA: the engine must run correctly and
# reproducibly with no GPU present, and the GPU path is exercised separately on
# GPU-equipped runners. Build and verify:
#
#   docker build -t solaraeus:cpu -f Dockerfile .
#   docker run --rm solaraeus:cpu solaraeus doctor
#   docker run --rm solaraeus:cpu solaraeus golden compare
#
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# System libraries required by the geospatial stack (rasterio/GDAL, pyproj/PROJ)
# and by matplotlib/trimesh for headless rendering.
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libgdal-dev \
        libproj-dev \
        libgeos-dev \
        libgl1 \
        libglib2.0-0 \
        git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Dependency layer first so edits to source do not invalidate the pip cache.
COPY pyproject.toml README.md LICENSE CITATION.cff ./
COPY src ./src
RUN pip install -e ".[viewer-export,dev]"

# Remaining project content
COPY cities ./cities
COPY tools ./tools
COPY tests ./tests
COPY examples ./examples
COPY docs ./docs
COPY Makefile ./

# Smoke-test the image at build time: if the engine or the golden master is
# broken, the build fails here rather than at run time.
RUN solaraeus doctor && \
    solaraeus golden capture --out /tmp/golden && \
    solaraeus golden compare --baseline tools/golden/baseline --out /tmp/golden

CMD ["solaraeus", "doctor"]
