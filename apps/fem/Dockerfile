# Q3-L2 FEM toolchain — Elmer + Gmsh (+ GetDP when packaged)
# Mo-有限元 owns this image body; Mo-运维 owns compose wiring (profile fem).
# NEVER install Elmer/GetDP/Gmsh on the host — only in this image.
#
# Base: Ubuntu 22.04 + official Elmer CSC PPA (elmerfem-csc).
FROM ubuntu:22.04

LABEL org.mo.service=fem \
      org.mo.stage=q3-l2-elmer \
      org.mo.kernels="elmer,gmsh,getdp"

ENV DEBIAN_FRONTEND=noninteractive \
    MO_FEM_WORKDIR=/var/mo/fem \
    LANG=C.UTF-8

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      ca-certificates \
      gnupg \
      software-properties-common \
      bash \
      curl \
      python3 \
      libopenblas0 \
      libgomp1 \
 && add-apt-repository -y ppa:elmer-csc-ubuntu/elmer-csc-ppa \
 && apt-get update \
 && apt-get install -y --no-install-recommends \
      elmerfem-csc \
      gmsh \
      getdp \
 && rm -rf /var/lib/apt/lists/* \
 && mkdir -p "${MO_FEM_WORKDIR}" \
 && command -v ElmerSolver \
 && command -v ElmerGrid \
 && command -v gmsh \
 && command -v getdp \
 && ldd "$(command -v ElmerSolver)" | tee /tmp/ldd-elmer.txt \
 && ! grep -q "not found" /tmp/ldd-elmer.txt \
 && gmsh -version \
 && getdp -version

WORKDIR /var/mo/fem

# Compose keeps the service idle; worker-fem / exec invokes ElmerSolver|gmsh on MO_FEM_WORKDIR jobs.
COPY apps/fem/scripts/entrypoint.sh /usr/local/bin/mo-fem-entrypoint
RUN chmod +x /usr/local/bin/mo-fem-entrypoint

ENTRYPOINT ["/usr/local/bin/mo-fem-entrypoint"]
CMD ["sleep", "infinity"]
