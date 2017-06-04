# Reproducing our results

Create a Google Cloud instance running Ubuntu/Linux (we used n1-standard-4, with 4vCPUs and 15GB memory).

Install mininet (we found that the easiest way to do this is to install from source, following the instructions on: http://www.brianlinkletter.com/how-to-install-mininet-sdn-network-simulator/ 

Install matplotlib (run sudo apt-get install python-matplotlib)

Clone our repository (run https://github.com/MitchellDumovic/cs244-assignment3.git)

Navigate into the repository (run cd cs244-assignment3)

In the home directory of the repository is a script called run_experiment.sh. This script will run both experiments and plot the results. Note that in order to run this experiment, you need root access for the instance. To run the script, run:
	Chmod +x run_experiment.sh
	./run_experiment.sh

The script will generate 3 figures into the repository’s home directory. The figures are:
	throughput.png: (reproduction of Figure 5 above)
	alternative-throughput.png: (reproduction of Figure 6 above)
	experiment_2_throughput.png: (reproduction of Figure 7 above)

