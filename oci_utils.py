import oci
from typing import Dict, List, Optional, Tuple
import os

class OCIManager:
    def __init__(self, config_file: str = "~/.oci/config", profile: str = "DEFAULT"):
        self.config = oci.config.from_file(os.path.expanduser(config_file), profile)
        self.identity = oci.identity.IdentityClient(self.config)
        self.network = oci.core.VirtualNetworkClient(self.config)
        self.compute = oci.core.ComputeClient(self.config)
        
        # Get tenancy OCID
        self.tenancy_id = self.config["tenancy"]
    
    def list_compartments(self) -> List[Dict]:
        """List all compartments in the tenancy."""
        compartments = self.identity.list_compartments(
            self.tenancy_id,
            compartment_id_in_subtree=True,
            lifecycle_state="ACTIVE"
        ).data
        return [{"id": comp.id, "name": comp.name} for comp in compartments]
    
    def list_vcns(self, compartment_id: str) -> List[Dict]:
        """List VCNs in a compartment."""
        vcns = self.network.list_vcns(compartment_id).data
        return [{"id": vcn.id, "name": vcn.display_name, "cidr": vcn.cidr_block} for vcn in vcns]
    
    def list_subnets(self, compartment_id: str, vcn_id: str) -> List[Dict]:
        """List subnets in a VCN."""
        subnets = self.network.list_subnets(
            compartment_id=compartment_id,
            vcn_id=vcn_id
        ).data
        return [{"id": subnet.id, "name": subnet.display_name, "cidr": subnet.cidr_block} for subnet in subnets]
    
    def list_security_lists(self, compartment_id: str, vcn_id: str) -> List[Dict]:
        """List security lists in a VCN."""
        security_lists = self.network.list_security_lists(
            compartment_id=compartment_id,
            vcn_id=vcn_id
        ).data
        return [{"id": sl.id, "name": sl.display_name} for sl in security_lists]
    
    def get_security_list(self, security_list_id: str) -> Dict:
        """Get security list details."""
        sl = self.network.get_security_list(security_list_id).data
        return {
            "id": sl.id,
            "name": sl.display_name,
            "egress_rules": sl.egress_security_rules,
            "ingress_rules": sl.ingress_security_rules
        }
    
    def update_security_list_rules(self, security_list_id: str, egress_rules: List[Dict], ingress_rules: List[Dict]) -> None:
        """Update security list rules."""
        sl = self.network.get_security_list(security_list_id).data
        details = oci.core.models.UpdateSecurityListDetails(
            egress_security_rules=egress_rules,
            ingress_security_rules=ingress_rules
        )
        self.network.update_security_list(security_list_id, details)
    
    def create_vcn(self, compartment_id: str, display_name: str, cidr_block: str, 
                  dns_label: Optional[str] = None, is_ipv6_enabled: bool = False) -> Dict:
        """Create a new VCN with additional options."""
        details = oci.core.models.CreateVcnDetails(
            compartment_id=compartment_id,
            display_name=display_name,
            cidr_block=cidr_block,
            dns_label=dns_label,
            is_ipv6_enabled=is_ipv6_enabled
        )
        vcn = self.network.create_vcn(details).data
        return {"id": vcn.id, "name": vcn.display_name}
    
    def create_subnet(self, compartment_id: str, vcn_id: str, display_name: str, 
                     cidr_block: str, subnet_type: str = "PUBLIC",
                     dns_label: Optional[str] = None,
                     availability_domain: Optional[str] = None) -> Dict:
        """Create a new subnet with additional options."""
        details = oci.core.models.CreateSubnetDetails(
            compartment_id=compartment_id,
            vcn_id=vcn_id,
            display_name=display_name,
            cidr_block=cidr_block,
            dns_label=dns_label,
            prohibit_public_ip_on_vnic=(subnet_type == "PRIVATE"),
            availability_domain=availability_domain
        )
        subnet = self.network.create_subnet(details).data
        return {"id": subnet.id, "name": subnet.display_name}
    
    def create_internet_gateway(self, compartment_id: str, vcn_id: str, 
                              display_name: str, is_enabled: bool = True) -> Dict:
        """Create a new internet gateway."""
        details = oci.core.models.CreateInternetGatewayDetails(
            compartment_id=compartment_id,
            vcn_id=vcn_id,
            display_name=display_name,
            is_enabled=is_enabled
        )
        gateway = self.network.create_internet_gateway(details).data
        return {"id": gateway.id, "name": gateway.display_name}

    def create_route_table(self, compartment_id: str, vcn_id: str, 
                          display_name: str, route_rules: List[Dict]) -> Dict:
        """Create a new route table."""
        route_rules_objects = []
        for rule in route_rules:
            route_rules_objects.append(
                oci.core.models.RouteRule(
                    network_entity_id=rule["network_entity_id"],
                    destination=rule["destination"],
                    destination_type=rule.get("destination_type", "CIDR_BLOCK")
                )
            )

        details = oci.core.models.CreateRouteTableDetails(
            compartment_id=compartment_id,
            vcn_id=vcn_id,
            display_name=display_name,
            route_rules=route_rules_objects
        )
        route_table = self.network.create_route_table(details).data
        return {"id": route_table.id, "name": route_table.display_name}

    def create_security_list(self, compartment_id: str, vcn_id: str, 
                           display_name: str, ingress_rules: List[Dict], 
                           egress_rules: List[Dict]) -> Dict:
        """Create a new security list."""
        details = oci.core.models.CreateSecurityListDetails(
            compartment_id=compartment_id,
            vcn_id=vcn_id,
            display_name=display_name,
            ingress_security_rules=ingress_rules,
            egress_security_rules=egress_rules
        )
        security_list = self.network.create_security_list(details).data
        return {"id": security_list.id, "name": security_list.display_name}

    def list_availability_domains(self, compartment_id: str) -> List[Dict]:
        """List availability domains in a compartment."""
        ads = self.identity.list_availability_domains(compartment_id).data
        return [{"name": ad.name} for ad in ads]

    def list_internet_gateways(self, compartment_id: str, vcn_id: str) -> List[Dict]:
        """List internet gateways in a VCN."""
        gateways = self.network.list_internet_gateways(
            compartment_id=compartment_id,
            vcn_id=vcn_id
        ).data
        return [{"id": gw.id, "name": gw.display_name, "enabled": gw.is_enabled} for gw in gateways]

    def list_route_tables(self, compartment_id: str, vcn_id: str) -> List[Dict]:
        """List route tables in a VCN."""
        route_tables = self.network.list_route_tables(
            compartment_id=compartment_id,
            vcn_id=vcn_id
        ).data
        return [{"id": rt.id, "name": rt.display_name, "rules": rt.route_rules} for rt in route_tables]
    
    def list_images(self, compartment_id: str) -> List[Dict]:
        """List compute images."""
        images = self.compute.list_images(
            compartment_id,
            operating_system="Oracle Linux"
        ).data
        return [{"id": img.id, "name": img.display_name} for img in images]
    
    def list_shapes(self, compartment_id: str) -> List[Dict]:
        """List available compute shapes."""
        shapes = self.compute.list_shapes(compartment_id).data
        return [{"name": shape.shape, "ocpus": shape.ocpus, "memory_in_gbs": shape.memory_in_gbs} 
                for shape in shapes]
    
    def launch_instance(
        self,
        compartment_id: str,
        display_name: str,
        image_id: str,
        shape: str,
        subnet_id: str,
        ssh_public_key: str,
        boot_volume_size_in_gbs: Optional[int] = None,
        shape_config: Optional[Dict] = None
    ) -> Dict:
        """Launch a compute instance."""
        instance_details = oci.core.models.LaunchInstanceDetails(
            compartment_id=compartment_id,
            display_name=display_name,
            image_id=image_id,
            shape=shape,
            subnet_id=subnet_id,
            metadata={
                "ssh_authorized_keys": ssh_public_key
            }
        )

        # Add shape config for Flex shapes
        if shape_config and ".Flex" in shape:
            instance_details.shape_config = oci.core.models.LaunchInstanceShapeConfigDetails(
                ocpus=shape_config["ocpus"],
                memory_in_gbs=shape_config["memory_in_gbs"]
            )

        if boot_volume_size_in_gbs:
            instance_details.source_details = oci.core.models.InstanceSourceViaImageDetails(
                boot_volume_size_in_gbs=boot_volume_size_in_gbs,
                image_id=image_id
            )
            
        instance = self.compute.launch_instance(instance_details).data
        return {"id": instance.id, "name": instance.display_name}
    
    def list_instances(self, compartment_id: str) -> List[Dict]:
        """List compute instances."""
        instances = self.compute.list_instances(compartment_id).data
        result = []
        for instance in instances:
            vnic_attachments = self.compute.list_vnic_attachments(
                compartment_id,
                instance_id=instance.id
            ).data
            
            private_ip = None
            public_ip = None
            if vnic_attachments:
                vnic = self.network.get_vnic(vnic_attachments[0].vnic_id).data
                private_ip = vnic.private_ip
                public_ip = vnic.public_ip
                
            result.append({
                "id": instance.id,
                "name": instance.display_name,
                "state": instance.lifecycle_state,
                "private_ip": private_ip,
                "public_ip": public_ip,
                "shape": instance.shape
            })
        return result
    
    def start_instance(self, instance_id: str) -> None:
        """Start a stopped compute instance."""
        self.compute.instance_action(instance_id, "START")
    
    def stop_instance(self, instance_id: str) -> None:
        """Stop a running compute instance."""
        self.compute.instance_action(instance_id, "STOP")
    
    def terminate_instance(self, instance_id: str, preserve_boot_volume: bool = False) -> None:
        """Terminate a compute instance."""
        self.compute.terminate_instance(
            instance_id,
            preserve_boot_volume=preserve_boot_volume
        )

    def list_nat_gateways(self, compartment_id: str, vcn_id: str) -> List[Dict]:
        """List NAT gateways in a VCN."""
        gateways = self.network.list_nat_gateways(
            compartment_id=compartment_id,
            vcn_id=vcn_id
        ).data
        return [{"id": gw.id, "name": gw.display_name, "enabled": gw.block_traffic} for gw in gateways]

    def list_service_gateways(self, compartment_id: str, vcn_id: str) -> List[Dict]:
        """List service gateways in a VCN."""
        gateways = self.network.list_service_gateways(
            compartment_id=compartment_id,
            vcn_id=vcn_id
        ).data
        return [{"id": gw.id, "name": gw.display_name, "services": [svc.service_name for svc in gw.services]} for gw in gateways]

    def create_nat_gateway(self, compartment_id: str, vcn_id: str, 
                          display_name: str, block_traffic: bool = False) -> Dict:
        """Create a new NAT gateway."""
        details = oci.core.models.CreateNatGatewayDetails(
            compartment_id=compartment_id,
            vcn_id=vcn_id,
            display_name=display_name,
            block_traffic=block_traffic
        )
        gateway = self.network.create_nat_gateway(details).data
        return {"id": gateway.id, "name": gateway.display_name}

    def create_service_gateway(self, compartment_id: str, vcn_id: str, 
                             display_name: str, services: List[str]) -> Dict:
        """Create a new service gateway."""
        # Get available services
        services_list = self.network.list_services(compartment_id).data
        service_details = []
        for service_name in services:
            service = next((svc for svc in services_list if svc.service_name == service_name), None)
            if service:
                service_details.append(oci.core.models.ServiceIdRequestDetails(service_id=service.id))

        details = oci.core.models.CreateServiceGatewayDetails(
            compartment_id=compartment_id,
            vcn_id=vcn_id,
            display_name=display_name,
            services=service_details
        )
        gateway = self.network.create_service_gateway(details).data
        return {"id": gateway.id, "name": gateway.display_name}

    def list_available_services(self, compartment_id: str) -> List[Dict]:
        """List available services for service gateway."""
        services = self.network.list_services().data
        return [{"id": svc.id, "name": svc.service_name if hasattr(svc, 'service_name') else svc.name} for svc in services]

    def delete_vcn(self, vcn_id: str) -> None:
        """Delete a VCN."""
        self.network.delete_vcn(vcn_id) 