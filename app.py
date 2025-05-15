import streamlit as st
import ipaddress
from oci_utils import OCIManager
import json

# Initialize session state
if 'oci' not in st.session_state:
    st.session_state.oci = OCIManager()

def validate_cidr(cidr: str) -> bool:
    """Validate CIDR block format."""
    try:
        ipaddress.ip_network(cidr)
        return True
    except ValueError:
        return False

def network_tab():
    st.header("Network Management")
    
    # Compartment selection
    compartments = st.session_state.oci.list_compartments()
    selected_compartment = st.selectbox(
        "Select Compartment",
        options=[comp["name"] for comp in compartments],
        key="network_compartment"
    )
    compartment_id = next(comp["id"] for comp in compartments if comp["name"] == selected_compartment)
    
    # Create tabs for different network components
    vcn_tab, subnet_tab, gateway_tab, route_tab, security_tab = st.tabs([
        "VCN", "Subnet", "Gateway", "Route Table", "Security List"
    ])
    
    # VCN Tab
    with vcn_tab:
        st.subheader("Virtual Cloud Network (VCN)")
        
        # Initialize session states
        if 'show_vcn_dialog' not in st.session_state:
            st.session_state.show_vcn_dialog = False
        if 'selected_vcn' not in st.session_state:
            st.session_state.selected_vcn = None
        
        # Add New VCN button and Refresh button in the same row
        col1, col2 = st.columns([6, 1])
        with col1:
            if st.button("➕ Add New VCN", type="primary"):
                st.session_state.show_vcn_dialog = True
        with col2:
            if st.button("🔄 Refresh"):
                st.rerun()
        
        # VCN Creation Dialog - Moved here to appear right after the buttons
        if st.session_state.show_vcn_dialog:
            with st.form(key="create_vcn_form"):
                st.markdown("### Create New VCN")
                
                vcn_name = st.text_input("VCN Name")
                vcn_cidr = st.text_input("CIDR Block (e.g., 10.0.0.0/16)")
                vcn_dns_label = st.text_input("DNS Label (optional)")
                vcn_ipv6 = st.checkbox("Enable IPv6")
                
                col1, col2 = st.columns(2)
                submit = col1.form_submit_button("Create VCN", type="primary")
                cancel = col2.form_submit_button("Cancel")
                
                if submit:
                    if not vcn_name:
                        st.error("VCN name is required")
                    elif not validate_cidr(vcn_cidr):
                        st.error("Invalid CIDR block format")
                    else:
                        try:
                            result = st.session_state.oci.create_vcn(
                                compartment_id=compartment_id,
                                display_name=vcn_name,
                                cidr_block=vcn_cidr,
                                dns_label=vcn_dns_label if vcn_dns_label else None,
                                is_ipv6_enabled=vcn_ipv6
                            )
                            st.success(f"VCN {vcn_name} created successfully")
                            st.session_state.show_vcn_dialog = False
                            st.session_state.selected_vcn = result["id"]
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error creating VCN: {str(e)}")
                
                if cancel:
                    st.session_state.show_vcn_dialog = False
                    st.rerun()
        
        # Display VCNs in a table
        vcns = st.session_state.oci.list_vcns(compartment_id)
        if vcns:
            # Create the table header
            st.markdown("### Existing VCNs")
            cols = st.columns([3, 2, 2, 1, 1])
            headers = ["Name", "CIDR Block", "State", "Select", "Actions"]
            for col, header in zip(cols, headers):
                col.markdown(f"**{header}**")
            
            # Add a separator
            st.markdown("---")
            
            # Display each VCN in a row
            for vcn in vcns:
                cols = st.columns([3, 2, 2, 1, 1])
                cols[0].write(vcn["name"])
                cols[1].write(vcn["cidr"])
                cols[2].write("Active")  # You might want to get the actual state from the VCN object
                
                # Select button
                is_selected = st.session_state.selected_vcn == vcn["id"]
                if cols[3].button("✓" if is_selected else "Select", key=f"select_vcn_{vcn['id']}", 
                                type="primary" if is_selected else "secondary"):
                    st.session_state.selected_vcn = vcn["id"] if not is_selected else None
                    st.rerun()
                
                # Delete button with confirmation
                delete_key = f"delete_vcn_{vcn['id']}"
                confirm_key = f"confirm_delete_vcn_{vcn['id']}"
                
                if confirm_key not in st.session_state:
                    st.session_state[confirm_key] = False
                
                if not st.session_state[confirm_key]:
                    if cols[4].button("🗑️", key=delete_key):
                        st.session_state[confirm_key] = True
                else:
                    # Show confirmation buttons
                    confirm_cols = st.columns([1, 1])
                    if confirm_cols[0].button("✓", key=f"confirm_{delete_key}"):
                        try:
                            st.session_state.oci.delete_vcn(vcn['id'])
                            if st.session_state.selected_vcn == vcn['id']:
                                st.session_state.selected_vcn = None
                            st.success(f"VCN {vcn['name']} deleted successfully")
                            st.session_state[confirm_key] = False
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error deleting VCN: {str(e)}")
                            st.session_state[confirm_key] = False
                    if confirm_cols[1].button("✗", key=f"cancel_{delete_key}"):
                        st.session_state[confirm_key] = False
                        st.rerun()
                
                # Add a separator between VCNs
                st.markdown("---")
        else:
            st.info("No VCNs found in this compartment")
    
    # Get selected VCN ID if available
    vcn_id = st.session_state.selected_vcn if st.session_state.selected_vcn else None
    
    # Subnet Tab
    with subnet_tab:
        st.subheader("Subnet Management")
        
        # Initialize session state for subnet creation dialog if not exists
        if 'show_subnet_dialog' not in st.session_state:
            st.session_state.show_subnet_dialog = False
        
        # Add New Subnet button and Refresh button in the same row
        col1, col2 = st.columns([6, 1])
        with col1:
            if st.button("➕ Add New Subnet", type="primary"):
                if not vcn_id:
                    st.error("Please select a VCN first")
                else:
                    st.session_state.show_subnet_dialog = True
        with col2:
            if st.button("🔄 Refresh Subnets"):
                st.rerun()
        
        # Subnet Creation Dialog - Appears right after the buttons
        if st.session_state.show_subnet_dialog and vcn_id:
            with st.form(key="create_subnet_form"):
                st.markdown("### Create New Subnet")
                
                subnet_name = st.text_input("Subnet Name")
                subnet_cidr = st.text_input("CIDR Block")
                
                col1, col2 = st.columns(2)
                with col1:
                    subnet_type = st.selectbox(
                        "Subnet Type",
                        options=["PUBLIC", "PRIVATE"],
                        key="subnet_type"
                    )
                    
                with col2:
                    ads = st.session_state.oci.list_availability_domains(compartment_id)
                    selected_ad = st.selectbox(
                        "Availability Domain",
                        options=[ad["name"] for ad in ads],
                        key="subnet_ad"
                    ) if ads else None
                
                subnet_dns = st.text_input("DNS Label (optional)")
                
                col1, col2 = st.columns(2)
                submit = col1.form_submit_button("Create Subnet", type="primary")
                cancel = col2.form_submit_button("Cancel")
                
                if submit:
                    if not subnet_name:
                        st.error("Subnet name is required")
                    elif not validate_cidr(subnet_cidr):
                        st.error("Invalid CIDR block format")
                    else:
                        try:
                            st.session_state.oci.create_subnet(
                                compartment_id=compartment_id,
                                vcn_id=vcn_id,
                                display_name=subnet_name,
                                cidr_block=subnet_cidr,
                                subnet_type=subnet_type,
                                dns_label=subnet_dns if subnet_dns else None,
                                availability_domain=selected_ad
                            )
                            st.success(f"Subnet {subnet_name} created successfully")
                            st.session_state.show_subnet_dialog = False
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error creating subnet: {str(e)}")
                
                if cancel:
                    st.session_state.show_subnet_dialog = False
                    st.rerun()
        
        # Get all VCNs for reference
        vcns = st.session_state.oci.list_vcns(compartment_id)
        vcn_names = {vcn["id"]: vcn["name"] for vcn in vcns}
        
        # Display all subnets across all VCNs in a table
        all_subnets = []
        for vcn in vcns:
            subnets = st.session_state.oci.list_subnets(compartment_id, vcn["id"])
            for subnet in subnets:
                subnet["vcn_name"] = vcn["name"]
                all_subnets.append(subnet)
        
        if all_subnets:
            # Create the table header
            st.markdown("### Existing Subnets")
            cols = st.columns([3, 2, 2, 2, 2, 1])
            headers = ["Name", "CIDR Block", "VCN", "Type", "AD", "Actions"]
            for col, header in zip(cols, headers):
                col.markdown(f"**{header}**")
            
            # Add a separator
            st.markdown("---")
            
            # Display each subnet in a row
            for subnet in all_subnets:
                cols = st.columns([3, 2, 2, 2, 2, 1])
                cols[0].write(subnet["name"])
                cols[1].write(subnet["cidr"])
                cols[2].write(subnet["vcn_name"])
                
                # Determine if subnet is public or private based on prohibit_public_ip_on_vnic
                subnet_type = "PRIVATE" if getattr(subnet, "prohibit_public_ip_on_vnic", True) else "PUBLIC"
                cols[3].write(subnet_type)
                
                # Get availability domain
                ad = getattr(subnet, "availability_domain", "Regional")
                cols[4].write(ad.split("-")[-1] if ad != "Regional" else ad)
                
                # Delete button with confirmation
                delete_key = f"delete_subnet_{subnet['id']}"
                confirm_key = f"confirm_delete_subnet_{subnet['id']}"
                
                if confirm_key not in st.session_state:
                    st.session_state[confirm_key] = False
                
                if not st.session_state[confirm_key]:
                    if cols[5].button("🗑️", key=delete_key):
                        st.session_state[confirm_key] = True
                else:
                    # Show confirmation buttons
                    confirm_cols = st.columns([1, 1])
                    if confirm_cols[0].button("✓", key=f"confirm_{delete_key}"):
                        try:
                            st.session_state.oci.delete_subnet(subnet['id'])
                            st.success(f"Subnet {subnet['name']} deleted successfully")
                            st.session_state[confirm_key] = False
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error deleting subnet: {str(e)}")
                            st.session_state[confirm_key] = False
                    if confirm_cols[1].button("✗", key=f"cancel_{delete_key}"):
                        st.session_state[confirm_key] = False
                        st.rerun()
                
                # Add a separator between subnets
                st.markdown("---")
        else:
            st.info("No subnets found in this compartment")
    
    # Gateway Tab
    with gateway_tab:
        st.subheader("Gateway Management")
        
        if not vcn_id:
            st.warning("Please select a VCN first")
        else:
            # Create tabs for different gateway types
            igw_tab, nat_tab, sgw_tab = st.tabs([
                "Internet Gateways", "NAT Gateways", "Service Gateways"
            ])
            
            # Internet Gateway Management
            with igw_tab:
                st.subheader("Internet Gateways")
                
                # Initialize session states for IGW
                if 'show_igw_dialog' not in st.session_state:
                    st.session_state.show_igw_dialog = False
                if 'show_delete_igw_dialog' not in st.session_state:
                    st.session_state.show_delete_igw_dialog = False
                if 'gateway_to_delete' not in st.session_state:
                    st.session_state.gateway_to_delete = None
                
                # Add New IGW button and Refresh button in the same row
                col1, col2 = st.columns([6, 1])
                with col1:
                    if st.button("➕ Add New Internet Gateway", type="primary"):
                        st.session_state.show_igw_dialog = True
                with col2:
                    if st.button("🔄", key="refresh_igw"):
                        st.rerun()
                
                # IGW Creation Dialog
                if st.session_state.show_igw_dialog:
                    with st.form(key="create_igw_form"):
                        st.markdown("### Create New Internet Gateway")
                        igw_name = st.text_input("Gateway Name", key="igw_name")
                        igw_enabled = st.checkbox("Enable Gateway", value=True, key="igw_enabled")
                        
                        col1, col2 = st.columns(2)
                        submit = col1.form_submit_button("Create Gateway", type="primary")
                        cancel = col2.form_submit_button("Cancel")
                        
                        if submit:
                            if not igw_name:
                                st.error("Gateway name is required")
                            else:
                                try:
                                    st.session_state.oci.create_internet_gateway(
                                        compartment_id=compartment_id,
                                        vcn_id=vcn_id,
                                        display_name=igw_name,
                                        is_enabled=igw_enabled
                                    )
                                    st.success(f"Internet Gateway {igw_name} created successfully")
                                    st.session_state.show_igw_dialog = False
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error creating Internet Gateway: {str(e)}")
                        
                        if cancel:
                            st.session_state.show_igw_dialog = False
                            st.rerun()
                
                # List existing Internet Gateways in a table
                internet_gateways = st.session_state.oci.list_internet_gateways(compartment_id, vcn_id)
                if internet_gateways:
                    # Create the table header
                    st.markdown("### Existing Internet Gateways")
                    cols = st.columns([3, 2, 2, 1])
                    headers = ["Name", "State", "Status", "Actions"]
                    for col, header in zip(cols, headers):
                        col.markdown(f"**{header}**")
                    
                    # Add a separator
                    st.markdown("---")
                    
                    # Display each gateway in a row
                    for gw in internet_gateways:
                        cols = st.columns([3, 2, 2, 1])
                        cols[0].write(gw['name'])
                        # Use getattr to safely get the state
                        state = getattr(gw, 'state', 'Unknown')
                        cols[1].write(state)
                        cols[2].write("✅ Enabled" if gw['enabled'] else "❌ Disabled")
                        
                        # Delete button
                        if cols[3].button("🗑️", key=f"delete_igw_{gw['id']}"):
                            st.session_state.show_delete_igw_dialog = True
                            st.session_state.gateway_to_delete = gw
                            st.rerun()
                        
                        # Add a separator between gateways
                        st.markdown("---")
                    
                    # Delete confirmation dialog
                    if st.session_state.show_delete_igw_dialog and st.session_state.gateway_to_delete:
                        gw = st.session_state.gateway_to_delete
                        with st.form(key="delete_igw_dialog"):
                            st.warning(f"⚠️ Are you sure you want to delete Internet Gateway '{gw['name']}'?")
                            
                            col1, col2 = st.columns(2)
                            confirm = col1.form_submit_button("Confirm Delete", type="primary")
                            cancel = col2.form_submit_button("Cancel")
                            
                            if confirm:
                                try:
                                    st.session_state.oci.delete_internet_gateway(gw['id'])
                                    st.success(f"Internet Gateway {gw['name']} deleted successfully")
                                    st.session_state.show_delete_igw_dialog = False
                                    st.session_state.gateway_to_delete = None
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error deleting Internet Gateway: {str(e)}")
                            
                            elif cancel:
                                st.session_state.show_delete_igw_dialog = False
                                st.session_state.gateway_to_delete = None
                                st.rerun()
                else:
                    st.info("No Internet Gateways found")
            
            # NAT Gateway Management
            with nat_tab:
                st.subheader("NAT Gateways")
                
                # Initialize session states for NAT Gateway
                if 'show_nat_dialog' not in st.session_state:
                    st.session_state.show_nat_dialog = False
                if 'show_delete_nat_dialog' not in st.session_state:
                    st.session_state.show_delete_nat_dialog = False
                
                # Add New NAT Gateway button and Refresh button in the same row
                col1, col2 = st.columns([6, 1])
                with col1:
                    if st.button("➕ Add New NAT Gateway", type="primary"):
                        st.session_state.show_nat_dialog = True
                with col2:
                    if st.button("🔄", key="refresh_nat"):
                        st.rerun()
                
                # NAT Gateway Creation Dialog
                if st.session_state.show_nat_dialog:
                    with st.form(key="create_nat_form"):
                        st.markdown("### Create New NAT Gateway")
                        nat_name = st.text_input("Gateway Name", key="nat_name")
                        block_traffic = st.checkbox("Block Traffic", value=False, key="nat_block")
                        
                        col1, col2 = st.columns(2)
                        submit = col1.form_submit_button("Create Gateway", type="primary")
                        cancel = col2.form_submit_button("Cancel")
                        
                        if submit:
                            if not nat_name:
                                st.error("Gateway name is required")
                            else:
                                try:
                                    st.session_state.oci.create_nat_gateway(
                                        compartment_id=compartment_id,
                                        vcn_id=vcn_id,
                                        display_name=nat_name,
                                        block_traffic=block_traffic
                                    )
                                    st.success(f"NAT Gateway {nat_name} created successfully")
                                    st.session_state.show_nat_dialog = False
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error creating NAT Gateway: {str(e)}")
                        
                        if cancel:
                            st.session_state.show_nat_dialog = False
                            st.rerun()
                
                # List existing NAT Gateways in a table
                nat_gateways = st.session_state.oci.list_nat_gateways(compartment_id, vcn_id)
                if nat_gateways:
                    # Create the table header
                    st.markdown("### Existing NAT Gateways")
                    cols = st.columns([3, 2, 2, 1])
                    headers = ["Name", "State", "Status", "Actions"]
                    for col, header in zip(cols, headers):
                        col.markdown(f"**{header}**")
                    
                    # Add a separator
                    st.markdown("---")
                    
                    # Display each gateway in a row
                    for gw in nat_gateways:
                        cols = st.columns([3, 2, 2, 1])
                        cols[0].write(gw['name'])
                        # Use getattr to safely get the state
                        state = getattr(gw, 'state', 'Unknown')
                        cols[1].write(state)
                        cols[2].write("❌ Blocked" if getattr(gw, 'block_traffic', False) else "✅ Active")
                        
                        # Delete button
                        if cols[3].button("🗑️", key=f"delete_nat_{gw['id']}"):
                            st.session_state.show_delete_nat_dialog = True
                            st.session_state.gateway_to_delete = gw
                            st.rerun()
                        
                        # Add a separator between gateways
                        st.markdown("---")
                    
                    # Delete confirmation dialog
                    if st.session_state.show_delete_nat_dialog and st.session_state.gateway_to_delete:
                        gw = st.session_state.gateway_to_delete
                        with st.form(key="delete_nat_dialog"):
                            st.warning(f"⚠️ Are you sure you want to delete NAT Gateway '{gw['name']}'?")
                            
                            col1, col2 = st.columns(2)
                            confirm = col1.form_submit_button("Confirm Delete", type="primary")
                            cancel = col2.form_submit_button("Cancel")
                            
                            if confirm:
                                try:
                                    st.session_state.oci.delete_nat_gateway(gw['id'])
                                    st.success(f"NAT Gateway {gw['name']} deleted successfully")
                                    st.session_state.show_delete_nat_dialog = False
                                    st.session_state.gateway_to_delete = None
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error deleting NAT Gateway: {str(e)}")
                            
                            elif cancel:
                                st.session_state.show_delete_nat_dialog = False
                                st.session_state.gateway_to_delete = None
                                st.rerun()
                else:
                    st.info("No NAT Gateways found")
            
            # Service Gateway Management
            with sgw_tab:
                st.subheader("Service Gateways")
                
                # Initialize session states for Service Gateway
                if 'show_sgw_dialog' not in st.session_state:
                    st.session_state.show_sgw_dialog = False
                if 'show_delete_sgw_dialog' not in st.session_state:
                    st.session_state.show_delete_sgw_dialog = False
                
                # Add New Service Gateway button and Refresh button in the same row
                col1, col2 = st.columns([6, 1])
                with col1:
                    if st.button("➕ Add New Service Gateway", type="primary"):
                        st.session_state.show_sgw_dialog = True
                with col2:
                    if st.button("🔄", key="refresh_sgw"):
                        st.rerun()
                
                # Service Gateway Creation Dialog
                if st.session_state.show_sgw_dialog:
                    with st.form(key="create_sgw_form"):
                        st.markdown("### Create New Service Gateway")
                        sgw_name = st.text_input("Gateway Name", key="sgw_name")
                        
                        # Get available services
                        available_services = st.session_state.oci.list_available_services(compartment_id)
                        service_options = [svc["name"] for svc in available_services]
                        
                        # Add "All Services" option if it's available
                        all_services_option = next((svc["name"] for svc in available_services if "all" in svc["name"].lower()), None)
                        
                        selected_services = st.multiselect(
                            "Select Services",
                            options=service_options,
                            default=[all_services_option] if all_services_option else [],
                            help="Select the Oracle services to access through this gateway"
                        )
                        
                        col1, col2 = st.columns(2)
                        submit = col1.form_submit_button("Create Gateway", type="primary")
                        cancel = col2.form_submit_button("Cancel")
                        
                        if submit:
                            if not sgw_name:
                                st.error("Gateway name is required")
                            elif not selected_services:
                                st.error("Please select at least one service")
                            else:
                                try:
                                    st.session_state.oci.create_service_gateway(
                                        compartment_id=compartment_id,
                                        vcn_id=vcn_id,
                                        display_name=sgw_name,
                                        services=selected_services
                                    )
                                    st.success(f"Service Gateway {sgw_name} created successfully")
                                    st.session_state.show_sgw_dialog = False
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error creating Service Gateway: {str(e)}")
                        
                        if cancel:
                            st.session_state.show_sgw_dialog = False
                            st.rerun()
                
                # List existing Service Gateways in a table
                service_gateways = st.session_state.oci.list_service_gateways(compartment_id, vcn_id)
                if service_gateways:
                    # Create the table header
                    st.markdown("### Existing Service Gateways")
                    cols = st.columns([3, 2, 3, 1])
                    headers = ["Name", "State", "Services", "Actions"]
                    for col, header in zip(cols, headers):
                        col.markdown(f"**{header}**")
                    
                    # Add a separator
                    st.markdown("---")
                    
                    # Display each gateway in a row
                    for gw in service_gateways:
                        cols = st.columns([3, 2, 3, 1])
                        cols[0].write(gw['name'])
                        # Use getattr to safely get the state
                        state = getattr(gw, 'state', 'Unknown')
                        cols[1].write(state)
                        cols[2].write(", ".join(gw.get('services', [])))
                        
                        # Delete button
                        if cols[3].button("🗑️", key=f"delete_sgw_{gw['id']}"):
                            st.session_state.show_delete_sgw_dialog = True
                            st.session_state.gateway_to_delete = gw
                            st.rerun()
                        
                        # Add a separator between gateways
                        st.markdown("---")
                    
                    # Delete confirmation dialog
                    if st.session_state.show_delete_sgw_dialog and st.session_state.gateway_to_delete:
                        gw = st.session_state.gateway_to_delete
                        with st.form(key="delete_sgw_dialog"):
                            st.warning(f"⚠️ Are you sure you want to delete Service Gateway '{gw['name']}'?")
                            
                            col1, col2 = st.columns(2)
                            confirm = col1.form_submit_button("Confirm Delete", type="primary")
                            cancel = col2.form_submit_button("Cancel")
                            
                            if confirm:
                                try:
                                    st.session_state.oci.delete_service_gateway(gw['id'])
                                    st.success(f"Service Gateway {gw['name']} deleted successfully")
                                    st.session_state.show_delete_sgw_dialog = False
                                    st.session_state.gateway_to_delete = None
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error deleting Service Gateway: {str(e)}")
                            
                            elif cancel:
                                st.session_state.show_delete_sgw_dialog = False
                                st.session_state.gateway_to_delete = None
                                st.rerun()
                else:
                    st.info("No Service Gateways found")
    
    # Route Table Tab
    with route_tab:
        st.subheader("Route Table Management")
        
        if not vcn_id:
            st.warning("Please select a VCN first")
        else:
            # Initialize session states for Route Table
            if 'show_rt_dialog' not in st.session_state:
                st.session_state.show_rt_dialog = False
            if 'show_delete_rt_dialog' not in st.session_state:
                st.session_state.show_delete_rt_dialog = False
            if 'route_table_to_delete' not in st.session_state:
                st.session_state.route_table_to_delete = None
            
            # Add New Route Table button and Refresh button in the same row
            col1, col2 = st.columns([6, 1])
            with col1:
                if st.button("➕ Add New Route Table", type="primary"):
                    st.session_state.show_rt_dialog = True
            with col2:
                if st.button("🔄", key="refresh_rt"):
                    st.rerun()
            
            # Route Table Creation Dialog
            if st.session_state.show_rt_dialog:
                with st.form(key="create_rt_form"):
                    st.markdown("### Create New Route Table")
                    rt_name = st.text_input("Route Table Name", key="rt_name")
                    
                    # Get available target types
                    target_types = ["Internet Gateway", "NAT Gateway", "Service Gateway"]
                    selected_target_type = st.selectbox(
                        "Target Type",
                        options=target_types,
                        key="rt_target_type"
                    )
                    
                    # Show appropriate target selection based on type
                    target_id = None
                    if selected_target_type == "Internet Gateway":
                        internet_gateways = st.session_state.oci.list_internet_gateways(compartment_id, vcn_id)
                        if internet_gateways:
                            selected_igw = st.selectbox(
                                "Target Internet Gateway",
                                options=[gw["name"] for gw in internet_gateways],
                                key="rt_igw"
                            )
                            target_id = next(gw["id"] for gw in internet_gateways if gw["name"] == selected_igw)
                        else:
                            st.warning("No Internet Gateways available. Please create one first.")
                    
                    elif selected_target_type == "NAT Gateway":
                        nat_gateways = st.session_state.oci.list_nat_gateways(compartment_id, vcn_id)
                        if nat_gateways:
                            selected_nat = st.selectbox(
                                "Target NAT Gateway",
                                options=[gw["name"] for gw in nat_gateways],
                                key="rt_nat"
                            )
                            target_id = next(gw["id"] for gw in nat_gateways if gw["name"] == selected_nat)
                        else:
                            st.warning("No NAT Gateways available. Please create one first.")
                    
                    elif selected_target_type == "Service Gateway":
                        service_gateways = st.session_state.oci.list_service_gateways(compartment_id, vcn_id)
                        if service_gateways:
                            selected_sgw = st.selectbox(
                                "Target Service Gateway",
                                options=[gw["name"] for gw in service_gateways],
                                key="rt_sgw"
                            )
                            target_id = next(gw["id"] for gw in service_gateways if gw["name"] == selected_sgw)
                        else:
                            st.warning("No Service Gateways available. Please create one first.")
                    
                    # Destination CIDR
                    destination_cidr = st.text_input(
                        "Destination CIDR",
                        value="0.0.0.0/0",
                        help="CIDR block for the route rule (e.g., 0.0.0.0/0 for all traffic)",
                        key="rt_destination"
                    )
                    
                    col1, col2 = st.columns(2)
                    submit = col1.form_submit_button("Create Route Table", type="primary")
                    cancel = col2.form_submit_button("Cancel")
                    
                    if submit:
                        if not rt_name:
                            st.error("Route Table name is required")
                        elif not target_id:
                            st.error("Please select a valid target gateway")
                        elif not validate_cidr(destination_cidr):
                            st.error("Invalid CIDR block format")
                        else:
                            try:
                                route_rules = [{
                                    "network_entity_id": target_id,
                                    "destination": destination_cidr,
                                    "destination_type": "CIDR_BLOCK"
                                }]
                                
                                st.session_state.oci.create_route_table(
                                    compartment_id=compartment_id,
                                    vcn_id=vcn_id,
                                    display_name=rt_name,
                                    route_rules=route_rules
                                )
                                st.success(f"Route Table {rt_name} created successfully")
                                st.session_state.show_rt_dialog = False
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error creating Route Table: {str(e)}")
                    
                    if cancel:
                        st.session_state.show_rt_dialog = False
                        st.rerun()
            
            # List existing Route Tables in a table
            route_tables = st.session_state.oci.list_route_tables(compartment_id, vcn_id)
            if route_tables:
                # Create the table header
                st.markdown("### Existing Route Tables")
                cols = st.columns([3, 4, 1])
                headers = ["Name", "Rules", "Actions"]
                for col, header in zip(cols, headers):
                    col.markdown(f"**{header}**")
                
                # Add a separator
                st.markdown("---")
                
                # Display each route table in a row
                for rt in route_tables:
                    cols = st.columns([3, 4, 1])
                    cols[0].write(rt["name"])
                    
                    # Format rules for display
                    rules_text = ""
                    for rule in rt.get("rules", []):
                        destination = getattr(rule, "destination", "N/A")
                        target_id = getattr(rule, "network_entity_id", None)
                        target_name = "Unknown Target"
                        
                        # Try to determine the target name based on the entity ID
                        if target_id:
                            # Check Internet Gateways
                            internet_gateways = st.session_state.oci.list_internet_gateways(compartment_id, vcn_id)
                            target = next((gw for gw in internet_gateways if gw["id"] == target_id), None)
                            if target:
                                target_name = f"Internet Gateway: {target['name']}"
                            else:
                                # Check NAT Gateways
                                nat_gateways = st.session_state.oci.list_nat_gateways(compartment_id, vcn_id)
                                target = next((gw for gw in nat_gateways if gw["id"] == target_id), None)
                                if target:
                                    target_name = f"NAT Gateway: {target['name']}"
                                else:
                                    # Check Service Gateways
                                    service_gateways = st.session_state.oci.list_service_gateways(compartment_id, vcn_id)
                                    target = next((gw for gw in service_gateways if gw["id"] == target_id), None)
                                    if target:
                                        target_name = f"Service Gateway: {target['name']}"
                        
                        rules_text += f"• {destination} → {target_name}\n"
                    
                    cols[1].text(rules_text if rules_text else "No rules defined")
                    
                    # Delete button
                    if cols[2].button("🗑️", key=f"delete_rt_{rt['id']}"):
                        st.session_state.show_delete_rt_dialog = True
                        st.session_state.route_table_to_delete = rt
                        st.rerun()
                    
                    # Add a separator between route tables
                    st.markdown("---")
                
                # Delete confirmation dialog
                if st.session_state.show_delete_rt_dialog and st.session_state.route_table_to_delete:
                    rt = st.session_state.route_table_to_delete
                    with st.form(key="delete_rt_dialog"):
                        st.warning(f"⚠️ Are you sure you want to delete Route Table '{rt['name']}'?")
                        
                        col1, col2 = st.columns(2)
                        confirm = col1.form_submit_button("Confirm Delete", type="primary")
                        cancel = col2.form_submit_button("Cancel")
                        
                        if confirm:
                            try:
                                st.session_state.oci.delete_route_table(rt['id'])
                                st.success(f"Route Table {rt['name']} deleted successfully")
                                st.session_state.show_delete_rt_dialog = False
                                st.session_state.route_table_to_delete = None
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error deleting Route Table: {str(e)}")
                        
                        elif cancel:
                            st.session_state.show_delete_rt_dialog = False
                            st.session_state.route_table_to_delete = None
                            st.rerun()
            else:
                st.info("No Route Tables found")
    
    # Security List Tab
    with security_tab:
        st.subheader("Security List Management")
        
        if not vcn_id:
            st.warning("Please select a VCN first")
        else:
            # Initialize session states for Security List
            if 'show_sl_dialog' not in st.session_state:
                st.session_state.show_sl_dialog = False
            if 'show_delete_sl_dialog' not in st.session_state:
                st.session_state.show_delete_sl_dialog = False
            if 'security_list_to_delete' not in st.session_state:
                st.session_state.security_list_to_delete = None
            if 'show_rule_dialog' not in st.session_state:
                st.session_state.show_rule_dialog = False
            if 'selected_security_list' not in st.session_state:
                st.session_state.selected_security_list = None
            
            # Add New Security List button and Refresh button in the same row
            col1, col2 = st.columns([6, 1])
            with col1:
                if st.button("➕ Add New Security List", type="primary"):
                    st.session_state.show_sl_dialog = True
            with col2:
                if st.button("🔄", key="refresh_sl"):
                    st.rerun()
            
            # Security List Creation Dialog
            if st.session_state.show_sl_dialog:
                with st.form(key="create_sl_form"):
                    st.markdown("### Create New Security List")
                    sl_name = st.text_input("Security List Name", key="sl_name")
                    
                    # Rule Type Selection
                    rule_type = st.selectbox(
                        "Rule Type",
                        options=["Ingress", "Egress"],
                        key="initial_rule_type"
                    )
                    
                    # Common rule configuration
                    protocol = st.selectbox(
                        "Protocol",
                        options=["all", "tcp", "udp", "icmp"],
                        key="initial_protocol"
                    )
                    
                    # Source/Destination based on rule type
                    if rule_type == "Ingress":
                        cidr = st.text_input(
                            "Source CIDR",
                            value="0.0.0.0/0",
                            help="CIDR block for the source (e.g., 0.0.0.0/0 for all traffic)",
                            key="initial_source_cidr"
                        )
                    else:  # Egress
                        cidr = st.text_input(
                            "Destination CIDR",
                            value="0.0.0.0/0",
                            help="CIDR block for the destination (e.g., 0.0.0.0/0 for all traffic)",
                            key="initial_dest_cidr"
                        )
                    
                    # Port configuration for TCP/UDP
                    if protocol in ["tcp", "udp"]:
                        st.markdown("#### Port Configuration")
                        col1, col2 = st.columns(2)
                        with col1:
                            port_min = st.number_input(
                                "Min Port",
                                min_value=1,
                                max_value=65535,
                                value=80,
                                help="Minimum port number (1-65535)",
                                key="initial_port_min"
                            )
                        with col2:
                            port_max = st.number_input(
                                "Max Port",
                                min_value=1,
                                max_value=65535,
                                value=80,
                                help="Maximum port number (1-65535)",
                                key="initial_port_max"
                            )
                    
                    # Stateless option
                    is_stateless = st.checkbox(
                        "Stateless",
                        value=False,
                        help="If checked, return traffic is not automatically allowed",
                        key="initial_stateless"
                    )
                    
                    col1, col2 = st.columns(2)
                    submit = col1.form_submit_button("Create Security List", type="primary")
                    cancel = col2.form_submit_button("Cancel")
                    
                    if submit:
                        if not sl_name:
                            st.error("Security List name is required")
                        elif not validate_cidr(cidr):
                            st.error("Invalid CIDR block format")
                        else:
                            try:
                                # Prepare the initial rule
                                rule = {
                                    "protocol": protocol,
                                    "is_stateless": is_stateless
                                }
                                
                                # Add source/destination based on rule type
                                if rule_type == "Ingress":
                                    rule["source"] = cidr
                                else:
                                    rule["destination"] = cidr
                                
                                # Add port configuration for TCP/UDP
                                if protocol in ["tcp", "udp"]:
                                    port_options = {
                                        "destination_port_range": {
                                            "min": port_min,
                                            "max": port_max
                                        }
                                    }
                                    if protocol == "tcp":
                                        rule["tcp_options"] = port_options
                                    else:
                                        rule["udp_options"] = port_options
                                
                                # Create security list with initial rule
                                ingress_rules = [rule] if rule_type == "Ingress" else []
                                egress_rules = [rule] if rule_type == "Egress" else []
                                
                                st.session_state.oci.create_security_list(
                                    compartment_id=compartment_id,
                                    vcn_id=vcn_id,
                                    display_name=sl_name,
                                    ingress_rules=ingress_rules,
                                    egress_rules=egress_rules
                                )
                                st.success(f"Security List {sl_name} created successfully with initial {rule_type.lower()} rule")
                                st.session_state.show_sl_dialog = False
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error creating Security List: {str(e)}")
                    
                    if cancel:
                        st.session_state.show_sl_dialog = False
                        st.rerun()
            
            # List existing Security Lists in a table
            security_lists = st.session_state.oci.list_security_lists(compartment_id, vcn_id)
            if security_lists:
                # Create the table header
                st.markdown("### Existing Security Lists")
                cols = st.columns([3, 2, 2, 2])
                headers = ["Name", "Ingress Rules", "Egress Rules", "Actions"]
                for col, header in zip(cols, headers):
                    col.markdown(f"**{header}**")
                
                # Add a separator
                st.markdown("---")
                
                # Display each security list in a row
                for sl in security_lists:
                    cols = st.columns([3, 2, 2, 2])
                    cols[0].write(sl["name"])
                    
                    # Count rules
                    ingress_count = len(sl.get("ingress_rules", []))
                    egress_count = len(sl.get("egress_rules", []))
                    
                    cols[1].write(f"{ingress_count} rules")
                    cols[2].write(f"{egress_count} rules")
                    
                    # Action buttons
                    action_col = cols[3].columns(2)
                    # Edit button
                    if action_col[0].button("✏️", key=f"edit_sl_{sl['id']}"):
                        st.session_state.selected_security_list = sl
                        st.session_state.show_rule_dialog = True
                        st.rerun()
                    
                    # Delete button
                    if action_col[1].button("🗑️", key=f"delete_sl_{sl['id']}"):
                        st.session_state.show_delete_sl_dialog = True
                        st.session_state.security_list_to_delete = sl
                        st.rerun()
                    
                    # Add a separator between security lists
                    st.markdown("---")
                
                # Rule Management Dialog
                if st.session_state.show_rule_dialog and st.session_state.selected_security_list:
                    sl = st.session_state.selected_security_list
                    st.markdown(f"### Manage Rules for {sl['name']}")
                    
                    # Create tabs for ingress and egress rules
                    rule_tabs = st.tabs(["Ingress Rules", "Egress Rules"])
                    
                    # Ingress Rules Tab
                    with rule_tabs[0]:
                        st.markdown("### Ingress Rules")
                        
                        # Add new ingress rule
                        with st.expander("Add New Ingress Rule", expanded=False):
                            with st.form("add_ingress_rule"):
                                source = st.text_input("Source CIDR", value="0.0.0.0/0")
                                protocol = st.selectbox(
                                    "Protocol",
                                    options=["all", "tcp", "udp", "icmp"]
                                )
                                
                                # Show port options for TCP/UDP
                                port_min = None
                                port_max = None
                                if protocol in ["tcp", "udp"]:
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        port_min = st.number_input("Min Port", min_value=1, max_value=65535, value=80)
                                    with col2:
                                        port_max = st.number_input("Max Port", min_value=1, max_value=65535, value=80)
                                
                                is_stateless = st.checkbox("Stateless", value=False)
                                
                                if st.form_submit_button("Add Rule"):
                                    new_rule = {
                                        "source": source,
                                        "protocol": protocol,
                                        "is_stateless": is_stateless
                                    }
                                    
                                    if protocol in ["tcp", "udp"]:
                                        port_options = {
                                            "destination_port_range": {
                                                "min": port_min,
                                                "max": port_max
                                            }
                                        }
                                        if protocol == "tcp":
                                            new_rule["tcp_options"] = port_options
                                        else:
                                            new_rule["udp_options"] = port_options
                                    
                                    try:
                                        current_rules = sl.get("ingress_rules", []).copy()
                                        current_rules.append(new_rule)
                                        st.session_state.oci.update_security_list_rules(
                                            sl['id'],
                                            sl.get("egress_rules", []),
                                            current_rules
                                        )
                                        st.success("Rule added successfully")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error adding rule: {str(e)}")
                        
                        # List existing ingress rules
                        for idx, rule in enumerate(sl.get("ingress_rules", [])):
                            with st.container():
                                cols = st.columns([3, 2, 2, 1])
                                cols[0].write(f"From: {rule.get('source', 'Any')}")
                                cols[1].write(f"Protocol: {rule.get('protocol', 'All')}")
                                
                                # Format port range
                                port_range = "Any"
                                if "tcp_options" in rule and rule["tcp_options"].get("destination_port_range"):
                                    port_range = f"TCP {rule['tcp_options']['destination_port_range']['min']}-{rule['tcp_options']['destination_port_range']['max']}"
                                elif "udp_options" in rule and rule["udp_options"].get("destination_port_range"):
                                    port_range = f"UDP {rule['udp_options']['destination_port_range']['min']}-{rule['udp_options']['destination_port_range']['max']}"
                                cols[2].write(port_range)
                                
                                if cols[3].button("🗑️", key=f"del_ingress_{idx}"):
                                    try:
                                        current_rules = sl.get("ingress_rules", []).copy()
                                        current_rules.pop(idx)
                                        st.session_state.oci.update_security_list_rules(
                                            sl['id'],
                                            sl.get("egress_rules", []),
                                            current_rules
                                        )
                                        st.success("Rule deleted successfully")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error deleting rule: {str(e)}")
                    
                    # Egress Rules Tab
                    with rule_tabs[1]:
                        st.markdown("### Egress Rules")
                        
                        # Add new egress rule
                        with st.expander("Add New Egress Rule", expanded=False):
                            with st.form("add_egress_rule"):
                                destination = st.text_input("Destination CIDR", value="0.0.0.0/0")
                                protocol = st.selectbox(
                                    "Protocol",
                                    options=["all", "tcp", "udp", "icmp"],
                                    key="egress_protocol"
                                )
                                
                                # Show port options for TCP/UDP
                                port_min = None
                                port_max = None
                                if protocol in ["tcp", "udp"]:
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        port_min = st.number_input("Min Port", min_value=1, max_value=65535, value=80, key="egress_port_min")
                                    with col2:
                                        port_max = st.number_input("Max Port", min_value=1, max_value=65535, value=80, key="egress_port_max")
                                
                                is_stateless = st.checkbox("Stateless", value=False, key="egress_stateless")
                                
                                if st.form_submit_button("Add Rule"):
                                    new_rule = {
                                        "destination": destination,
                                        "protocol": protocol,
                                        "is_stateless": is_stateless
                                    }
                                    
                                    if protocol in ["tcp", "udp"]:
                                        port_options = {
                                            "destination_port_range": {
                                                "min": port_min,
                                                "max": port_max
                                            }
                                        }
                                        if protocol == "tcp":
                                            new_rule["tcp_options"] = port_options
                                        else:
                                            new_rule["udp_options"] = port_options
                                    
                                    try:
                                        current_rules = sl.get("egress_rules", []).copy()
                                        current_rules.append(new_rule)
                                        st.session_state.oci.update_security_list_rules(
                                            sl['id'],
                                            current_rules,
                                            sl.get("ingress_rules", [])
                                        )
                                        st.success("Rule added successfully")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error adding rule: {str(e)}")
                        
                        # List existing egress rules
                        for idx, rule in enumerate(sl.get("egress_rules", [])):
                            with st.container():
                                cols = st.columns([3, 2, 2, 1])
                                cols[0].write(f"To: {rule.get('destination', 'Any')}")
                                cols[1].write(f"Protocol: {rule.get('protocol', 'All')}")
                                
                                # Format port range
                                port_range = "Any"
                                if "tcp_options" in rule and rule["tcp_options"].get("destination_port_range"):
                                    port_range = f"TCP {rule['tcp_options']['destination_port_range']['min']}-{rule['tcp_options']['destination_port_range']['max']}"
                                elif "udp_options" in rule and rule["udp_options"].get("destination_port_range"):
                                    port_range = f"UDP {rule['udp_options']['destination_port_range']['min']}-{rule['udp_options']['destination_port_range']['max']}"
                                cols[2].write(port_range)
                                
                                if cols[3].button("🗑️", key=f"del_egress_{idx}"):
                                    try:
                                        current_rules = sl.get("egress_rules", []).copy()
                                        current_rules.pop(idx)
                                        st.session_state.oci.update_security_list_rules(
                                            sl['id'],
                                            current_rules,
                                            sl.get("ingress_rules", [])
                                        )
                                        st.success("Rule deleted successfully")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error deleting rule: {str(e)}")
                    
                    if st.button("Done"):
                        st.session_state.show_rule_dialog = False
                        st.session_state.selected_security_list = None
                        st.rerun()
                
                # Delete confirmation dialog
                if st.session_state.show_delete_sl_dialog and st.session_state.security_list_to_delete:
                    sl = st.session_state.security_list_to_delete
                    with st.form(key="delete_sl_dialog"):
                        st.warning(f"⚠️ Are you sure you want to delete Security List '{sl['name']}'?")
                        
                        col1, col2 = st.columns(2)
                        confirm = col1.form_submit_button("Confirm Delete", type="primary")
                        cancel = col2.form_submit_button("Cancel")
                        
                        if confirm:
                            try:
                                st.session_state.oci.delete_security_list(sl['id'])
                                st.success(f"Security List {sl['name']} deleted successfully")
                                st.session_state.show_delete_sl_dialog = False
                                st.session_state.security_list_to_delete = None
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error deleting Security List: {str(e)}")
                        
                        elif cancel:
                            st.session_state.show_delete_sl_dialog = False
                            st.session_state.security_list_to_delete = None
                            st.rerun()
            else:
                st.info("No Security Lists found")

