**Meal Master Parser**

This is a simple parser for Meal Master files.
Version 7 and 8 are supported or rather on these and for these
versions the parser was developed.

The parser first tries to detect the file format and if it is not
utf-8 convert the file into utf-8.

The recipes are stored in a csv file with the same name as the input file plus .csv added as a suffix.

**Usage**

Either pass in a single file or a directory in which the files, you wish to parse,
reside in. 

E.g: python mmparse.py {file or directory}

The csv will be created either in the supplied directory or in case of a single file
just directly where the parser was called.

**Caution**

Like I said at the start this is a CRUDE parser. For my needs it was fine. If you have
thousands of MealMaster files and do not care if some are not correctly parsed this tool is totally fine.
If you need more accuracy, feel free to fork and improve it.
