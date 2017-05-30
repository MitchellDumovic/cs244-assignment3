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
	

class DCellTop (Topo):
	
	def build(self, n=4, l=1):
		print n
		print l
		self.bw = 1.5
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
	def gen_mac(self, pref, n_type):
		assert(len(pref) + 1 < 6)
		blocks = ["00" for i in range(6)]
		firstBlock = "00"
		if n_type == "s":
			blocks[0] = "01"
		elif n_type == "h":
			blocks[0] = "02"
		for i, switchId in enumerate(pref):
			assert(len(switchId) < 3)
			if (len(switchId) == 1):
				blocks[i+1] = "0" + switchId
			else:
				blocks[i+1] = switchId
		return ':'.join(blocks)

	def gen_dpid(self, pref, n_type):
		return self.gen_mac(pref, n_type).replace(':', '') + "0000"

	def build_topology(self, pref, n, l):
		if l == 0:
			masterswitch = self.gen_name(pref, "m")
			macMaster = self.gen_mac(pref, "m")
			dpidMaster = self.gen_dpid(pref, 'm')
			self.addSwitch(masterswitch, mac=macMaster, dpid=dpidMaster)
			print masterswitch, macMaster, dpidMaster
			for i in range(0, n):
				new_pref = pref + [str(i)]
				innerswitch = self.gen_name(new_pref, "s")
				innerhost = self.gen_name(new_pref, "h")
				macSwitch = self.gen_mac(new_pref, "s")
				macHost = self.gen_mac(new_pref, "h")
				dpidSwitch = self.gen_dpid(new_pref, 's')
				dpidHost = self.gen_dpid(new_pref, 'h')
				
				print innerswitch, macSwitch, dpidSwitch
				print innerhost, macHost, dpidHost
				self.addSwitch(innerswitch, mac=macSwitch, dpid=dpidSwitch)
				self.addHost(innerhost, mac=macHost, dpid=dpidHost)
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

	def build_trivial_topology(self):
		# to test controller
		# h1 -> s1 -> s2 -> s3 -> h2
		h1 = self.addHost('h1', mac="00:00:00:00:00:11")
                h2 = self.addHost('h2', mac="00:00:00:00:22:00")
                s1 = self.addSwitch('s1', mac="00:00:00:33:00:00")
                s2 = self.addSwitch('s2', mac="00:00:44:00:00:00")
                s3 = self.addSwitch('s3', mac="00:55:00:00:00:00")
                self.addLink(h1, s1)
		self.addLink(s1, s2)
                self.addLink(s2, s3)
                self.addLink(s3, h2)

def main():
	assert len(sys.argv) == 3
	n = int(sys.argv[1])
	l = int(sys.argv[2])
	topo = DCellTop(n, l)
	net = Mininet(topo=topo, host=CPULimitedHost, link = TCLink, controller=RemoteController)
        net.start()
	

	CLI(net)

	dumpNodeConnections(net.hosts)
	net.pingAllFull()
	net.stop()

if __name__ == "__main__":
	main()

