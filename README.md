
# BTVNanoCommissioning
[![Linting](https://github.com/cms-btv-pog/BTVNanoCommissioning/actions/workflows/python_linting.yml/badge.svg)](https://github.com/cms-btv-pog/BTVNanoCommissioning/actions/workflows/python_linting.yml)
[![TTbar](https://github.com/cms-btv-pog/BTVNanoCommissioning/actions/workflows/ttbar_workflow.yml/badge.svg)](https://github.com/cms-btv-pog/BTVNanoCommissioning/actions/workflows/ttbar_workflow.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Repository for Commissioning studies in the BTV POG based on (custom) nanoAOD samples

## Requirements
### Setup 

:heavy_exclamation_mark: suggested to install under `bash` environment

```
# only first time 
git clone git@github.com:cms-btv-pog/BTVNanoCommissioning.git 

# activate enviroment once you have coffea framework 
conda activate coffea
```
### Coffea installation with Miniconda
For installing Miniconda, see also https://hackmd.io/GkiNxag0TUmHnnCiqdND1Q#Local-or-remote
```
wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh
# Run and follow instructions on screen
bash Miniconda3-latest-Linux-x86_64.sh
```
NOTE: always make sure that conda, python, and pip point to local Miniconda installation (`which conda` etc.).

You can either use the default environment `base` or create a new one:
```
# create new environment with python 3.7, e.g. environment of name `coffea`
conda create --name btv_nano_commissioning python=3.7
# activate environment `coffea`
conda activate btv_nano_commissioning
```
You could simply create the environment through the existing `env.yml` under your conda environment
```
conda env create -f env.yml -p ${conda_dir}/envs/coffea
```

Or install manually for the required packages, coffea, xrootd, and more:
```
pip install git+https://github.com/CoffeaTeam/coffea.git #latest published release with `pip install coffea`
conda install -c conda-forge xrootd
conda install -c conda-forge ca-certificates
conda install -c conda-forge ca-policy-lcg
conda install -c conda-forge dask-jobqueue
conda install -c anaconda bokeh 
conda install -c conda-forge 'fsspec>=0.3.3'
conda install dask
```

Once the environment is set up, compile the python package:
```
pip install -e .
```

### Other installation options for coffea
See https://coffeateam.github.io/coffea/installation.html
### Running jupyter remotely
See also https://hackmd.io/GkiNxag0TUmHnnCiqdND1Q#Remote-jupyter

1. On your local machine, edit `.ssh/config`:
```
Host lxplus*
  HostName lxplus7.cern.ch
  User <your-user-name>
  ForwardX11 yes
  ForwardAgent yes
  ForwardX11Trusted yes
Host *_f
  LocalForward localhost:8800 localhost:8800
  ExitOnForwardFailure yes
```
2. Connect to remote with `ssh lxplus_f`
3. Start a jupyter notebook:
```
jupyter notebook --ip=127.0.0.1 --port 8800 --no-browser
```
4. URL for notebook will be printed, copy and open in local browser



## Structure

### Test 
Example worfkflow for ttbar is included. 

Each workflow can be a separate "processor" file, creating the mapping from NanoAOD to
the histograms we need. Workflow processors can be passed to the `runner.py` script 
along with the fileset these should run over. Multiple executors can be chosen 
(for now iterative - one by one, uproot/futures - multiprocessing and dask-slurm). 

To run the example, run:
```
python runner.py --workflow ttcom
```

Example plots can be found in ` make_some_plots.ipynb` though we might want to make
that more automatic in the end.

To test a small set of files to see whether the workflows run smoothly, run:
```
python runner.py --workflow ${workflow} --json metadata/test.json 
```

## Scale-out (Sites)

Scale out can be notoriously tricky between different sites. Coffea's integration of `slurm` and `dask`
makes this quite a bit easier and for some sites the ``native'' implementation is sufficient, e.g Condor@DESY.
However, some sites have certain restrictions for various reasons, in particular Condor @CERN and @FNAL.

### Condor@FNAL (CMSLPC)
Follow setup instructions at https://github.com/CoffeaTeam/lpcjobqueue. After starting 
the singularity container run with 
```bash
python runner.py --wf ttcom --executor dask/lpc
```

### Condor@CERN (lxplus)
Only one port is available per node, so its possible one has to try different nodes until hitting
one with `8786` being open. Other than that, no additional configurations should be necessary.

```bash
python runner.py --wf ttcom --executor dask/lxplus
```

### Coffea-casa (Nebraska AF)
Coffea-casa is a JupyterHub based analysis-facility hosted at Nebraska. For more information and setup instuctions see
https://coffea-casa.readthedocs.io/en/latest/cc_user.html

After setting up and checking out this repository (either via the online terminal or git widget utility run with
```bash
python runner.py --wf ttcom --executor dask/casa
```
Authentication is handled automatically via login auth token instead of a proxy. File paths need to replace xrootd redirector with "xcache", `runner.py` does this automatically.


### Condor@DESY 
```bash
python runner.py --wf ttcom --executor dask/condor
```

### Maxwell@DESY 
```bash
python runner.py --wf ttcom --executor parsl/slurm
```


## Make the json files

Use the `fetch.py` in `filefetcher`, the `$input_DAS_list` is the info extract from DAS, and output json files in `metadata/`

```
python fetch.py --input ${input_DAS_list} --output ${output_json_name} --site ${site}
```

## Create compiled corretions file(`pkl.gz`)

Compile correction pickle files for a specific JEC campaign by changing the dict of jet_factory, and define the MC campaign and the output file name by passing it as arguments to the python script:

```
python -m utils.compile_jec UL17_106X data/JME/UL17_106X/jec_compiled.pkl.gz
```
## Config file
The config file in `.py` format is passed as the argument `--cfg` of the `runner.py` script. The file has the following structure:

| Parameter name    | Allowed values               | Description
| :-----:           | :---:                        | :------------------------------------------
| `dataset`         | string                       | Path of .txt file with list of DAS datasets
| `json`            | string                       | Path of .json file to create with NanoAOD files
| `storage_prefix`  | string                       | Path of storage folder to save datasets
| `workflow`        | 'base', 'mem'                | Workflow to run
| `input`           | string                       | Path of .json file, input to the workflow
| `output`          | string                       | Path of output folder
| `executor`        | 'futures', 'parsl/slurm'     | Executor
| `workers`         | int                          | Number of parallel threads (with futures)
| `scaleout`        | int                          | Number of jobs to submit (with parsl/slurm)
| `chunk`           | int                          | Chunk size
| `max`             | int                          | Maximum number of chunks to process
| `skipbadfiles`    | bool                         | Skip bad files
| `voms`            | string                       | Voms parameters (with condor)
| `limit`           | int                          | Maximum number of files per sample to process
| `finalstate`      | 'dilepton'                   | Final state of ttHbb process
| `preselections`   | list                         | List of preselection cuts
| `categories`      | dict                         | Dictionary of categories with cuts to apply
| `variables`       | $VARNAME : {$PARAMETERS}     | Dictionary of variables in 1-D histograms and plotting parameters
| `variables2d`     | n.o.                         | __To be implemented__
| `scale`           | 'linear', 'log'              | y-axis scale to apply to plots

The variables' names can be chosen among those reported in `parameters.allhistograms.histogram_settings`, which contains also the default values of the plotting parameters. If no plotting parameters are specified, the default ones will be used.

The plotting parameters can be customized for plotting, for example to rebin the histograms. In case of rebinning, the binning used in the plots has to be compatible with the one of the input histograms.

The `Cut` objects listed in `preselections` and `categories` have to be defined in `parameters.cuts.baseline_cuts`. A library of pre-defined functions for event is available in `lib.cut_functions`, but custom functions can be defined in a separate file.



## Plotting code

- data/MC comparison code

```python
python -m plotting.plotdataMC --lumi ${lumi} --phase ctag_ttdilep_sf --output ctag_ttdilep_sf (--discr zmass --log True/False --data data_runD)
# lumi in /pb
# phase = workflow 
# output coffea file output = hist_$output$.coffea 
# discr = input variables, the defaults are the discriminators, can add multiple variables with space
# log = logorithm on y-axis
# data = data name
```

- data/data, MC/MC comparison

```python
python -m plotting.comparison --phase ctag_ttdilep_sf --output ctag_ttdilep_sf -ref 2017_runB --compared 2017_runC 2017_runD (--discr zmass --log True/False --sepflav True/False)
# phase = workflow 
# output coffea file output = hist_$output$.coffea 
# ref = reference data/MC sample
# comapred = 
# discr = input variables, the defaults are the discriminators, can add multiple variables with space
# log = logorithm on y-axis
# sepflav = separate the jets into different flavor
```
