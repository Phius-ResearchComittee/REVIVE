# REVIVE
REVIVE Pilot program tools

## Install and Run
REVIVE Calculator uses the PySide6 GUI framework, which runs most optimally in a python environment. To create an environment, you may use python's `venv` command as shown below. The installation instructions below are for python 3.11 or greater, so for older installations the command will be `python` or `python3` instead of `py`. If you run into any problems, please refer to the `venv` page [here](https://docs.python.org/3/library/venv.html#module-venv).

### 1. Create the virtual environment
Starting inside the REVIVE directory, enter the following commands in your terminal to create a virtual environment called `.venv`. This must be done only once upon installation; every subsequent run will only need to activate this `.venv` to use the app as described in step 2.
```console
cd REVIVE2024
py -m venv .venv
```

### 2. Activate the virtual environment
To activate your virtual environment, the command is platform-dependent. Making sure you are in the `REVIVE2024` directory, enter the command that corresponds to your machine and command shell. This will need to be done any time you would like to run the app.
| Platform/Shell | Command |
| - | - |
| Windows (cmd.exe) | .venv\Scripts\activate.bat |
| Windows (PowerShell) | .venv\Scripts\Activate.ps1 |
| Mac (zsh) | source .venv/bin/activate |
| Mac (PowerShell) | .venv/bin/Activate.ps1 |
| Linux (bash) | source .venv/bin/activate |

_**Note for Windows PowerShell Users:** If errors occur while trying to activate for the first time, you may need to set the execution policy for the user with the command below. More information on execution policies [here](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_execution_policies?view=powershell-7.4)._
```ps
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 3. Install dependencies
All required modules for running the REVIVE Calculator are listed in `requirements.txt`. To install all of these in one command, first confirm that your virtual environment is activated and you are in the `REVIVE2024` directory. Then run the command below. It will take several minutes.
```
py -m pip install -r "requirements.txt"
```
This operation is also only required after the initial creation of a clean virtual environment. Every subsequent activation of `.venv` will already have these requirements installed.

### 4. Run the program
To launch the REVIVE Calculator app interface, simply use the command below while inside the `REVIVE2024` directory and `.venv` is activated.
```
py main.py
```

### 5. Cleanup
It is a good idea to avoid installing any extra dependencies to `.venv` other than the packages denoted in `requirements.txt`. To keep the virtual environment clean, make sure to deactivate `.venv` when you are done using the app. As a reminder, all dependencies will remain intact, so on the next run only steps 2 and 4 are required. To deactivate on any platform, the following command will do so as long as the environment is currently activated.
```
deactivate
```