# burst-trigger-toy

Run 

$python deadtime-pipeline.py 

to get command line options.

E.g. 
$ python deadtime-pipeline.py 10000 50000.0 0.1 21.6 5 1

10000 simulated triggers, 50kHz average trigger rate ("ungated"), >=0.1us deadtime between triggers on the APV, 21.6us readout time of the APV, pipeline depth of 5 and 1= use TI rules (see code for setting).

