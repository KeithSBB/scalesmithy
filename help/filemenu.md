# File Menu
## Save
This will display a file dialog to select a json file name and
then a second dialog to select which scale families to save to
this file.  Scale Smithy stores scales as scale families which
have named modes without reference to any particular key

## Load
This will display a file dialog to select which scale json file to
load and then a second dialog on which scale families from this file
to load into Scale Smithy.  If an existing scale family exists with the
same name thenis is shown in red.  Loading red scale families will
overwrite that scale family in memory and permanenmtly save it into
the config file when terminating the application.

## Print
This will display a print dialog and let you print the current
window contents

## Save Image
This will display a file dialog that a image of the screen can be
saved to.  Various formats are supported including png, jpeg. The
file extension is used to determine the format.