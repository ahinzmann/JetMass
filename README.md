# JetMass
[![flake8](https://github.com/UHH2/JetMass/actions/workflows/lint.yml/badge.svg)](https://github.com/UHH2/JetMass/actions/workflows/lint.yml)

This repository is home of the code for two W & top jet mass related analyses: the measurement of jet mass scale (JMS) data-to-simulation scale factors in the hadronic ($W(q\bar{q}$)+jets) and semileptonic processes ($t \bar{t} \rightarrow \mu \nu$+ jets)  and the 2D likelihood-based unfolding of the jet mass in the hadronic channel.

Both analyses run off of the custom UHH2 MiniAOD N-tuples in the [UHH2 framework](https://github.com/UHH2/UHH2). To install the UHH2 modules, simply clone the repo into a valid `10_6_X` UHH2 installation and add the directory to the `Makefile.local` and run `make` in the `UHH2` directory.
The first step is to run the pre-selection in the UHH2 framework. The config-files for all UL-years and the two samples can be found in the `config/` sub-directory. The cpp-modules can be found in the `include/` and `src/` sub-directories. The pre-selection module will write flat ROOT-trees for data and each signal- and background-mc holding the necessary physics objects and variables of the (pre-)selected events.

Once the flat-trees are produced templates/histograms are filled using `coffea`. See [python/README.md](python/README.md) for detailed instructions.  

The templates are then used in maximum-likelihood fits using the [rhalphalib](https://github.com/nsmith-/rhalphalib)-package and [combine](http://cms-analysis.github.io/HiggsAnalysis-CombinedLimit/). See [rhalph/README.md](rhalph/README.md) for detailed instructions.  

## W/Z+jets EW-Correction and QCD k-factors
- make sure to get ROOT files from 
[UHHNtupleConverter](https://github.com/Diboson3D/UHHNtupleConverter):

```
mkdir NLOWeights; cd NLOWeights
wget https://github.com/Diboson3D/UHHNtupleConverter/raw/master/NLOweights/WJetsCorr.root
wget https://github.com/Diboson3D/UHHNtupleConverter/raw/master/NLOweights/ZJetsCorr.root
```


## setting up python `venv`
- make sure to have python 3.9 installed
- most python scripts will use the venv - they have the python-wrapper `bin/pythonJMS.sh` in their shebang (i.e. `#!/usr/bin/env pythonJMS.sh`)
  - make sure to have `JetMass/bin` in your `$PATH`
  - in order to create the python venv do:
    ```
    python -m venv <venv-path-wherever>
    source <venv-path-wherever>/bin/activate
    pip install pip --upgrade
    pip install -r python/requirements.txt
    deactivate
    ```
  - adjust `VENVPYTHON` in [bin/pythonJMS.sh#L6](bin/pythonJMS.sh#L6)