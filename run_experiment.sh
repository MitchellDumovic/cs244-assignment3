# !/bin/bash
cd pox/pox/ext
sudo rm -f h00_h43_iperf.txt
sudo rm -f tcpdump_s10.txt
sudo rm -rf iperfs
mkdir iperfs
sudo mn -c
sudo python build_topology.py 4 1 1
sudo python build_topology.py 4 1 2 
sudo python plot_throughput.py -f h00_h43_iperf.txt -o ../../../throughput.png
sudo python plot_alternative_throughput.py -f tcpdump_s10.txt -o ../../../alternative-throughput.png
sudo python plot_experiment2.py -d ./iperfs/ -o ../../../experiment_2_throughput.png
cd ../../../