def compute_launch_tab():
    st.header("Launch Compute Instance")
    
    # Basic Instance Configuration
    st.subheader("Basic Configuration")
    
    # Compartment selection
    compartments = st.session_state.oci.list_compartments()
    selected_compartment = st.selectbox(
        "Select Compartment",
        options=[comp["name"] for comp in compartments],
        key="compute_compartment"
    )
    compartment_id = next(comp["id"] for comp in compartments if comp["name"] == selected_compartment)
    
    # Instance Name
    instance_name = st.text_input("Instance Name", help="Enter a name for your compute instance")
    
    # Image selection
    st.subheader("Image Selection")
    images = st.session_state.oci.list_images(compartment_id)
    selected_image = st.selectbox(
        "Select Image",
        options=[img["name"] for img in images],
        key="compute_image",
        help="Select the operating system image for your instance"
    )
    image_id = next(img["id"] for img in images if img["name"] == selected_image)
    
    # Shape selection
    st.subheader("Compute Shape")
    shapes = st.session_state.oci.list_shapes(compartment_id)
    selected_shape = st.selectbox(
        "Select Shape",
        options=[shape["name"] for shape in shapes],
        key="compute_shape",
        help="Select the compute shape (CPU/Memory configuration)"
    )
    
    # Get the selected shape details
    shape_details = next(shape for shape in shapes if shape["name"] == selected_shape)
    
    # Handle Flex shapes
    shape_config = {}
    if ".Flex" in selected_shape:
        st.info("This is a Flex shape. You can configure the OCPU and memory.")
        
        # Get the base shape (e.g., "VM.Standard.E4.Flex")
        base_shape = selected_shape.split(".Flex")[0] + ".Flex"
        
        # OCPU selection
        ocpus = st.number_input(
            "Number of OCPUs",
            min_value=1,
            max_value=64,  # This might need to be adjusted based on your tenancy limits
            value=1,
            step=1,
            help="Select the number of OCPUs for your Flex instance"
        )
        
        # Memory selection (GB per OCPU)
        memory_per_ocpu_options = [16, 32, 64]  # Common memory ratios
        memory_per_ocpu = st.selectbox(
            "Memory per OCPU (GB)",
            options=memory_per_ocpu_options,
            index=0,
            help="Select the amount of memory per OCPU"
        )
        
        total_memory = ocpus * memory_per_ocpu
        st.write(f"Total Memory: {total_memory} GB")
        
        shape_config = {
            "ocpus": ocpus,
            "memory_in_gbs": total_memory
        }
        
        # Show the estimated cost (if available in your implementation)
        st.info(f"Selected configuration: {ocpus} OCPUs, {total_memory}GB Memory")
    
    # Network Configuration
    st.subheader("Network Configuration")
    
    # VCN selection
    vcns = st.session_state.oci.list_vcns(compartment_id)
    selected_vcn = st.selectbox(
        "Select Virtual Cloud Network (VCN)",
        options=[vcn["name"] for vcn in vcns],
        key="compute_vcn",
        help="Select the VCN for your instance"
    ) if vcns else None
    
    subnet_id = None
    if selected_vcn:
        vcn_id = next(vcn["id"] for vcn in vcns if vcn["name"] == selected_vcn)
        subnets = st.session_state.oci.list_subnets(compartment_id, vcn_id)
        
        if subnets:
            selected_subnet = st.selectbox(
                "Select Subnet",
                options=[subnet["name"] for subnet in subnets],
                key="compute_subnet",
                help="Select the subnet for your instance"
            )
            subnet_id = next(subnet["id"] for subnet in subnets if subnet["name"] == selected_subnet)
        else:
            st.warning("No subnets found in the selected VCN. Please create a subnet first.")
    else:
        st.warning("No VCNs found. Please create a VCN first.")
    
    # Storage Configuration
    st.subheader("Storage Configuration")
    boot_volume_size = st.number_input(
        "Boot Volume Size (GB)",
        min_value=50,
        value=50,
        step=10,
        help="Specify the size of the boot volume in GB (minimum 50GB)"
    )
    
    # SSH Access
    st.subheader("SSH Access")
    ssh_key = st.text_area(
        "SSH Public Key",
        help="Paste your SSH public key for instance access"
    )
    
    # Launch Instance Button
    st.markdown("---")
    launch_disabled = not all([
        instance_name,
        selected_image,
        selected_shape,
        subnet_id,
        ssh_key
    ])
    
    if launch_disabled:
        st.warning("Please fill in all required fields to launch the instance.")
    
    if st.button("Launch Instance", disabled=launch_disabled):
        try:
            launch_args = {
                "compartment_id": compartment_id,
                "display_name": instance_name,
                "image_id": image_id,
                "shape": selected_shape,
                "subnet_id": subnet_id,
                "ssh_public_key": ssh_key,
                "boot_volume_size_in_gbs": boot_volume_size
            }
            
            # Add shape config for Flex shapes
            if shape_config:
                launch_args["shape_config"] = shape_config
            
            instance = st.session_state.oci.launch_instance(**launch_args)
            st.success(f"Instance {instance_name} launched successfully!")
            st.info("You can view the instance details in the 'Instances' tab once it's ready.")
        except Exception as e:
            st.error(f"Error launching instance: {str(e)}")

