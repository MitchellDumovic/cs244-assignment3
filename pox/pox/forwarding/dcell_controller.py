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

from pox.lib.addresses import EthAddr
from pox.lib.util import dpid_to_str
from pox.core import core
import pox.openflow.libopenflow_01 as of
import os
import struct

log = core.getLogger()

# Switches we know of.  [dpid] -> Switch
switches = {}

# Hosts [dpid] -> Switch
hosts = {}

def toList(s, l):
  n_type = s[:2]
  length = l
  if n_type != '00':
    length +=1
  arr = [s[i:i + 2] for i in range(2, len(s), 2)]
  return arr[:length]

def fromList(arr):
  result = ""
  if len(arr) == 1:
    result += "00"
  else:
    result += "01"
  for i in range(7):
    if i < len(arr):
      result += arr[i]
    else:
      result += "00"
  return result

class DCellSwitch (object):
  def __init__ (self):
    self.connection = None
    self.dpid = None

  
  def getMac(self):
    return ':'.join([self.dpid[i:i + 2] for i in range(0, 12, 2)])

  def install(self, dest_mac, port):
    msg = of.ofp_flow_mod()
    match = of.ofp_match(dl_dst=EthAddr(dest_mac))
    msg.match = match
    msg.actions.append(of.ofp_action_output(port=port))
    assert self.connection != None
    self.connection.send(msg)

  def connect (self, connection, dpid):
    assert(connection is not None)
    if self.dpid is None:
      self.dpid = dpid
    assert(self.dpid == dpid)
    self.connection = connection
    connection.addListeners(self)
    log.info("Connect %s" % (connection,))

  def disconnect (self):
    if self.connection is not None:
      log.info("Disconnect %s" % (self.connection,))
      self.connection.removeListeners(self._listeners)
      self.connection = None


  def _handle_PacketIn (self, event):
    """
    Handles packet in messages from the switch.
    """
    packet = event.parsed # This is the parsed packet data.
    if not packet.parsed:
      log.warning("Ignoring incomplete packet")
      return

    packet_in = event.ofp # The actual ofp_packet_in message.

    # Comment out the following line and uncomment the one after
    # when starting the exercise.

  def _handle_ConnectionDown (self, event):
    self.disconnect()


class dcell_routing (object):

  def __init__ (self, numSwitches, n, l):
    core.openflow.addListeners(self)
    self.numSwitches = numSwitches
    self.n = n 
    self.l = l
    self.switchCounter = 0

  def _handle_ConnectionUp (self, event):
    print event.connection.dpid, struct.pack('>q', event.connection.dpid).encode("hex")
    
    dpidFormatted = struct.pack('>q', event.connection.dpid).encode('hex')
    log.info("Connection %s" % (event.connection,))
    isHost = dpidFormatted.startswith("02")
    if not dpidFormatted.endswith("00" * 5):
	dpidFormatted = "00" * 8
    sw = None
    if not isHost:
      sw = switches.get(dpidFormatted)
    else:
      sw = hosts.get(dpidFormatted)
    
    if sw is None:
      sw = DCellSwitch()
      if isHost:
	hosts[dpidFormatted] = sw
      else:
        switches[dpidFormatted] = sw
      sw.connect(event.connection, dpidFormatted)
      self.switchCounter+=1
      if self.switchCounter == self.numSwitches:
        self.installAllPaths()
    else:
      log.warning("Reconnecting. DPID = " + str(dpidFormatted) + ", switchCounter = " + self.switchCounter)
      sw.connect(event.connection, dpidFormatted)

  def installAllPaths(self):
    print "Installing all paths"
    paths = {}
    for src in switches:
      if src.startswith('00'):
        continue
      for dst in switches:
        if (dst.startswith('00')):
          continue
        if src == dst:
          continue
        self.DCellRouting(src, dst, paths)
    
    # Install flow table entries for all switch-switch flows
    for (src, dest), path in paths.items():
      dest_switch = switches[dest]
      prev_switch = switches[src]
      for switch in path:
        if switch == prev_switch:
          continue
          # get port from prev_switch going to switch
        port = self.get_port(prev_switch, switch)
        prev_switch.install(dest_switch.getMac(), port)
        prev_switch = switch

  def get_port(self, switch1, switch2):
    isMaster1 = switch1.dpid.startswith('00')
    isMaster2 = switch2.dpid.startswith('00')
    assert(not (isMaster1 and isMaster2))
    if isMaster2:
      return 2
    if isMaster1:
      return int(toList(switch2.dpid, self.l)[-1]) + 1
    return 3


  def DCellRouting(self, src, dest, paths):
    if ((src, dest) in paths):
      return paths[(src, dest)]
    if src == dest:
      return [switches[src]]
    pref = os.path.commonprefix([toList(src, self.l), toList(dest, self.l)])
    m = len(pref)
    if (m == self.l):
      dcellpath = self.findPathInSameDCell(src, dest)
      paths[(src, dest)] = dcellpath
      paths[(dest, src)] = dcellpath
      return dcellpath


    (n1, n2) = self.GetLink(pref, toList(src, self.l)[m], toList(dest, self.l)[m])
    path1 = self.DCellRouting(src, n1, paths)
    path2 = self.DCellRouting(n2, dest, paths)

    path = path1 + path2
    paths[(src, dest)] = path
    paths[(dest, src)] = path

  def findPathInSameDCell(self, src, dst):
    srcSwitch = switches[src]
    destSwitch = switches[dst]

    masterDpid = "00" + src[2:4] + ('00' * 6)
    assert(masterDpid in switches)
    masterSwitch = switches[masterDpid]
    return [srcSwitch, masterSwitch, destSwitch]

  def GetLink(self, pref, cellId1, cellId2):
    s = min(int(cellId1), int(cellId2))
    d = max(int(cellId1), int(cellId2))


    n1Target = (d - 1) % self.n
    n1List = ['0' + str(s), '0' + str(n1Target)]
    n2List = ['0' + str(d), '0' + str(s)]
    n1Dpid = fromList(n1List)
    n2Dpid = fromList(n2List)
    

    if (s == int(cellId1)):
      return (n1Dpid, n2Dpid)
    else:
      return (n2Dpid, n1Dpid)

def launch ():
  """
  Starts the component
  """
  core.registerNew(dcell_routing, 25, 4, 1)
