from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.node import OVSController
from mininet.util import dumpNodeConnections
from mininet.cli import CLI
class DCellTop (Topo):
	
	def build(self, n=4, l=1):
		self.bw = 1.5
		self.delay = 5
		self.time = 200
		self.find_t_k(n, l)
		self.build_topology([], n, l)
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

	def build_topology(self, pref, n, l):
		if l == 0:
			switch_id = ''.join(pref)
			dcell_z_switch = self.addSwitch('sz1' + switch_id)
			for i in range(0, n):
				inner_switch_z_id = switch_id + str(i)
				# host to host connections
				switch_z = self.addSwitch('s' + inner_switch_z_id)
				host_z = self.addHost('h' + inner_switch_z_id)
				self.addLink(host_z, switch_z, bw=self.bw, delay=self.delay)
				self.addLink(switch_z, host_z, bw=self.bw, delay=self.delay)
				self.addLink(switch_z, dcell_z_switch, bw=self.bw)
			return
		else:
			for i in range(0,  self.t_ks[l-1] + 1):
				self.build_topology(pref + [str(i)], n, l-1)
			

			for i in range(0, self.t_ks[l-1]):
				for j in range(i + 1, self.t_ks[l-1] + 1):
					uid1 = j-1
					uid2 = i
					node1_pref = pref + [str(i), str(uid1)]
					node1_id = 's' + ''.join(node1_pref)
					node2_pref = pref + [str(j), str(uid2)]
					node2_id = 's' + ''.join(node2_pref)
					self.addLink(node1_id, node2_id, bw=self.bw)



def main():
	topo = DCellTop()
	net = Mininet(topo=topo, host=CPULimitedHost, link = TCLink, controller=OVSController)
        net.start()
	

	CLI(net)

	dumpNodeConnections(net.hosts)
	net.pingAllFull()
	net.stop()

if __name__ == "__main__":
	main()

