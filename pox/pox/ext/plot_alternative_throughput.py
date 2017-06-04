from helper import *
import plot_defaults

from matplotlib.ticker import MaxNLocator
from datetime import datetime
from pylab import figure
import argparse
parser = argparse.ArgumentParser()

parser.add_argument('--file', '-f', help="Iperf output file to plot", required=True, action="store")
parser.add_argument('--out', '-o', help="Output png file for the plot.", default=None)

args = parser.parse_args()

def parse_tcpdump(fname):
	ret = []
	lines = open(fname).readlines()

	bucket = -1
	packetnum = 0
	firstBucket = -1
	for line in lines:
		timestamp = line.split(' ')[0]
		time = datetime.strptime(timestamp, '%H:%M:%S.%f')
		diff = time - datetime(1900, 1, 1)
		seconds = diff.total_seconds()
		packetnum += 1
		if bucket == -1:
			firstBucket = seconds
			bucket = seconds
		elif seconds - bucket > 0.5:
			bucket += 0.5
			ret.append([bucket - firstBucket, packetnum])
			packetnum = 0
	return ret


m.rc('figure', figsize=(16,6))
fig = figure()
ax = fig.add_subplot(111)

data = parse_tcpdump(args.file)
xaxis = map(float, col(0, data))
throughputs = map(float, col(1, data))
ax.plot(xaxis, throughputs, lw=2)
ax.xaxis.set_major_locator(MaxNLocator(4))
axes = plt.gca()
plt.xlabel("Time (seconds)")
plt.ylabel("Packets seen over alternate route")
plt.grid(True)
plt.tight_layout()

if args.out:
	plt.savefig(args.out)
else:
	plt.show()
