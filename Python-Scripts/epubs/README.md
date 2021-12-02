# Epub conversion

This script is used to convert the markdown files, which we generate from epub files with the help of `Calibre`, into TEI XML.


## Prerequisites

This script has no external dependencies. It expects the source files in `.txt` files at the location given in the `SOURCE_PATH` constant. It will attempt to write the resulting `.xml` files to the location given in the `SAVE_PATH` constant. If this location is not empty, it will issue a warning, but proceed to (over)write the files there.


## Usage

## Tests
