from pox.lib.revent import *
from pox.lib.util import dpid_to_str, str_to_bool
from pox.core   import  core 
import pox.openflow.discovery as discovery
from pox.lib.util import assert_type, initHelper, dpid_to_str
from pox.lib.revent import Event, EventMixin
from pox.openflow.libopenflow_01 import *
import pox.openflow.libopenflow_01 as of
from pox.openflow.util import make_type_to_unpacker_table
from pox.openflow.flow_table import SwitchFlowTable
from pox.lib.packet import *
import logging


log = core.getLogger()

class LinkEvent (Event):
  """
  Link up/down event
  """
  def __init__ (self, add, link):
    Event.__init__(self)
    self.link = link
    self.added = add
    self.removed = not add

  def port_for_dpid (self, dpid):
    if self.link.dpid1 == dpid:
      return self.link.port1
    if self.link.dpid2 == dpid:
      return self.link.port2
    return None

class ExpireLink (Event):
    def __init__ (self,link):
        Event.__init__(self)
        self.link = link

    def port_for_dpid (self, dpid):
        if self.link.dpid1 == dpid:
            return self.link.port1
        if self.link.dpid2 == dpid:
            return self.link.port2
        return None



class FastDiscovery (EventMixin):
  """
  Component that attempts to discover network toplogy.
  Listen to the discovery component, set up or set down the link based on the portstatus
  """
  _eventMixin_events = set([
    discovery.LinkEvent,
    discovery.ExpireLink
  ])

  _core_name = "openflow_discovery" # we want to be core.openflow_discovery

  Link = discovery.Discovery.Link
  LinkEvent = discovery.LinkEvent
                                    
  def __init__ (self):
    self.up = {} 
    core.slow_discovery.addListeners(self)  # slow_discovery refers to the nomal discovery 
    core.listen_to_dependencies(self)
                              
   
  def _handle_LinkEvent (self, event):
  ##If link up, add to self.up or set state to up; here we only care about the link up event
    if event.added:     
         self.up[event.link]=[True,True]
         log.debug("link %s is up" % str(event.link)) 
         self.raiseEventNoErrors(LinkEvent, True, event.link)  

  def _handle_ExpireLink (self, event):
      if self.up[event.link] == [True, True]:
##          self.up[event.link] = [False, False]
          log.debug("link %s is down because of link between normal switches" % str(event.link))
          self.raiseEventNoErrors(LinkEvent, False, event.link)

  def _handle_openflow_PortStatus (self, event):
    if (event.deleted or (event.ofp.desc.state & OFPPS_LINK_DOWN)):
         #the port is down#                  
         log.debug("status of %s 's port %s have changed to or is down" % (str(event.dpid),str(event.port)))
         expired = [link for link in self.up
                       if (link.port1 == event.port and link.dpid1==event.dpid) or (link.port2 == event.port and link.dpid2==event.dpid)]

         for link in expired:
              if (link.port1 == event.port): self.up[link][0]=False
              if (link.port2 == event.port): self.up[link][1]=False
              log.debug("link %s is down" % str(link)) 
              self.raiseEventNoErrors(LinkEvent, False, link)

##              if self.up[link] == [False,False]:
##                  log.info("No normal switch exists in the link %s " % str(link))


    elif (event.added or (event.ofp.desc.state & OFPPS_LINK_DOWN)==False ):
           #the port is up#
          log.debug("status of %s 's port %s have changed to or is up" %(str(event.dpid),str(event.port)))
          added = [link for link in self.up
                       if (link.port1 == event.port and link.dpid1==event.dpid) or (link.port2 == event.port and link.dpid2==event.dpid)]
          for link in added:
               if (link.port1 == event.port): self.up[link][0]=True
               if (link.port2 == event.port): self.up[link][1]=True
               if self.up[link] == [True,True]:
                   log.debug("link %s is up" % str(link)) 
                   self.raiseEventNoErrors(LinkEvent, True, link)
     
         
 
  def is_edge_port (self, dpid, port):
    """
    Return True if given port does not connect to another switch
    """
    for link,is_up in self.up.iteritems():
      if link.dpid1 == dpid and link.port1 == port:
        return False
      if link.dpid2 == dpid and link.port2 == port:
        return False
    return True

    


def launch (no_flow = False, explicit_drop = True, link_timeout = None,eat_early_packets = False):
      explicit_drop = str_to_bool(explicit_drop)
      eat_early_packets = str_to_bool(eat_early_packets)
      install_flow = not str_to_bool(no_flow)
      if link_timeout: link_timeout = int(link_timeout)
      old_discovery = discovery.Discovery(explicit_drop=explicit_drop,
      install_flow=install_flow, link_timeout=link_timeout,
      eat_early_packets=eat_early_packets)

      core.register("slow_discovery", old_discovery) #register as core.slow_discovery
      core.registerNew(FastDiscovery) # register as core.openflow_discovery

