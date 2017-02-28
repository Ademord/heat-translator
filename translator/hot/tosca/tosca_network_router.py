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

from toscaparser.common.exception import InvalidPropertyValueError
from translator.hot.syntax.hot_resource import HotResource

# Name used to dynamically load appropriate map class.
TARGET_CLASS_NAME = 'ToscaRouter'
TOSCA_LINKS_TO = 'tosca.relationships.network.LinksTo'

class ToscaRouter(HotResource):
    '''Translate TOSCA node type tosca.nodes.network.Network.'''

    toscatype = 'tosca.nodes.network.Router'
    ROUTER_INTERFACE_SUFFIX = '_interface'
    ROUTER_PROPS = []
    EXTERNAL_GATEWAY_INFO_PROPS = ['public_network']
    ROUTER_INTERFACE_PROPS = ['router_id', 'subnet_id']

    existing_resource_id = None

    def __init__(self, nodetemplate, csar_dir=None):
        super(ToscaRouter, self).__init__(nodetemplate,
                                           type='OS::Neutron::Router',
                                           csar_dir=csar_dir)
        pass

    def handle_properties(self):
        tosca_props = self.get_tosca_props()

        router_props = {}
        for key, value in tosca_props.items():
            if key in self.ROUTER_PROPS or key in self.EXTERNAL_GATEWAY_INFO_PROPS:
                if key in self.EXTERNAL_GATEWAY_INFO_PROPS:
                    if 'external_gateway_info' in router_props.keys():
                        router_props['external_gateway_info'].update({key: value})
                    else:
                        router_props['external_gateway_info'] = {key: value}
                    # self.existing_resource_id = value
                    break
        self.properties = router_props


    def handle_expansion(self):
        # If the network resource should not be output (they are hidden),
        # there is no need to generate subnet resource
        if self.hide_resource:
            return
        tosca_props = self.get_tosca_props()
        router_interface_props = {}
        # for key, value in tosca_props.items():
        #     if key in self.ROUTER_INTERFACE_PROPS:
        #         if key == 'private_subnet':
        router_interface_props['router'] = '{ get_resource: %s }' % (self.name)

        links_to = None
        for rel, node in self.nodetemplate.relationships.items():
            # Check for LinksTo relantions. If found add a subnet property with 
            # the network name into the router interface
            if not links_to and rel.is_derived_from(TOSCA_LINKS_TO):
                links_to = node
                network_resource = None
                for hot_resource in self.depends_on_nodes:
                    if links_to.name == hot_resource.name:
                        network_resource = hot_resource
                        self.depends_on.remove(hot_resource)
                        break

                if network_resource.existing_resource_id:
                    router_interface_props['subnet'] = \
                        str(network_resource.existing_resource_id)
                else:
                    router_interface_props['subnet'] = \
                        '{ get_resource: %s }' % (links_to.name + '_subnet')

        router_interface_resource_name = self.name + self.ROUTER_INTERFACE_SUFFIX

        hot_resources = [HotResource(self.nodetemplate,
                                     type='OS::Neutron::RouterInterface',
                                     name=router_interface_resource_name,
                                     properties=router_interface_props)]
        return hot_resources
