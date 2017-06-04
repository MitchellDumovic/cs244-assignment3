from helper import *
import plot_defaults

from matplotlib.ticker import MaxNLocator

from pylab import figure
import argparse
parser = argparse.ArgumentParser()

parser.add_argument('--file', '-f', help="Iperf output file to plot", required=True, action="store")
parser.add_argument('--out', '-o', help="Output png file for the plot.", default=None)

args = parser.parse_args()

def parse_iperf(fname):
	ret = []
	lines = open(fname).readlines()
	time = 1.0
	for line in lines:
		if 'bits/sec' not in line:
			continue
		try:
			split = line.split('Bytes')
			last = split[-1].strip()
			split = last.split(' ')
			ret.append([time, float(split[0])])
			time+=1.0
		except:
			break
	return ret


m.rc('figure', figsize=(16,6))
fig = figure()
ax = fig.add_subplot(111)

data = parse_iperf(args.file)
xaxis = map(float, col(0, data))
throughputs = map(float, col(1, data))
ax.plot(xaxis, throughputs, lw=2)
ax.xaxis.set_major_locator(MaxNLocator(4))
axes = plt.gca()
axes.set_ylim([0, 100])
plt.xlabel("Time (seconds)")
plt.ylabel("Throughput (Mbits/sec)")
plt.grid(True)
plt.tight_layout()

if args.out:
	plt.savefig(args.out)
else:
	plt.show()
