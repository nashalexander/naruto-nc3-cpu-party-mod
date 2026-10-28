#!/usr/bin/env bash
# Uses the project-local slirp built by bootstrap_melonds.sh and system Qt6.
set -euo pipefail
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_dir"
mkdir -p tools/downloads tools/src tools/build tools/local/lib/pkgconfig tools/local/include
for spec in 'melonDS-0.9.5 https://github.com/melonDS-emu/melonDS/archive/refs/tags/0.9.5.tar.gz' 'extra-cmake-modules-6.20.0 https://github.com/KDE/extra-cmake-modules/archive/refs/tags/v6.20.0.tar.gz'; do
    read -r name url <<< "$spec"
    if [[ ! -s "tools/downloads/$name.tar.gz" ]]; then
        curl --fail --location --connect-timeout 15 --max-time 180 "$url" -o "tools/downloads/$name.tar.gz.part"
        mv "tools/downloads/$name.tar.gz.part" "tools/downloads/$name.tar.gz"
    fi
    sha256sum "tools/downloads/$name.tar.gz" > "tools/downloads/$name.tar.gz.sha256"
    if [[ ! -d "tools/src/$name" ]]; then tar -xzf "tools/downloads/$name.tar.gz" -C tools/src; fi
done
cmake -S tools/src/extra-cmake-modules-6.20.0 -B tools/build/ecm -G Ninja \
    -DCMAKE_INSTALL_PREFIX="$project_dir/tools/local" -DBUILD_TESTING=OFF \
    -DBUILD_HTML_DOCS=OFF -DBUILD_MAN_DOCS=OFF -DBUILD_QTHELP_DOCS=OFF
cmake --install tools/build/ecm
test -f tools/build/melonDS-1.1/net/libslirp/libslirp.a || {
    echo 'First build melonDS 1.1 with scripts/bootstrap_melonds.sh'; exit 1;
}
ln -sfn "$project_dir/tools/src/melonDS-1.1/src/net/libslirp/src" tools/local/include/slirp
cp tools/build/melonDS-1.1/net/libslirp/libslirp-version.h tools/local/include/
cat > tools/local/lib/pkgconfig/slirp.pc <<EOF
prefix=$project_dir/tools
libdir=\${prefix}/build/melonDS-1.1/net/libslirp
includedir=\${prefix}/local/include

Name: slirp
Description: Project-local libslirp from melonDS 1.1
Version: 4.8.0
Libs: -L\${libdir} -lslirp
Cflags: -I\${includedir}
EOF
export PKG_CONFIG_PATH="$project_dir/tools/local/lib/pkgconfig${PKG_CONFIG_PATH:+:$PKG_CONFIG_PATH}"
qt_version="$(pkg-config --modversion Qt6Gui)"
qt_include="$(pkg-config --variable=includedir Qt6Gui)"
# Old source needs explicit standard/private Qt includes with current GCC/Qt.
cxx_flags="-include algorithm -include cstdint -I$qt_include/QtGui/$qt_version -I$qt_include/QtGui/$qt_version/QtGui -I$qt_include/QtCore/$qt_version -I$qt_include/QtCore/$qt_version/QtCore"
cmake -S tools/src/melonDS-0.9.5 -B tools/build/melonDS-0.9.5 -G Ninja \
    -DUSE_QT6=ON -DPORTABLE=ON -DENABLE_JIT=OFF -DENABLE_LTO_RELEASE=OFF \
    -DCMAKE_BUILD_TYPE=RelWithDebInfo -DCMAKE_POLICY_VERSION_MINIMUM=3.5 \
    -DCMAKE_PREFIX_PATH="$project_dir/tools/local" "-DCMAKE_CXX_FLAGS=$cxx_flags"
cmake --build tools/build/melonDS-0.9.5 --parallel "${NC3_BUILD_JOBS:-4}"
