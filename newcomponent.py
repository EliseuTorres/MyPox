# write another simple component which listens to
# discovery events and logs them and use Mininet's link
# command to put links up and down


from pox.lib.revent import *
from pox.lib.util import dpid_to_str, str_to_bool
from pox.core import core
import pox.openflow.libopenflow_01 as of
import pox.openflow.discovery as discovery

log = core.getLogger()

class Mycomponent (object)

  def __init__ (self):
    core.openflow.addListeners(self)
    core.openflow_discovery.addListeners(self)
 
  def _handle_LinkEvent (self, event):
	if event.added: ifconfig event.port_for_dpid up
	   log.debug("Switch %s has come up.", dpid_to_str(event.dpid))
	if event.removed: ifconfig event.port_for_dpid up
	   log.debug("Switch %s has come up.", dpid_to_str(event.dpid))

    log.debug("Switch %s has come up.", dpid_to_str(event.dpid))
 
def launch (): 
   core.registerNew(Mycomponent)

 
 




     
