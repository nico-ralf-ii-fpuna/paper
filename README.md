# Paper

Code for paper we submitted to the ERRC 2017 conference in Santa Maria, Brazil.

This is a simple implementation of a Web Application Firewall (WAF) based on Anomaly Detection using One Class SVM.


## Getting Started

Tested with Python 3.5 on Ubuntu 14.04 and Windows 7

1. Install dependencies
```
cd paper
pip install -r requirements.txt
```
_If there are problems on Windows with some packages, Anaconda can be used to install them_.
_In Ubuntu using `pip` should just work fine_.

2. Download necessary data sets
    - Paste files from [CSIC 2010 HTTP data sets](http://www.isi.csic.es/dataset/) into `/waf/data_sets/csic/original_files/`
    - Paste files from [CSIC Torpeda 2012 HTTP data sets](http://www.tic.itefi.csic.es/torpeda/datasets.html) into `/waf/data_sets/torpeda/original_files/`

3. Execute the run test files inside the `waf` folder
   like this `python3 run_test_1.py`
   To test the proxy implementation you have to start all the files beginning with `run_test_*` in 
   their listed order (alphabetical order), starting with the data server and concluding with 
   source, waiting some seconds between the executions to give them some time to initialize.

## Authors
- Nico Epp
- Ralf Funk