# !/bin/bash
sudo rm -f h00_h43_iperf.txt
sudo rm -f tcpdump_s10.txt
sudo mn -c
echo 'starting pox'
sudo ../../pox.py log.level --ERROR --openflow=ERROR dcell_controller > /dev/null &
PID=$!
echo 'starting build topology'
sudo python ./build_topology.py 4 1
echo 'finshed build topology, killing pox'
sudo kill $PID
echo 'killed pox, plotting'
sudo python ./plot_throughput.py -f h00_h43_iperf.txt -o throughput.png
sudo python ./plot_alternative_throughput.py -f tcpdump_s10.txt -o alternative-throughput.png