def instance_management_tab():
    st.header("Instance Management")
    
    # Compartment selection
    compartments = st.session_state.oci.list_compartments()
    selected_compartment = st.selectbox(
        "Select Compartment",
        options=[comp["name"] for comp in compartments],
        key="instance_compartment"
    )
    compartment_id = next(comp["id"] for comp in compartments if comp["name"] == selected_compartment)
    
    # Initialize session state for confirmation dialogs if not exists
    if 'show_terminate_dialog' not in st.session_state:
        st.session_state.show_terminate_dialog = False
        st.session_state.instance_to_terminate = None
    
    # Refresh button in its own column
    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("🔄 Refresh", key="refresh_instances"):
            st.rerun()
    
    # Get instances
    instances = st.session_state.oci.list_instances(compartment_id)
    
    if not instances:
        st.info("No instances found in this compartment.")
        return
    
    # Create a table view of instances
    st.markdown("### Instances")
    
    # Create the table header
    cols = st.columns([3, 2, 2, 2, 3])
    headers = ["Name", "State", "Shape", "IP Addresses", "Actions"]
    for col, header in zip(cols, headers):
        col.markdown(f"**{header}**")
    
    # Add a separator
    st.markdown("---")
    
    # Display each instance in a row
    for instance in instances:
        cols = st.columns([3, 2, 2, 2, 3])
        
        # Instance Name
        cols[0].write(instance['name'])
        
        # State with color coding
        state = instance['state']
        state_color = {
            'RUNNING': '🟢',
            'STOPPED': '🔴',
            'TERMINATING': '🟡',
            'PROVISIONING': '🟡',
            'STOPPING': '🟡',
            'STARTING': '🟡'
        }.get(state, '⚪')
        cols[1].write(f"{state_color} {state}")
        
        # Shape
        cols[2].write(instance.get('shape', 'N/A'))
        
        # IP Addresses
        ip_text = f"Public: {instance['public_ip'] or 'N/A'}\nPrivate: {instance['private_ip'] or 'N/A'}"
        cols[3].text(ip_text)
        
        # Action buttons
        action_col = cols[4]
        if state == 'RUNNING':
            if action_col.button("⏹️ Stop", key=f"stop_{instance['id']}", help="Stop this instance"):
                try:
                    st.session_state.oci.stop_instance(instance['id'])
                    st.success(f"Stopping instance {instance['name']}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error stopping instance: {str(e)}")
        
        elif state == 'STOPPED':
            if action_col.button("▶️ Start", key=f"start_{instance['id']}", help="Start this instance"):
                try:
                    st.session_state.oci.start_instance(instance['id'])
                    st.success(f"Starting instance {instance['name']}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error starting instance: {str(e)}")
        
        # Always show terminate button unless instance is already terminating
        if state not in ['TERMINATING']:
            if action_col.button("🗑️ Terminate", key=f"terminate_{instance['id']}", 
                               help="Terminate this instance", type="secondary"):
                st.session_state.show_terminate_dialog = True
                st.session_state.instance_to_terminate = instance
                st.rerun()
        
        # Add a separator between instances
        st.markdown("---")
    
    # Terminate confirmation dialog
    if st.session_state.show_terminate_dialog and st.session_state.instance_to_terminate:
        instance = st.session_state.instance_to_terminate
        
        # Create a modal-like dialog
        with st.form(key="terminate_dialog"):
            st.warning(f"⚠️ Are you sure you want to terminate instance '{instance['name']}'?")
            
            preserve_boot_volume = st.checkbox(
                "Preserve Boot Volume",
                value=True,
                help="If checked, the boot volume will be preserved and can be used to create a new instance"
            )
            
            col1, col2 = st.columns(2)
            confirm = col1.form_submit_button("Confirm Termination", type="primary")
            cancel = col2.form_submit_button("Cancel", type="secondary")
            
            if confirm:
                try:
                    st.session_state.oci.terminate_instance(
                        instance['id'],
                        preserve_boot_volume=preserve_boot_volume
                    )
                    st.success(f"Terminating instance {instance['name']}")
                    st.session_state.show_terminate_dialog = False
                    st.session_state.instance_to_terminate = None
                    st.rerun()
                except Exception as e:
                    st.error(f"Error terminating instance: {str(e)}")
            
            elif cancel:
                st.session_state.show_terminate_dialog = False
                st.session_state.instance_to_terminate = None
                st.rerun()

def main():
    st.set_page_config(
        page_title="OCI Resource Manager",
        page_icon="🌐",
        layout="wide"
    )
    
    st.title("OCI Resource Manager")
    
    tab1, tab2, tab3 = st.tabs(["Network Management", "Compute Creator", "Instance Management"])
    
    with tab1:
        network_tab()
    with tab2:
        compute_launch_tab()
    with tab3:
        instance_management_tab()

if __name__ == "__main__":
    main() 