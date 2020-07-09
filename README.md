# openpnp_kicad_utils

- pnp_preprocessor
Reformat centroid output from kicad to fit openpnp
Replace kicad package names with kicad package names through an alias file

- kifoot2openpnp
Will translate kicad footprint information into openpnp footprint/pad information and overall package dimension.
Uses the package alias file to match kicad package with openpnp package.
Uses the https://github.com/KiCad/kicad-library-utils submodule to parse data from kicad.  Rememer to initialize and pull this submodule.

- OpenPnPParts
Generate QRcode images according to the openpnp parts list.  Allows compact labelling of feeders.
Either generates individual images or a single combined image.


Generally can use init file, user input or command line to get input and output filenames and processing options.

