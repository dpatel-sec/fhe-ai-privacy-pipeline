# Installing OpenFHE

The project needs both the general Python dependencies in `requirements.txt` and the OpenFHE Python bindings.

## Ubuntu 24.04

The prebuilt `openfhe` package targets Ubuntu 24.04. After creating and activating a virtual environment, install the dependencies:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install openfhe
```

Then run either project script from the repository root:

```bash
python src/main_demo.py
python src/bonus_privacy_preserving_inference.py
```

## macOS (Apple Silicon)

The prebuilt OpenFHE Python wheel used in this project is not compatible with macOS, so build OpenFHE and its Python wrapper locally. These commands were used to build this project on macOS/arm64:

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt cmake "pybind11[global]"
brew install libomp
git clone --depth 1 https://github.com/openfheorg/openfhe-development.git
git clone --depth 1 https://github.com/openfheorg/openfhe-python.git
git -C openfhe-development submodule update --init --recursive
mkdir openfhe-build openfhe-install
cd openfhe-build
CPPFLAGS='-I/opt/homebrew/opt/libomp/include' LDFLAGS='-L/opt/homebrew/opt/libomp/lib' ../.venv/bin/cmake ../openfhe-development -DCMAKE_INSTALL_PREFIX=../openfhe-install
make -j4
make install
cd ..
mkdir openfhe-python-build openfhe-python-package
cd openfhe-python-build
CPPFLAGS='-I/opt/homebrew/opt/libomp/include' LDFLAGS='-L/opt/homebrew/opt/libomp/lib' ../.venv/bin/cmake ../openfhe-python -DCMAKE_PREFIX_PATH="$PWD/../openfhe-install;$PWD/../.venv" -Dpybind11_DIR="$PWD/../.venv/share/cmake/pybind11" -DPython_EXECUTABLE="$PWD/../.venv/bin/python" -DPython_ROOT_DIR="$PWD/../.venv" -DPython_FIND_VIRTUALENV=ONLY -DCMAKE_INSTALL_PREFIX="$PWD/../openfhe-python-package"
make -j4
make install
cd ..
mkdir -p openfhe-python-package/lib
cp openfhe-install/lib/libOPENFHE*.dylib openfhe-python-package/lib/
```

The `src/openfhe_runtime.py` helper detects the `openfhe-python-package/` folder created by this process. These build directories are excluded from Git because they are compiled artifacts.
