+++
title = "🐍 Python utils"
slug = "python-utils"
+++


#### Virtual environnment
```bash
# create a new virtual environnment
virtualenv .name_env

# activate this environnment
source .name_env/bin/activate

# install chosen packages
pip install numpy

# exit the environnment
deactivate

# delete the environnment with all installed packages
rm -rf .name_env
```

#### pip requirements
```bash
# list all installed packages and their version
pip freeze > requirements.txt

# install all listed packages
pip install -r requirements.txt
```