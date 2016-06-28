# g15mediadaemon
Python daemon-like app that controls your music apps using the mediakeys and showing media information on the lcd (connected to g15daemon)

#Requirements
- Python3
- Xlib
- pulsectl (for spotify app)
- freetype

Include dir is added to sys.path, so you can install dependencies from the project dir like: pip3 install --install-option="--install-purelib=$(pwd)/include" python3-xlib
