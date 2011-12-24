Clutterm
========

A clutter based terminal written in pure python (no vte lib).

This is a work in progress and it's far from ready for every day use.


What's working ?
----------------

  - Clutter / Pango support with python3 using introspection lib
  - Asynchronous communication with underlying pseudo terminal using select
  - Pango markup for color
  - 256 colors support
  - Shaders can be applied to the terminal surface (try it with F1-F6)
  - Smooth terminal cursor 
  - Visual effect on bell
  - Most of useful xterm escapes are implemented


What's not
----------

Almost everything else:
  - Remaining xterm escapes
  - Bugs in escapes handling
  - Text selection
  - Escapes lexer need optimisation and clean up
  - Text rendering is slow
  - Resize does not always work
  - Several bindings need to be added


Want to contribute ?
--------------------

You are more than welcome, just fork it and make me pull request with a little explanation of your modifications.
