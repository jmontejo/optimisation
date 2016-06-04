The idea of the optimisation procedure is the following:

1) rank all variables (following some figure of merit) and select the best ranked variable

2) choose a cut on the best variable and apply this cut for all following steps

3) rank the variables again, select the next variable and apply the next cut

4) this is done, after the change in the selected figure of merit for the optimisation is not improved significantly anymore



For the usage of this optimisation code, one has to follow only few steps

1) setup ATLAS and ROOT (the setup.sh script will most probable only work in Wuppertal)

2) define everything in the configuration file (more details below)

3) "python optimsation.py config.py"

4) you will get some output during the optimisation and also for the final cuts



More information for the configuration:

You can have a look at exapmle-config.py for an easy example how to define the configuration file.

1) you should adapt the signal and the background file location by changing the location and probably also the name of the tree for 

Config.signal = Sample("nice_name", Utils.load_chain(<file_location>, <tree_name>))

and Config.backgrounds = [Sample(...), Sample(...), ...]

2) adapt the Variables which should be used for the optimisation

Config.Variables = {...} by adding variables into this dictionary

To define a variable, you simply have to add:

"name": Range( lowerBoundary, upperBoundary, nBins, direction)

The nBins should be not too fine, otherwise the optimisation needs much longer. A good solution is to select the number of bins such that the selected cuts would end at some round nubmers.
For the direction, a bool is given. If False is choosen, an upper cut value is searched for, if True is choosen a lower cut value will be given in the end.


3) One should define which weights and also which preselection should be used. For this, one need to give the correct strings to

Config.event_weight

Config.preselection

4) For the optimisation, different ranking and optimisation methods can be used. They can be defined by changing "Config.rankingMethod" or "Config.optimisationMethod".

For expample, one can use "sig" which is S / sqrt (B + B * sig_B) for a given background uncertainty sig_B. In order to use the RooStats.NumberCountingUtils.BinomialExpZ function, one need to use "roostats" for the method.

5) Another feature is the possibility to apply a damping fucntion. Using this damping, the first cuts are choosen less tight in order to take into account correlations between different variables better.

This can be used by Config.damp_func = Damp["name"], where different functions are given in configuration.py