# uk-pilot-synthetic-data-gen
Scripts for generating synthetic data for UK pilot 


Prepare the environment and install dependencies 

```
python3 -m venv ../synthetic-data-env
source ../synthetic-data-env/bin/activate
pip3 install -r requirements.txt 
```

Then run with providing
 1. EDP id. Either Digital1 or Digital2. 
 2. A random seed

```
python3 main.py -r 4 -e Digital1
```