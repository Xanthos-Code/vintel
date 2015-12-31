
You want to build Vintel on your own?

This is for windows users. Linux users can install the programs
and tools mostly using distribution's software management.


=================================================================

To run the source, you need:

* Python 2.7.x
  https://www.python.org/downloads/
  Vintel was not written for Python 3!

* PyQt4x
  http://www.riverbankcomputing.com/software/pyqt/download
  Please use the PyQt Binary Package for Py2.7
  Vintel was not written for PyQt5!

* BeautifulSoup 4
  https://pypi.python.org/pypi/beautifulsoup4

* Pyglet 1.2.4 (for python 2.7)
  pygame is used to play the sound: If it is not available the
  sound option will be disabled.

--- Deprectated ---

* pygame 1.9.1 (for python 2.7)
  http://pygame.org/download.shtml
  pygame is used to play the sound: If it is not available the
  soundoption will be disabled.

=================================================================

How to set up an development directory:


- Download and install Python 2.7 from the link above

- Downlad and install PyQt from the link above

- If you installed Python 2.7.9 (or newer) pip is installed
  with it. Pip is an package manager for Python.
  Use it to install BeautifulSoup4:
  pip install BeautifulSoup4

* If you want sound support, download and install pyglet from
  the link above.

Now you are able to start the vintel.py.

=================================================================

Hot to create the standalone exe?

The standalone exe is created using pyinstaller.
All media files and the .spec-file with the configuration for
pyinstaller are included in the source-archive.
https://github.com/pyinstaller/pyinstaller/wiki
