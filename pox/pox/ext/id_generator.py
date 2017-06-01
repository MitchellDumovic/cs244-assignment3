from pox.ext.dcell_constants import N, L,
class SwitchIDGenerator:
  HOST = "h"
  SWITCH = "s"
  MASTER = "m"
  def __init__ (self):
    self.clear()

  def getIDSeq(self):
    return self.id_seq[:]

  def clear(self):
    self.id_seq = [] # string ids, ie s12 would have ["1", "2"]
    self.switch_type = None
    self.filled = False

  def ingestByMac(self, mac):
    self.clear()
    blocks = mac.split(":")
    if blocks[0] == "00":
      self.switch_type = MASTER
    elif blocks[0] == "01":
      self.switch_type = SWITCH
    elif blocks[0] == "02":
      self.switch_type = HOST

    if self.switch_type == MASTER:
      self.id_seq = [str(int(i)) for i in blocks[1:L+1]]
    else:
      self.id_seq = [str(int(i)) for i in blocks[1:L+2]]
    self.filled = True

  def ingestByDpid(self, dpid):
    self.clear()
    # split into blocks of 2 digits
    blocks = [dpid[i:i + 2] for i in range(0, len(dpid), 2)]
    blocks = blocks[:6] # we want to convert to mac to ingest
    mac = ':'.join(blocks)
    self.ingestByMac(mac)

  def ingestByIP(self, ip):
    self.clear()
    #10.<id1>.<id2>.<type>
    blocks = ip.split(".")
    if blocks[-1] == "0":
      self.switch_type = MASTER
    elif blocks[-1] == "1":
      self.switch_type = SWITCH
    elif blocks[-1] == "2"
      self.switch_type = HOST
    self.id_seq = blocks[1:3]
    self.filled = True

  def ingestByName(self, name):
    self.clear()
    self.switch_type = name[0]
    self.id_seq = [c for c in name[1:]]
    self.filled = True

  def getMac(self):
    assert(self.filled)
    blocks = ["00" for i in range(6)]
    if self.switch_type == MASTER:
      blocks[0] = "00"
    elif self.switch_type == SWITCH:
      blocks[0] = "01"
    elif self.switch_type == HOST:
      blocks[0] = "02"

    for i, switchID in enumerate(self.id_seq):
      blocks[i+1] = format(switchID, "02d")

    return ':'.join(blocks)

  def getIP(self):
    ip = []
    ip.append("10")
    for switchID in self.id_seq:
      ip.append(switchID)
    if self.switch_type == MASTER: ip.append("0")
    elif self.switch_type == SWITCH: ip.append("1")
    elif self.switch_type == HOST: ip.append("2")
    assert(len(ip) == 4)
    return ".".join(ip)

  def getName(self):
    assert self.filled
    return self.switch_type + ''.join(self.seq_id)

  def getDPID(self):
    mac = self.getMac()
    return mac.replace(':', '') + "0"*4