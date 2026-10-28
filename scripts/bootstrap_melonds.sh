#!/usr/bin/env bash
# Local build only: no sudo, system installation, or original-input writes.
set -euo pipefail
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_dir"
mkdir -p tools/downloads tools/src tools/build workbench/captures
exec > >(tee -a workbench/captures/bootstrap.log) 2>&1
for command in curl tar cmake ninja pkg-config g++; do
    command -v "$command" >/dev/null || { echo "Missing build prerequisite: $command"; exit 1; }
done
pkg-config --exists Qt6Core Qt6Gui Qt6Widgets Qt6Network Qt6Multimedia Qt6OpenGL Qt6OpenGLWidgets Qt6Svg sdl2 libarchive libzstd faad2 || {
    echo 'Missing development dependencies. See notes/WORKBENCH.md; nothing installed globally.'
    exit 1
}
export PKG_CONFIG_PATH="$project_dir/tools/local/lib/pkgconfig${PKG_CONFIG_PATH:+:$PKG_CONFIG_PATH}"
if ! pkg-config --exists libenet; then
    if [[ ! -s tools/downloads/enet-1.3.18.tar.gz ]]; then
        curl --fail --location --retry 2 --connect-timeout 15 --max-time 180 \
            https://github.com/lsalzman/enet/archive/refs/tags/v1.3.18.tar.gz \
            --output tools/downloads/enet-1.3.18.tar.gz.part
        mv tools/downloads/enet-1.3.18.tar.gz.part tools/downloads/enet-1.3.18.tar.gz
    fi
    sha256sum tools/downloads/enet-1.3.18.tar.gz > tools/downloads/enet-1.3.18.tar.gz.sha256
    if [[ ! -d tools/src/enet-1.3.18 ]]; then
        tar -xzf tools/downloads/enet-1.3.18.tar.gz -C tools/src
    fi
    cmake -S tools/src/enet-1.3.18 -B tools/build/enet-1.3.18 -G Ninja \
        -DCMAKE_INSTALL_PREFIX="$project_dir/tools/local"
    cmake --build tools/build/enet-1.3.18 --parallel 4
    cmake --install tools/build/enet-1.3.18
    mkdir -p tools/local/lib/pkgconfig
    cat > tools/local/lib/pkgconfig/libenet.pc <<EOF
prefix=$project_dir/tools/local
libdir=\${prefix}/lib/static
includedir=\${prefix}/include

Name: libenet
Description: ENet reliable UDP networking library
Version: 1.3.18
Libs: -L\${libdir} -lenet
Cflags: -I\${includedir}
EOF
fi
archive=tools/downloads/melonDS-1.1.tar.gz
if [[ ! -s "$archive" ]]; then
    curl --fail --location --retry 2 --connect-timeout 15 --max-time 180 \
        https://github.com/melonDS-emu/melonDS/archive/refs/tags/1.1.tar.gz \
        --output "$archive.part"
    mv "$archive.part" "$archive"
fi
sha256sum "$archive" | tee tools/downloads/melonDS-1.1.tar.gz.sha256
if [[ ! -d tools/src/melonDS-1.1 ]]; then
    tar -xzf "$archive" -C tools/src
fi
cmake -S tools/src/melonDS-1.1 -B tools/build/melonDS-1.1 -G Ninja \
    -DCMAKE_BUILD_TYPE=RelWithDebInfo -DENABLE_GDBSTUB=ON -DENABLE_JIT=OFF \
    -DENABLE_LTO_RELEASE=OFF -DENABLE_WAYLAND=OFF -DUSE_QT6=ON
cmake --build tools/build/melonDS-1.1 --parallel "${NC3_BUILD_JOBS:-4}"
mkdir -p tools/build/melonDS-1.1/portable
if [[ ! -f tools/build/melonDS-1.1/portable/melonDS.toml ]]; then
    cp tools/melonDS-debug.toml tools/build/melonDS-1.1/portable/melonDS.toml
fi
echo 'Local build complete. Run bash scripts/run_melonds.sh'
