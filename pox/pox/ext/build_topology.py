import sys
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.node import OVSController
from mininet.node import Controller
from mininet.node import RemoteController
from mininet.util import dumpNodeConnections
from mininet.cli import CLI
sys.path.append("../../")
from pox.ext.id_generator import SwitchIDGenerator
from time import sleep, time
topo_id_gen = SwitchIDGenerator()
class DCellTop (Topo):
	
	def build(self, n=4, l=1):
		print n
		print l
		self.bw = 100
		self.delay = 5
		self.time = 200
		self.find_t_k(n, l)

		init_pref = []
		if l == 0:
			init_pref = ["0"]
		self.build_topology(init_pref, n, l)
		# self.build_trivial_topology()
		print 'done building'

	def find_t_k(self, n, l):
		result = []
		t = n
		k = 0
		while (k <= l):
			result.append(t)
			t = t*(t+1)
			k += 1
		self.t_ks = result

	def get_g(self, k):
		return self.t_ks[k-1] + 1

	def get_t(self, k):
		return self.t_ks[k]

	def gen_name(self, pref, n_type):	
		node_id = "%s%s" % (n_type, ''.join(pref))
		return node_id

	def build_topology(self, pref, n, l):
		if l == 0:
			masterswitch = self.gen_name(pref, "m")
			topo_id_gen.ingestByName(masterswitch)
			macMaster = topo_id_gen.getMac()
			dpidMaster = topo_id_gen.getDPID()
			self.addSwitch(masterswitch, mac=macMaster, dpid=dpidMaster)
			print masterswitch, macMaster, dpidMaster
			for i in range(0, n):
				new_pref = pref + [str(i)]

				innerswitch = self.gen_name(new_pref, "s")
				topo_id_gen.ingestByName(innerswitch)
				macSwitch = topo_id_gen.getMac()
				dpidSwitch = topo_id_gen.getDPID()
				print innerswitch, macSwitch, dpidSwitch
				self.addSwitch(innerswitch, mac=macSwitch, dpid=dpidSwitch)

				innerhost = self.gen_name(new_pref, "h")
				topo_id_gen.ingestByName(innerhost)
				macHost = topo_id_gen.getMac()
				dpidHost = topo_id_gen.getDPID()
				ipHost = topo_id_gen.getIP()
				print innerhost, macHost, dpidHost, ipHost
				self.addHost(innerhost, mac=macHost, dpid=dpidHost, ip=ipHost)
				
				print "linking %s %s:" % (innerswitch, innerhost)
				# switch to host is port 1 for both switch and host
				self.addLink(innerswitch, innerhost, bw=self.bw, port1=1, port2=1)
				print "linking %s %s:" % (innerswitch, masterswitch)
				# switch to master switch is 2 for switch and i+1 for master switch
				self.addLink(innerswitch, masterswitch, bw=self.bw, port1=2, port2=i+1)
		else:
			for i in range(0,  self.get_g(l)):
				self.build_topology(pref + [str(i)], n, l-1)
			

			for i in range(0, self.get_t(l-1)):
				for j in range(i + 1, self.get_g(l)):
					n1 = self.gen_name(pref + [str(i), str(j-1)], "s")
					n2 = self.gen_name(pref + [str(j), str(i)], "s")
					self.addLink(n1, n2, bw=self.bw, port1=3, port2=3)
					print "linking %s %s:" % (n1, n2)


def start_iperf(net, name1, name2):
	h1 = net.get(name1)
	h2 = net.get(name2)

	print "Starting iperf server..."
	
	server = h2.popen("iperf -s")
	output_file = "./%s_%s_iperf.txt" % (name1, name2)
	
	iperf_cmd = "iperf -c %s -t %d > %s -i 1" % (h2.IP(), 30, output_file)
	
	client = h1.popen(iperf_cmd, shell=True)

def main():
	assert len(sys.argv) == 3
	n = int(sys.argv[1])
	l = int(sys.argv[2])
	topo = DCellTop(n, l)
	net = Mininet(topo=topo, host=CPULimitedHost, link = TCLink, controller=RemoteController)
        net.start()

	CLI(net)
		
	start_time = time()
	start_iperf(net, "h00", "h43")

	link_destroyed = False
	while True:
		sleep(5)
		now = time()
		delta = now - start_time
		if delta > 15 and not link_destroyed:
			net.delLinkBetween("s03", "s40")
			link_destroyed = True
		if delta > 30:
			break
	net.stop()

if __name__ == "__main__":
	main()

