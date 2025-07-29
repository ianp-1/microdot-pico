brew install cmake python
brew install --cask gcc-arm-embedded

git clone https://github.com/micropython/micropython.git
cd micropython

put the modules in micropython root directory

git submodule update --init --recursive
git checkout (enter latest version here)

cd micropython/ports/rp2
make BOARD=RPI_PICO2 USER_C_MODULES=/full/path/to/your/module -j$(sysctl -n hw.ncpu) V=1
