# -*- coding: cp936 -*-
# Copyright 2011-2013 James McCauley
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
Provides the discovery API for stable topologies on OpenFlow-only networks

This module piggybacks on the normal discovery module, and you can pass any
of the normal discovery commandline options to it.  Links are initially
discovered by the normal discovery, and we monitor link state via PortStatus.
"""
from pox.lib.revent import *
from pox.lib.util import dpid_to_str, str_to_bool
from pox.core import core
import pox.openflow.libopenflow_01 as of
# include port status message
import pox.openflow.discovery as discovery

log = core.getLogger()

class FastDiscovery (EventMixin):
  """
  Component that attempts to discover network toplogy.

  Listen to the discovery component, set up or set down the link based on the portstatus
  """

  _eventMixin_events = set([
    discovery.LinkEvent,
  ])

  _core_name = "openflow_discovery" # we want to be core.openflow_discovery

   Link = discovery.Discovery.Link                                    
                                  

  def __init__ (self):
    core.slow_discovery.addListeners(self)  # slow_discovery refers to the nomal discovery and it could raise LinkEvent
    
    self.up = {}                            # Link -> Boolean (up/down)
  
    core.openflow.addListenerByName("PortStatus", _handle_PortStatus) #Listen to port status messages     

  def _handle_LinkEvent (self, event):
    #If link up, add to self.up or set state to up; here we only care about the link up event
    if event.added: self.up[event.link]=1
        log.debug("link %s is down", event.link) 
        self.raiseEventNoErrors(LinkEvent, True, event.link)   
 
  def _handle_PortStatus (self, event):

    if event.deleted or event.ofp.desc.state & OFFP_LINK_DOWN
         #the port is down#
         log.debug("port %s is down", event.port_for_dpid) 
         del self.up[event.link]
         self.raiseEventNoErrors(LinkEvent, False, event.link)
    return 
    
    

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


  def launch (no_flow = False, explicit_drop = True, link_timeout = None,
            eat_early_packets = False):
  explicit_drop = str_to_bool(explicit_drop)
  eat_early_packets = str_to_bool(eat_early_packets)
  install_flow = not str_to_bool(no_flow)
  if link_timeout: link_timeout = int(link_timeout)

  old_discovery = discovery.Discovery(explicit_drop=explicit_drop,
      install_flow=install_flow, link_timeout=link_timeout,
      eat_early_packets=eat_early_packets)
  core.register("slow_discovery", old_discovery) #register as core.slow_discovery
  core.registerNew(FastDiscovery) # register as core.openflow_discovery
  
