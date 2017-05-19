from mininet.topo import Topo
from mininet.net import Mininet

class DCellTop (Topo):
	
	def build(self, n=4, l=1):
		self.bw = 1.5
		self.delay = 5
		self.time = 200
		find_t_k(n, l)
		self.swtiches = {}
		build_topology([], n, l)
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
			switch_id = '_'.join(pref)
			dcell_z_switch = self.addSwitch('sz' + switch_id)
			#self.switches['sz' + switch_id] = dcell_z_switch
			for i in range(0, n):
				inner_switch_z_id = switch_id + "_" + str(i)
				# host to host connections
				switch_z = self.addSwitch('s' + inner_switch_z_id)	
				host_z = self.addHost('h' + inner_switch_z_id)
				self.addLink(host_z, switch_z, bw=self.bw, delay=self.delay)
				self.addLink(host_z, dcell_z_switch, bw=self.bw, delay=self.delay)	
			return
		else:
			for i in range(0,  self.t_ks[l-1] + 1):
				build_topology(pref + [i], n, l-1)
			

			for i in range(0, self.t_ks[l-1]):
				for j in range(0, self.t_ks[l-1] + 1):
					uid1 = j-1
					uid2 = i
					node1_pref = pref + [i, uid1]
					node1_id = 's' + '_'.join(node1_pref)
					node2_pref = pref + [j, uid2]
					node2_id = 's' + '_'.join(node2_pref)
					self.addLink(node1_id, node2_id, bw=self.bw, delay=self.delay)



if __name__ == "__main__":
	topo = DCellTop()

