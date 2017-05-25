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

from pox.core import core
import pox.openflow.libopenflow_01 as of

log = core.getLogger()

# Switches we know of.  [dpid] -> Switch
switches = {}


class DCellSwitch (object):
  def __init__ (self):
    self.connection = None
    self.dpid = None

  def connect (self, connection):
    assert(connection is not None)
    if self.dpid is None:
      self.dpid = connection.dpid
    assert self.dpid == connection.dpid
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

  def __init__ (self, numSwitches):
    core.openflow.addListeners(self)
    self.numSwitches = numSwitches
    self.switchCounter = 0

  def _handle_ConnectionUp (self, event):
    log.info("Connection %s" % (event.connection,))
    sw = switches.get(event.dpid)
    if sw is None:
      sw = DCellSwitch()
      switches[event.dpid] = sw
      sw.connect(event.connection)
      self.switchCounter+=1
      if self.switchCounter == self.numSwitches:
        installAllPaths()
    else:
      log.warning("Reconnecting. DPID = " + str(event.dpid) + ", switchCounter = " + self.switchCounter)
      sw.connect(event.connection)

  def installAllPaths():
    pass



def launch ():
  """
  Starts the component
  """
  def start_switch (event):
    log.debug("Controlling %s" % (event.connection,))
    Tutorial(event.connection)
  core.openflow.addListenerByName("ConnectionUp", start_switch)
