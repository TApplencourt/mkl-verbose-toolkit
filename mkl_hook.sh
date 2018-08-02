#!/bin/bash

PLOCK=~/myscript.lock
#Export MKL_VERBOSE for one rank

# If ALPS_APP_PE variable is set and equal 1 or if I can create the directory source 
if ( [ -z "$ALPS_APP_PE" ] && mkdir "$PLOCK" 2>/dev/null ) || [ "${ALPS_APP_PE:-0}" -eq 1 ]; then
    export MKL_VERBOSE=1
fi

# Clean up on exit or sigterm
function cleanup {
    rmdir "$PLOCK" 2>/dev/null
}

if [ -z "$ALPS_APP_PE" ]; then
 trap cleanup EXIT SIGTERM
fi
#Run the command. 
#Take a nap before in order to avoid race condition
sleep 1
"$@"


