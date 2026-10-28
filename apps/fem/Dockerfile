# Q3-3 FEM runtime (Elmer / GetDP / Gmsh) — Mo-运维 + Mo-有限元
# Constraint: never install Elmer/GetDP/Gmsh on the host; only in this image.
# Mo-有限元 owns solver templates / entrypoints; Mo-运维 owns compose wiring.
#
# Current: slim placeholder so `make up-fem` can start the profile without host packages.
# Replace FROM/CMD when FEM tip lands a real toolchain image.
FROM debian:bookworm-slim

LABEL org.mo.service=fem \
      org.mo.stage=q3-3-stub

ENV DEBIAN_FRONTEND=noninteractive \
    MO_FEM_WORKDIR=/var/mo/fem

RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates bash \
 && rm -rf /var/lib/apt/lists/* \
 && mkdir -p "${MO_FEM_WORKDIR}"

WORKDIR /var/mo/fem

# Placeholder: real image will include gmsh + elmerfem / getdp binaries.
CMD ["bash", "-lc", "echo 'mo-fem stub: waiting for Mo-有限元 toolchain'; sleep infinity"]
