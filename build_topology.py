import sys
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.node import OVSController
from mininet.node import Controller
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
			print masterswitch
			self.addSwitch(masterswitch)
			for i in range(0, n):
				new_pref = pref + [str(i)]
				innerswitch = self.gen_name(new_pref, "s")
				innerhost = self.gen_name(new_pref, "h")
				print innerswitch
				print innerhost
				self.addSwitch(innerswitch)
				self.addHost(innerhost)
				print "linking %s %s:" % (innerswitch, innerhost)
				self.addLink(innerswitch, innerhost, bw=self.bw, port1=1, port2=1)
				print "linking %s %s:" % (innerswitch, masterswitch)

				self.addLink(innerswitch, masterswitch, bw=self.bw, port1=2, port2=i+1)
		else:
			for i in range(0,  self.get_g(l)):
				self.build_topology(pref + [str(i)], n, l-1)
			

			for i in range(0, self.get_t(l-1)):
				for j in range(i + 1, self.get_g(l)):
					n1 = self.gen_name(pref + [str(i), str(j-1)], "s")
					n2 = self.gen_name(pref + [str(j), str(i)], "s")
					self.addLink(n1, n2, bw=self.bw, port1=3+ i, port2=3+j)
					print "linking %s %s:" % (n1, n2)

	def build_trivial_topology(self):
		# to test controller
		# h1 -> s1 -> s2 -> s3 -> h2
		h1 = self.addHost('h1')
                h2 = self.addHost('h2')
                s1 = self.addSwitch('s1')
                s2 = self.addSwitch('s2')
                s3 = self.addSwitch('s3')
                self.addLink(h1, s1)
                self.addLink(s2, s3)
                self.addLink(s3, h2)

def main():
	assert len(sys.argv) == 3
	n = int(sys.argv[1])
	l = int(sys.argv[2])
	topo = DCellTop(n, l)
	net = Mininet(topo=topo, host=CPULimitedHost, link = TCLink, controller=OVSController)
        net.start()
	

	CLI(net)

	dumpNodeConnections(net.hosts)
	net.pingAllFull()
	net.stop()

if __name__ == "__main__":
	main()

