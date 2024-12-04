# Building REVIVE2024 executable
The following steps are a tutorial for building the REVIVE2024 .exe file.


### 1. Create a new virtual environment
A new, blank virtual environment must be created *outside* of the `REVIVE2024` directory. It is recommended to do so in the full `REVIVE` project directory for simplicity. Be sure that there is not another virtual environment folder already present (like `.venv`) in the current working directory! From here the process is the same as listed in the README:
```console
cd REVIVE
py -m venv .venv
```

### 2. Activate the virtual environment
To activate the fresh virtual environment, the process is the same as mentioned in the README. From the directory where the recently created  `.venv` resides, enter the command below that corresponds to the shell being used.
| Platform/Shell | Command |
| - | - |
| Windows (cmd.exe) | .venv\Scripts\activate.bat |
| Windows (PowerShell) | .venv\Scripts\Activate.ps1 |
| Mac (zsh) | source .venv/bin/activate |
| Mac (PowerShell) | .venv/bin/Activate.ps1 |
| Linux (bash) | source .venv/bin/activate |


### 3. Install dependencies
Once the environment is activated, the required dependencies can be installed to the virtual environment with the following command. If the current directory is still `REVIVE`, type the command as is; otherwise, replace the path below with the relative path to `requirements.txt` located in `REVIVE2024`.
```console
py -m pip install -r "REVIVE2024/requirements.txt"
```

### 4. Install the pyinstaller package
Keep in mind, it is important that `pyinstaller` must be installed by pip from *within* the environment created in step 1. Do **NOT** skip this step if `pyinstaller` has been previously installed outside of `.venv`; it must be done again inside the virtual environment or the wrong dependencies will be packed into the .exe later.
```console
py -m pip install pyinstaller
```

### 5. Use pyinstaller to build the .exe
All static resources used by the app must be referenced with the `pyinstaller` command. To simplify paths, the example below runs the `pyinstaller` from within the `REVIVE2024` directory. In the following command, the path to the versioned icon should be replaced with the real path to that icon's location. Additionally, the path to the virtual environment's `site-packages` directory must be replaced with its real location, which will be found inside of `.venv/Lib`. To avoid any spelling errors, it is best to copy these paths from a file explorer. Enter the following commands with the necessary replacements, making sure to move into the `REVIVE2024` directory before running the long one!

```console
cd REVIVE2024
pyinstaller --name REVIVEcalc -i path/to/versioned/iconfile.ico --add-data help_tree_content.json:. --add-data help_tree_structure.txt:. --add-data phius_runlist_options.json:. --add-data required_columns.json:. --add-data Phius-Logo-RGB__Color_Icon.ico:. --paths path/to/blank/venv/Lib/site-packages --onefile main.py
```

### 6. Running the .exe
The build step will take a decent amount of time, but once it is finished, the resulting .exe file can be found in the `dist` folder created in the directory where the `pyinstaller` command was run. Double-click to run the executable app. After a few seconds of seeing a console window on bootup, the app will appear as a small window on the computer screen.


### 7. Clean up
The virtual environment used to build the app will likely not be needed again, at least until the executable must be rebuilt. To prevent future mixups with virtual environments, it is recommended to deactivate and remove the `.venv` folder. Deactivate over command line with:
```console
deactivate
```
And then simply delete the `.venv` directory.