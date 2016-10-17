Each configuration file must start with a metadata section enclosed between `---`
The text between the markers represents a dictionary in json format.
The following keyworkds must be defined:

    - hostname

        The name of machine. Prefer the short version over the long version
        e.g. use `hmem` instead of `hmem.ucl.ac.be`
        
    - date 

        Creation date in the format `yyyy-mm-dd- e.g. `2011-12-24`

    - author

        The author of the configuration file.

    - description
        
        String or list of strings with info about the configuration file.

    - keyworkds

        List of strings with tags associated to the configuration file.
        Use `abiconf.py keys` to get the list of keywords already used 
        and try to re-use them for new files. 

    - modules

        List of modules required to build/run the executables.
        Empty list if no module is required.