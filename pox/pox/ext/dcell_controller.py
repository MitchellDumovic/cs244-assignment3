# Copyright 2012 James McCauley
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at:
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
This component is for use with the OpenFlow tutorial.

It acts as a simple hub, but can be modified to act like an L2
learning switch.

It's roughly similar to the one Brandon Heller did for NOX.
"""
from pox.lib.packet.arp import arp
import pox.lib.packet as pkt
from pox.lib.addresses import EthAddr, IPAddr
from pox.core import core
import pox.openflow.libopenflow_01 as of
import os
import struct
from pox.lib.packet.ipv4 import ipv4
from pox.ext.util import SwitchIDGenerator, GetDCellLink
from pox.ext.dcell_constants import N, L, NUM_SWITCHES
from time import sleep
log = core.getLogger()

# Switches we know of.  [dpid] -> Switch
switches = {}


class DCellSwitch (object):
  def __init__ (self):
    self.connection = None
    self.dpid = None
    self._listeners = None
    self.id_gen = SwitchIDGenerator()
    self.interDCELL_link_failed = False
    self.host_failed = False
    self.flow_msgs = []

  def getHostMac(self):
    assert self.dpid is not None
    # ingest switch's dpid
    self.id_gen.ingestByDpid(self.dpid)
    assert self.id_gen.switch_type == self.id_gen.SWITCH
    self.id_gen.switch_type = self.id_gen.HOST
    return self.id_gen.getMac()

  def install(self, dest_switch, port):
    assert self.connection is not None
    msg = of.ofp_flow_mod()
    msg.match = of.ofp_match(dl_dst = EthAddr(dest_switch.getHostMac()))
    msg.actions.append(of.ofp_action_output(port=port))
    self.connection.send(msg)
    self.flow_msgs.append(msg)

  def connect (self, connection, dpid):
    assert(connection is not None)
    if self.dpid is None:
      self.dpid = dpid
    assert(self.dpid == dpid)
    self.connection = connection
    self._listeners = connection.addListeners(self)
    log.info("Connect %s" % (connection,))

  def disconnect (self):
    if self.connection is not None:
      log.info("Disconnect %s" % (self.connection,))
      self.connection.removeListeners(self._listeners)
      self.connection = None

  def send_arp_reply(self, event):
    # SOURCE: referenced from l3_learning
    packet = event.parsed 
    arp_request = packet.payload
    requested_ip = arp_request.protodst.toStr()
    # get eth answer to arp request
    self.id_gen.ingestByIP(requested_ip)
    mac_str = self.id_gen.getMac()
    hardware_answer = EthAddr(mac_str)

    # generate an arp packet
    arp_reply = pkt.arp()
    arp_reply.opcode = arp_request.REPLY
    # IP addrs are just flipped
    arp_reply.protosrc = arp_request.protodst 
    arp_reply.protodst = arp_request.protosrc
    arp_reply.hwdst = packet.src # hardware dest is the requester's eth
    arp_reply.hwsrc = hardware_answer # hardware src is the mac answer

    #encapsulate this in an ethernet packet
    e = pkt.ethernet(dst=packet.src, src=hardware_answer)
    e.type = e.ARP_TYPE
    e.set_payload(arp_reply)

    #send this packet
    msg = of.ofp_packet_out()
    msg.data = e.pack()
    msg.actions.append(of.ofp_action_output(port=of.OFPP_IN_PORT))
    msg.in_port = event.port
    self.connection.send(msg)

  def GetInterDCellSwitchName(self):
    # we assume port 3. get the switch on the other side of the link
    self.id_gen.ingestByDpid(self.dpid)
    level = int(self.id_gen.getIDSeq()[0])
    name = self.id_gen.getName()
    for i in range(0, N+1):
      if level != i:
        l = GetDCellLink(level, i)
        if l[0] == name: return l[1]
        if l[1] == name: return l[0]
    # should never hit this point
    assert False
    return None

  def getSwitchesInDcell(self, level):
    dcell_switches = []
    for i in range(0, N):
      name = "s" + str(level) + str(i)
      self.id_gen.ingestByName(name)
      dcell_switches.append(switches[self.id_gen.getDPID()])
    return dcell_switches
    
  def handleFailedLink(self):
    self.id_gen.ingestByDpid(self.dpid)
    our_level = int(self.id_gen.getIDSeq()[0])

    other_side_name = self.GetInterDCellSwitchName()
    self.id_gen.ingestByName(other_side_name)
    other_side_level = int(self.id_gen.getIDSeq()[0])

    proxy_level = (other_side_level + 1) % (N+1)
    if proxy_level == our_level:
      proxy_level = (our_level + 1) % (N+1)

    (a_name, b_name) = GetDCellLink(our_level, proxy_level)
    self.id_gen.ingestByName(a_name)
    a = switches[self.id_gen.getDPID()]    

    destination_switches = self.getSwitchesInDcell(other_side_level) # "B" switches
    # for each of these dest switches, change flow table to go to master
    for dest_switch in destination_switches:
      self.install(dest_switch, 2)
    # in master, for each dest switch, go to a instead of current switch
    self.id_gen.ingestByDpid(a.dpid)
    master_proxy_port = int(self.id_gen.getIDSeq()[1])+1
    master_switch_name = "m" + str(our_level)
    self.id_gen.ingestByName(master_switch_name)
    master_switch = switches[self.id_gen.getDPID()]
    for dest_switch in destination_switches:
      master_switch.install(dest_switch, master_proxy_port)
    # in new proxy (a), for every dest in B, route to proxy on other side (b) rather than back to master
    for dest_switch in destination_switches:
      a.install(dest_switch, 3)

  def handleReactivatedLink(self):
    self.id_gen.ingestByDpid(self.dpid)
    our_level = int(self.id_gen.getIDSeq()[0])
    # switch that is now restored
    other_side_name = self.GetInterDCellSwitchName()
    self.id_gen.ingestByName(other_side_name)
    other_side_level = int(self.id_gen.getIDSeq()[0])
    # current proxy that we need to redirect
    proxy_level = (other_side_level + 1) % (N+1)
    if proxy_level == our_level:
      proxy_level = (our_level + 1) % (N+1)

    (a_name, b_name) = GetDCellLink(our_level, proxy_level)
    self.id_gen.ingestByName(a_name)
    a = switches[self.id_gen.getDPID()]

    destination_switches = self.getSwitchesInDcell(other_side_level) # "B" switches
    # for each of these dest switches, change flow table to go through restored link
    for dest_switch in destination_switches:
      self.install(dest_switch, 3)
    # in master, for each dest switch, go to a instead of current switch
    self.id_gen.ingestByDpid(self.dpid)
    master_self_port = int(self.id_gen.getIDSeq()[1])+1
    master_switch_name = "m" + str(our_level)
    self.id_gen.ingestByName(master_switch_name)
    master_switch = switches[self.id_gen.getDPID()]
    # for every destination switch, have master go back to the old exit point
    for dest_switch in destination_switches:
      master_switch.install(dest_switch, master_self_port)

    # in old proxy (a), for every dest in B, route to master rather than across the way
    for dest_switch in destination_switches:
      a.install(dest_switch, 2)

  def _handle_PortStatus(self, event):
    self.id_gen.ingestByDpid(self.dpid)
    if self.id_gen.switch_type != self.id_gen.SWITCH:
	return # there is no action we need to take if it's the master's end
    if event.port != 3:
	# Host failure
	if event.modified and event.ofp.desc.state == 1 and event.port == 1:
		self.host_failed = True
		sleep(5)
	if event.modified and event.ofp.desc.state == 0 and self.host_failed:
		self.host_failed = False
	return # we only care about links that cross DCells (we assume no rack failure)
    curr_switch_name = self.id_gen.getName()
    if event.modified and event.ofp.desc.state == 1 and not self.interDCELL_link_failed:
	# dropped
	if not self.host_failed:
	    sleep(0.5)
	self.handleFailedLink()
        self.interDCELL_link_failed = True # mark link as failed
    elif event.modified and event.ofp.desc.state == 0 and self.interDCELL_link_failed:
        # reactivated
        self.handleReactivatedLink()
        self.interDCELL_link_failed = False # back to normal

  def _handle_PacketIn (self, event):
    """
    Handles packet in messages from the switch.
    """
    packet = event.parsed # This is the parsed packet data.
    if packet.type == packet.ARP_TYPE:
      if packet.payload.opcode == arp.REQUEST:
        # send ARP reply
        self.send_arp_reply(event)

  def _handle_ConnectionDown (self, event):
    self.disconnect()

class dcell_routing (object):
  def __init__ (self):
    core.openflow.addListeners(self)
    self.switchCounter = 0
    self.id_gen = SwitchIDGenerator()

  def _handle_ConnectionUp (self, event):    
    dpidFormatted = struct.pack('>q', event.connection.dpid).encode('hex')
    log.info("Connection %s" % (event.connection,))
    if not dpidFormatted.endswith("00" * 5):
      dpidFormatted = "00" * 8
    sw = switches.get(dpidFormatted)
    if sw is None:
      sw = DCellSwitch()
      switches[dpidFormatted] = sw
      sw.connect(event.connection, dpidFormatted)
      self.switchCounter+=1
      if self.switchCounter == NUM_SWITCHES:
        self.installAllPaths()
    else:
      log.warning("Reconnecting. DPID = " + str(dpidFormatted) + ", switchCounter = " + str(self.switchCounter))
      sw.connect(event.connection, dpidFormatted)
      # Reinstall flow table entries
      for msg in sw.flow_msgs:
	sw.connection.send(msg)


  def installAllPaths(self):
    print "Installing all paths"
    paths = {}
    # by formatted dpids
    for src in switches:
      self.id_gen.ingestByDpid(src)
      if self.id_gen.switch_type == self.id_gen.MASTER: continue # continue if master
      for dst in switches:
        self.id_gen.ingestByDpid(dst)
        if self.id_gen.switch_type == self.id_gen.MASTER: continue
        self.DCellRouting(src, dst, paths)
    
    # Install flow table entries for all switch-switch flows
    for (src, dest), path in paths.items():
      dest_switch = switches[dest]
      prev_switch = None
      for switch in path:
        if prev_switch is None:
          prev_switch = switch
          continue
        # get port from prev_switch going to switch
        port = self.get_port(prev_switch, switch)
        prev_switch.install(dest_switch, port)
        prev_switch = switch
      prev_switch.install(dest_switch, 1)

    print 'done'

  def get_port(self, switch1, switch2):
    self.id_gen.ingestByDpid(switch1.dpid)
    isMaster1 = self.id_gen.switch_type == self.id_gen.MASTER
    self.id_gen.ingestByDpid(switch2.dpid)
    isMaster2 = self.id_gen.switch_type == self.id_gen.MASTER

    assert(not (isMaster1 and isMaster2))
    if isMaster2:
      return 2
    if isMaster1:
      self.id_gen.ingestByDpid(switch2.dpid)
      # the port is the last number in the switch
      return int(self.id_gen.getIDSeq()[-1]) + 1
    return 3

  def DCellRouting(self, src, dest, paths):
    if (src, dest) in paths:
      return paths[(src, dest)]
    if src == dest:
      return [switches[src]]

    self.id_gen.ingestByDpid(src)
    src_list = self.id_gen.getIDSeq()
    self.id_gen.ingestByDpid(dest)
    dest_list = self.id_gen.getIDSeq()

    pref = os.path.commonprefix([src_list, dest_list])
    m = len(pref)

    if (m == L):
      dcellpath = self.findPathInSameDCell(src, dest)
      paths[(src, dest)] = dcellpath
      paths[(dest, src)] = dcellpath[::-1] # reverse
      return dcellpath

    (n1, n2) = self.GetLink(pref, src_list[m], dest_list[m])
    path1 = self.DCellRouting(src, n1, paths)
    path2 = self.DCellRouting(n2, dest, paths)

    path = path1 + path2
    paths[(src, dest)] = path
    paths[(dest, src)] = path[::-1] #reverse

  def findPathInSameDCell(self, src, dst):
    srcSwitch = switches[src]
    destSwitch = switches[dst]

    self.id_gen.ingestByDpid(src)
    master_name = "m" + ''.join(self.id_gen.getIDSeq()[:L])
    self.id_gen.ingestByName(master_name)
    masterDpid = self.id_gen.getDPID()
    assert(masterDpid in switches)
    masterSwitch = switches[masterDpid]
    return [srcSwitch, masterSwitch, destSwitch]

  def GetLink(self, pref, cellId1, cellId2):
    # for now we are ignoring pref since we assume only dcell1
    (n1, n2) = GetDCellLink(int(cellId1), int(cellId2))
    self.id_gen.ingestByName(n1)
    n1dpid = self.id_gen.getDPID()
    self.id_gen.ingestByName(n2)
    n2dpid = self.id_gen.getDPID()
    return (n1dpid, n2dpid)

def launch ():
  """
  Starts the component
  """
  core.registerNew(dcell_routing)
