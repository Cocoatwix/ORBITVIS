# ORBITVIS
A simple PyGame application to visualise orbits created by LINCELLAUT.
The program was tested with PyGame 1.9.6, though other versions should work as well.

Check the "documentation" directory for a more detailed explanation of ORBITVIS' usage and inner working details.

# Before Using
This application requires compiling a shared library from [LINCELLAUT](https://github.com/Cocoatwix/LINCELLAUT) for it to function. The library must be compiled on the same device as you intend to use this app, otherwise Python won't be able to make use of the files. 

If you encounter the error `OSError: [WinError 193] %1 is not a valid Win32 application` when running, the shared library was probably compiled into a 32-bit library while the Python version you're using is 64-bit. Using a 32-bit install of Python should fix the issue.

See the LINCELLAUT project for more details.

# Some examples of ORBITVIS Visualisations
Matrix: `[[2 1][5 6]]`

Modulus: 7

Iterations: 1

![ORBITVIS - i1m7F2156](https://user-images.githubusercontent.com/31392083/172000181-f286dd5d-ed0a-4558-9a39-80981f7e8bb1.png)

Matrix: `[[8 3][7 1]]`

Modulus: 20

Iterations: 15

![ORBITVIS - i15m20F8371](https://user-images.githubusercontent.com/31392083/172000190-5796bb7b-9385-47dd-9815-e2917c189607.png)

Matrix: `[[1 1][1 2]]`


Modulus: 555

Iterations: 11

![ORBITVIS - i11m555F1112](https://user-images.githubusercontent.com/31392083/172000192-1c7800b6-3cea-434c-83c1-2532ff0c55d4.png)

More examples can be found in the "examples" directory :)
