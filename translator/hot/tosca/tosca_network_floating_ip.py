#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from translator.hot.syntax.hot_resource import HotResource

# Name used to dynamically load appropriate map class.
TARGET_CLASS_NAME = 'ToscaFloatingIP'
TOSCA_LINKS_TO = 'tosca.relationships.network.LinksTo'

class ToscaFloatingIP(HotResource):
    '''Translate TOSCA node type tosca.nodes.network.Network.'''

    toscatype = 'tosca.nodes.network.FloatingIP'
    FLOATING_IP_PROPS = ['floating_network']

    existing_resource_id = None

    def __init__(self, nodetemplate, csar_dir=None):
        super(ToscaFloatingIP, self).__init__(nodetemplate,
                                           type='OS::Neutron::FloatingIP',
                                           csar_dir=csar_dir)
        pass

    def handle_properties(self):
        tosca_props = self.get_tosca_props()
        floating_ip_props = {}
        for key, value in tosca_props.items():
            if key in self.FLOATING_IP_PROPS:
                if key == 'floating_network':
                    floating_ip_props[key] = value

        links_to = None
        for rel, node in self.nodetemplate.relationships.items():
            # Check for LinksTo relations. If found add a port property with
            # the port name into the floating ip
            if not links_to and rel.is_derived_from(TOSCA_LINKS_TO):
                links_to = node
                network_resource = None
                for hot_resource in self.depends_on_nodes:
                    if links_to.name == hot_resource.name:
                        network_resource = hot_resource
                        self.depends_on.remove(hot_resource)
                        break

                floating_ip_props['port_id'] = \
                    '{ get_resource: %s }' % (links_to.name)

        self.properties = floating_ip_props
