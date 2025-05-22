import streamlit as st
from oci_utils import OCIManager

st.set_page_config(
    page_title="OCI Resource Manager",
    page_icon="🛠️",
    layout="wide"
)

# Initialize session state for refresh counter
if 'refresh_counter' not in st.session_state:
    st.session_state.refresh_counter = 0

st.title("OCI Resource Manager 🌤️")

# Region selector (global)
def get_default_region():
    import oci
    config = oci.config.from_file()
    return config["region"]

if "oci_region" not in st.session_state:
    # Use default region from config file
    try:
        default_region = get_default_region()
    except Exception:
        default_region = "us-ashburn-1"
    st.session_state["oci_region"] = default_region

# Fetch available regions using a temporary OCIManager
try:
    temp_oci_manager = OCIManager(region=st.session_state["oci_region"])
    available_regions = temp_oci_manager.list_regions()
except Exception:
    available_regions = [st.session_state["oci_region"]]

selected_region = st.selectbox(
    "Select Region 🌎",
    options=available_regions,
    index=available_regions.index(st.session_state["oci_region"]) if st.session_state["oci_region"] in available_regions else 0,
    key="region_selector"
)
if selected_region != st.session_state["oci_region"]:
    st.session_state["oci_region"] = selected_region
    st.rerun()

# After region selector, add global compartment selector
# st.markdown("---")
# st.markdown("### Select Compartment 🗂️")
oci_manager_for_compartment = OCIManager(region=st.session_state["oci_region"])
compartment_query = st.text_input("Search Compartment 🗂️", key="global_compartment_query")
compartment_options = []
selected_compartment = None
if compartment_query and len(compartment_query) >= 3:
    with st.spinner("Searching compartments..."):
        compartment_options = oci_manager_for_compartment.search_compartments(compartment_query)
    if not compartment_options:
        st.info("No compartments found matching your search.")
    else:
        comp_names = [comp["name"] for comp in compartment_options]
        selected_compartment = st.selectbox(
            "Select Compartment",
            options=comp_names,
            key="global_compartment_select"
        )
else:
    st.info("Type at least 3 letters to search for a compartment.")

if selected_compartment:
    selected_compartment_id = next(
        (comp["id"] for comp in compartment_options if comp["name"] == selected_compartment),
        None
    )
    st.session_state["oci_compartment_id"] = selected_compartment_id
    st.session_state["oci_compartment_name"] = selected_compartment
else:
    st.session_state["oci_compartment_id"] = None
    st.session_state["oci_compartment_name"] = None

tab_labels = [
    "Dashboard 🏠", "Network Management 🌐", "Instance Management 🖥️", "Autonomous Database 🍀", "Object Storage 📦"
]
tabs = st.tabs(tab_labels)

with tabs[0]:
    st.markdown("# **Dashboard 🏠**")
    try:
        oci_manager = OCIManager(region=st.session_state["oci_region"])
        selected_compartment_id = st.session_state["oci_compartment_id"]
        selected_compartment = st.session_state["oci_compartment_name"]
        if selected_compartment_id:
            st.write(f"Selected compartment: {selected_compartment} 🎯")
            
            # List instances in the selected compartment
            st.subheader("🖥️ Instances")
            instances = oci_manager.list_instances(selected_compartment_id)
            
            if instances:
                st.markdown("Let's see what compute power you have! 💪")
                st.subheader("Compute Instances 🚀")
                # Create columns for the instance table
                cols = st.columns([3, 2, 2, 2, 2, 3])
                headers = ["Name", "State", "Shape", "Private IP", "Public IP", "Actions"]
                for col, header in zip(cols, headers):
                    col.write(f"**{header}**")
                # Display each instance
                for instance in instances:
                    cols = st.columns([3, 2, 2, 2, 2, 3])
                    # Name
                    cols[0].write(instance["name"])
                    # State with color
                    state = instance["state"]
                    state_color = {
                        "RUNNING": "green",
                        "STOPPED": "red",
                        "STARTING": "orange",
                        "STOPPING": "orange",
                        "TERMINATED": "gray"
                    }.get(state, "black")
                    cols[1].write(f":{state_color}[{state}]")
                    # Shape and IPs
                    cols[2].write(instance["shape"])
                    cols[3].write(instance["private_ip"])
                    cols[4].write(instance["public_ip"])
                    # Action buttons
                    action_col = cols[5]
                    if state == "RUNNING":
                        if action_col.button("Stop", key=f"stop_{instance['id']}"):
                            try:
                                oci_manager.stop_instance(instance["id"])
                                st.success(f"Stopping instance {instance['name']}")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error stopping instance: {str(e)}")
                    elif state == "STOPPED":
                        if action_col.button("Start", key=f"start_{instance['id']}"):
                            try:
                                oci_manager.start_instance(instance["id"])
                                st.success(f"Starting instance {instance['name']}")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error starting instance: {str(e)}")
                    # Terminate button (always available)
                    if action_col.button("Terminate", key=f"term_{instance['id']}"):
                        if st.warning(f"Are you sure you want to terminate {instance['name']}? 😱"):
                            try:
                                oci_manager.terminate_instance(instance["id"])
                                st.success(f"Terminating instance {instance['name']} 🗑️")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error terminating instance: {str(e)}")
            else:
                st.info("No instances found in this compartment. 🤷‍♂️")

            # Autonomous Database Section
            st.subheader("Autonomous Databases 🍀")
            databases = oci_manager.list_autonomous_databases(selected_compartment_id)
            
            if databases:
                st.markdown("Your smart databases are ready to serve! 🧠")
                # Create columns for the database table
                cols = st.columns([3, 2, 2, 2, 2, 3])
                headers = ["Name", "State", "Workload", "CPU Cores", "Storage (TB)", "Actions"]
                for col, header in zip(cols, headers):
                    col.write(f"**{header}**")
                # Display each database
                for db in databases:
                    cols = st.columns([3, 2, 2, 2, 2, 3])
                    # Name
                    cols[0].write(db["display_name"])
                    # State with color
                    state = db["lifecycle_state"]
                    state_color = {
                        "AVAILABLE": "green",
                        "STOPPED": "red",
                        "STARTING": "orange",
                        "STOPPING": "orange",
                        "TERMINATED": "gray",
                        "TERMINATING": "orange"
                    }.get(state, "black")
                    cols[1].write(f":{state_color}[{state}]")
                    # Workload and Resources
                    cols[2].write(db["db_workload"])
                    cols[3].write(str(db["cpu_core_count"]))
                    cols[4].write(str(db["data_storage_size_in_tbs"]))
                    # Action buttons
                    action_col = cols[5]
                    if db.get("service_console_url"):
                        ords_url = db["service_console_url"]
                        action_col.markdown(f"[Open ORDS 🚪]({ords_url}){{:target=\"_blank\"}}", unsafe_allow_html=True)
                    if state == "AVAILABLE":
                        if action_col.button("Stop", key=f"stop_db_{db['id']}"):
                            try:
                                oci_manager.stop_autonomous_database(db["id"])
                                st.success(f"Stopping database {db['display_name']} 🛑")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error stopping database: {str(e)}")
                    elif state == "STOPPED":
                        if action_col.button("Start", key=f"start_db_{db['id']}"):
                            try:
                                oci_manager.start_autonomous_database(db["id"])
                                st.success(f"Starting database {db['display_name']} 🚦")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error starting database: {str(e)}")
                    if state not in ["TERMINATING", "TERMINATED"]:
                        if action_col.button("Terminate", key=f"term_db_{db['id']}"):
                            if st.warning(f"Are you sure you want to terminate {db['display_name']}? 😱"):
                                try:
                                    oci_manager.terminate_autonomous_database(db["id"])
                                    st.success(f"Terminating database {db['display_name']} 🗑️")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error terminating database: {str(e)}")
            else:
                st.info("No Autonomous Databases found in this compartment. 📦")
        else:
            st.info("Please search for and select a compartment to view resources.")
    except Exception as e:
        st.error(f"Error: {str(e)}")

with tabs[1]:
    st.markdown("# **Network Management 🌐**")
    try:
        oci_manager = OCIManager(region=st.session_state["oci_region"])
        selected_compartment_id = st.session_state["oci_compartment_id"]
        if selected_compartment_id:
            # Virtual Cloud Networks section (no expander)
            st.markdown("## Virtual Cloud Networks 🌩️")
            if st.button("Create New VCN", key="create_vcn_button"):
                st.session_state.show_create_vcn = True
            if st.session_state.get('show_create_vcn', False):
                with st.form("create_vcn_form"):
                    st.subheader("Create New VCN 🆕")
                    vcn_name = st.text_input("VCN Name")
                    cidr_block = st.text_input("CIDR Block (e.g., 10.0.0.0/16)")
                    dns_label = st.text_input("DNS Label (optional)")
                    is_ipv6 = st.checkbox("Enable IPv6")
                    if st.form_submit_button("Create"):
                        try:
                            result = oci_manager.create_vcn(
                                selected_compartment_id,
                                vcn_name,
                                cidr_block,
                                dns_label if dns_label else None,
                                is_ipv6
                            )
                            st.success(f"VCN {vcn_name} created successfully! 🎉")
                            st.session_state.show_create_vcn = False
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error creating VCN: {str(e)} 😬")
            vcns = oci_manager.list_vcns(selected_compartment_id)
            if vcns:
                st.markdown("Your clouds are ready to connect! ☁️")
                cols = st.columns([3, 2, 2, 2, 2])
                headers = ["Name", "CIDR Block", "Subnets", "Security Lists", "Actions"]
                for col, header in zip(cols, headers):
                    col.write(f"**{header}**")
                for vcn in vcns:
                    cols = st.columns([3, 2, 2, 2, 2])
                    cols[0].write(vcn["name"])
                    cols[1].write(vcn["cidr"])
                    subnets = oci_manager.list_subnets(selected_compartment_id, vcn["id"])
                    security_lists = oci_manager.list_security_lists(selected_compartment_id, vcn["id"])
                    cols[2].write(f"{len(subnets)} subnets")
                    cols[3].write(f"{len(security_lists)} security lists")
                    action_col = cols[4]
                    if action_col.button("Create Subnet", key=f"create_subnet_{vcn['id']}"):
                        st.session_state.selected_vcn = vcn
                        st.session_state.show_create_subnet = True
                    if action_col.button("Delete VCN", key=f"delete_vcn_{vcn['id']}"):
                        if st.warning(f"Are you sure you want to delete VCN {vcn['name']}? ⚠️"):
                            try:
                                oci_manager.delete_vcn(vcn["id"])
                                st.success(f"VCN {vcn['name']} deleted successfully! 🗑️")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error deleting VCN: {str(e)} 😬")
            else:
                st.info("No VCNs found in this compartment. 🌫️")
            # Security Lists section (no expander)
            st.markdown("## Security Lists 🔒")
            if st.button("Create New Security List", key="create_security_list_button"):
                st.session_state.show_create_security_list = True
            if st.session_state.get('show_create_security_list', False):
                with st.form("create_security_list_form"):
                    st.subheader("Create New Security List 🆕")
                    vcns = oci_manager.list_vcns(selected_compartment_id)
                    vcn_options = {vcn["name"]: vcn["id"] for vcn in vcns}
                    selected_vcn_name = st.selectbox(
                        "Select VCN",
                        options=list(vcn_options.keys())
                    )
                    security_list_name = st.text_input("Security List Name")
                    st.write("Ingress Rules")
                    ingress_rules = []
                    num_ingress = st.number_input("Number of Ingress Rules", min_value=1, max_value=10, value=1)
                    for i in range(num_ingress):
                        with st.expander(f"Ingress Rule {i+1}"):
                            protocol = st.selectbox(
                                "Protocol",
                                options=["TCP", "UDP", "ICMP", "ALL"],
                                key=f"ingress_protocol_{i}"
                            )
                            source = st.text_input("Source CIDR", value="0.0.0.0/0", key=f"ingress_source_{i}")
                            port_min = st.number_input("Port Range Start", min_value=1, max_value=65535, value=22, key=f"ingress_port_min_{i}")
                            port_max = st.number_input("Port Range End", min_value=1, max_value=65535, value=22, key=f"ingress_port_max_{i}")
                            ingress_rules.append({
                                "protocol": protocol,
                                "source": source,
                                "port_min": port_min,
                                "port_max": port_max
                            })
                    st.write("Egress Rules")
                    egress_rules = []
                    num_egress = st.number_input("Number of Egress Rules", min_value=1, max_value=10, value=1)
                    for i in range(num_egress):
                        with st.expander(f"Egress Rule {i+1}"):
                            protocol = st.selectbox(
                                "Protocol",
                                options=["TCP", "UDP", "ICMP", "ALL"],
                                key=f"egress_protocol_{i}"
                            )
                            destination = st.text_input("Destination CIDR", value="0.0.0.0/0", key=f"egress_dest_{i}")
                            port_min = st.number_input("Port Range Start", min_value=1, max_value=65535, value=22, key=f"egress_port_min_{i}")
                            port_max = st.number_input("Port Range End", min_value=1, max_value=65535, value=22, key=f"egress_port_max_{i}")
                            egress_rules.append({
                                "protocol": protocol,
                                "destination": destination,
                                "port_min": port_min,
                                "port_max": port_max
                            })
                    if st.form_submit_button("Create Security List"):
                        try:
                            oci_ingress_rules = []
                            for rule in ingress_rules:
                                oci_ingress_rules.append({
                                    "protocol": rule["protocol"],
                                    "source": rule["source"],
                                    "tcpOptions": {
                                        "destinationPortRange": {
                                            "min": rule["port_min"],
                                            "max": rule["port_max"]
                                        }
                                    } if rule["protocol"] in ["TCP", "UDP"] else None
                                })
                            oci_egress_rules = []
                            for rule in egress_rules:
                                oci_egress_rules.append({
                                    "protocol": rule["protocol"],
                                    "destination": rule["destination"],
                                    "tcpOptions": {
                                        "destinationPortRange": {
                                            "min": rule["port_min"],
                                            "max": rule["port_max"]
                                        }
                                    } if rule["protocol"] in ["TCP", "UDP"] else None
                                })
                            result = oci_manager.create_security_list(
                                selected_compartment_id,
                                vcn_options[selected_vcn_name],
                                security_list_name,
                                oci_ingress_rules,
                                oci_egress_rules
                            )
                            st.success(f"Security List {security_list_name} created successfully!")
                            st.session_state.show_create_security_list = False
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error creating security list: {str(e)}")
            for vcn in vcns:
                st.markdown(f"### Security Lists in VCN: {vcn['name']} 🔐")
                security_lists = oci_manager.list_security_lists(selected_compartment_id, vcn["id"])
                if security_lists:
                    cols = st.columns([3, 2, 2, 2])
                    headers = ["Name", "Ingress Rules", "Egress Rules", "Actions"]
                    for col, header in zip(cols, headers):
                        col.write(f"**{header}**")
                    for sl in security_lists:
                        cols = st.columns([3, 2, 2, 2])
                        sl_details = oci_manager.get_security_list(sl["id"])
                        cols[0].write(sl["name"])
                        cols[1].write(f"{len(sl_details['ingress_rules'])} rules")
                        cols[2].write(f"{len(sl_details['egress_rules'])} rules")
                        action_col = cols[3]
                        if action_col.button("View Rules", key=f"view_rules_{sl['id']}"):
                            st.session_state.selected_security_list_id = sl["id"]
                        if action_col.button("Delete", key=f"delete_sl_{sl['id']}"):
                            if st.warning(f"Are you sure you want to delete Security List {sl['name']}? ⚠️"):
                                try:
                                    oci_manager.delete_security_list(sl["id"])
                                    st.success(f"Security List {sl['name']} deleted successfully! 🗑️")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error deleting security list: {str(e)} 😬")
                        if st.session_state.get('selected_security_list_id') == sl["id"]:
                            st.markdown("**Ingress Rules** 🟢")
                            for i, rule in enumerate(sl_details['ingress_rules']):
                                st.write(f"Rule {i+1}:")
                                st.write(f"- Protocol: {rule['protocol']}")
                                st.write(f"- Source: {rule['source']}")
                                if 'tcpOptions' in rule and rule['tcpOptions']:
                                    st.write(f"- Port Range: {rule['tcpOptions']['destinationPortRange']['min']}-{rule['tcpOptions']['destinationPortRange']['max']}")
                            st.markdown("**Egress Rules** 🔵")
                            for i, rule in enumerate(sl_details['egress_rules']):
                                st.write(f"Rule {i+1}:")
                                st.write(f"- Protocol: {rule['protocol']}")
                                st.write(f"- Destination: {rule['destination']}")
                                if 'tcpOptions' in rule and rule['tcpOptions']:
                                    st.write(f"- Port Range: {rule['tcpOptions']['destinationPortRange']['min']}-{rule['tcpOptions']['destinationPortRange']['max']}")
                else:
                    st.info("No Security Lists found in this VCN. 🛡️")
            # Route Tables section (no expander)
            st.markdown("## Route Tables 🛣️")
            if st.button("Add Route Table", key="create_route_table_button"):
                st.session_state.show_create_route_table = True
            if st.session_state.get('show_create_route_table', False):
                with st.form("create_route_table_form"):
                    st.subheader("Create New Route Table 🆕")
                    # VCN Selection
                    vcns = oci_manager.list_vcns(selected_compartment_id)
                    vcn_options = {vcn["name"]: vcn["id"] for vcn in vcns}
                    selected_vcn_name = st.selectbox(
                        "Select VCN",
                        options=list(vcn_options.keys()),
                        key="route_table_vcn"
                    )
                    route_table_name = st.text_input("Route Table Name")
                    st.write("Route Rules")
                    route_rules = []
                    num_rules = st.number_input("Number of Route Rules", min_value=1, max_value=10, value=1)
                    for i in range(num_rules):
                        st.markdown(f"**Route Rule {i+1}**")
                        igw_list = oci_manager.list_internet_gateways(selected_compartment_id, vcn_options[selected_vcn_name])
                        natgw_list = oci_manager.list_nat_gateways(selected_compartment_id, vcn_options[selected_vcn_name])
                        sgw_list = oci_manager.list_service_gateways(selected_compartment_id, vcn_options[selected_vcn_name])
                        gateway_options = {
                            "Internet Gateway": [{"id": gw["id"], "name": gw["name"]} for gw in igw_list],
                            "NAT Gateway": [{"id": gw["id"], "name": gw["name"]} for gw in natgw_list],
                            "Service Gateway": [{"id": gw["id"], "name": gw["name"]} for gw in sgw_list]
                        }
                        destination = st.text_input("Destination CIDR", value="0.0.0.0/0", key=f"route_dest_{i}")
                        gateway_type = st.selectbox(
                            "Gateway Type",
                            options=list(gateway_options.keys()),
                            key=f"gateway_type_{i}"
                        )
                        if gateway_options[gateway_type]:
                            gateway_name = st.selectbox(
                                f"Select {gateway_type}",
                                options=[gw["name"] for gw in gateway_options[gateway_type]],
                                key=f"gateway_name_{i}"
                            )
                            gateway_id = next(gw["id"] for gw in gateway_options[gateway_type] if gw["name"] == gateway_name)
                            route_rules.append({
                                "destination": destination,
                                "network_entity_id": gateway_id,
                                "destination_type": "CIDR_BLOCK"
                            })
                    if st.form_submit_button("Create Route Table"):
                        try:
                            result = oci_manager.create_route_table(
                                selected_compartment_id,
                                vcn_options[selected_vcn_name],
                                route_table_name,
                                route_rules
                            )
                            st.success(f"Route Table {route_table_name} created successfully!")
                            st.session_state.show_create_route_table = False
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error creating route table: {str(e)}")
            # List Route Tables for each VCN
            vcns = oci_manager.list_vcns(selected_compartment_id)
            for vcn in vcns:
                st.markdown(f"### Route Tables in VCN: {vcn['name']}")
                route_tables = oci_manager.list_route_tables(selected_compartment_id, vcn["id"])
                if route_tables:
                    for rt in route_tables:
                        st.write(f"**Route Table: {rt['name']}**")
                        st.write("Route Rules:")
                        for rule in rt['rules']:
                            st.write(f"- Destination: {rule.destination}")
                            st.write(f"- Target: {rule.network_entity_id}")
                        st.write("---")
                else:
                    st.info("No Route Tables found in this VCN.")
            # Gateways section (no expander)
            st.markdown("## Gateways 🚪")
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Add Internet Gateway", key="create_igw_button"):
                    st.session_state.show_create_igw = True
            with col2:
                if st.button("Add NAT Gateway", key="create_natgw_button"):
                    st.session_state.show_create_natgw = True
            with col3:
                if st.button("Add Service Gateway", key="create_sgw_button"):
                    st.session_state.show_create_sgw = True
            # Internet Gateway Form
            if st.session_state.get('show_create_igw', False):
                with st.form("create_igw_form"):
                    st.subheader("Create Internet Gateway")
                    vcns = oci_manager.list_vcns(selected_compartment_id)
                    vcn_options = {vcn["name"]: vcn["id"] for vcn in vcns}
                    selected_vcn_name = st.selectbox(
                        "Select VCN",
                        options=list(vcn_options.keys()),
                        key="igw_vcn"
                    )
                    igw_name = st.text_input("Internet Gateway Name")
                    is_enabled = st.checkbox("Enabled", value=True)
                    if st.form_submit_button("Create"):
                        try:
                            result = oci_manager.create_internet_gateway(
                                selected_compartment_id,
                                vcn_options[selected_vcn_name],
                                igw_name,
                                is_enabled
                            )
                            st.success(f"Internet Gateway {igw_name} created successfully!")
                            st.session_state.show_create_igw = False
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error creating internet gateway: {str(e)}")
            # NAT Gateway Form
            if st.session_state.get('show_create_natgw', False):
                with st.form("create_natgw_form"):
                    st.subheader("Create NAT Gateway")
                    vcns = oci_manager.list_vcns(selected_compartment_id)
                    vcn_options = {vcn["name"]: vcn["id"] for vcn in vcns}
                    selected_vcn_name = st.selectbox(
                        "Select VCN",
                        options=list(vcn_options.keys()),
                        key="natgw_vcn"
                    )
                    natgw_name = st.text_input("NAT Gateway Name")
                    block_traffic = st.checkbox("Block Traffic", value=False)
                    if st.form_submit_button("Create"):
                        try:
                            result = oci_manager.create_nat_gateway(
                                selected_compartment_id,
                                vcn_options[selected_vcn_name],
                                natgw_name,
                                block_traffic
                            )
                            st.success(f"NAT Gateway {natgw_name} created successfully!")
                            st.session_state.show_create_natgw = False
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error creating NAT gateway: {str(e)}")
            # Service Gateway Form
            if st.session_state.get('show_create_sgw', False):
                with st.form("create_sgw_form"):
                    st.subheader("Create Service Gateway")
                    vcns = oci_manager.list_vcns(selected_compartment_id)
                    vcn_options = {vcn["name"]: vcn["id"] for vcn in vcns}
                    selected_vcn_name = st.selectbox(
                        "Select VCN",
                        options=list(vcn_options.keys()),
                        key="sgw_vcn"
                    )
                    sgw_name = st.text_input("Service Gateway Name")
                    services = oci_manager.list_available_services(selected_compartment_id)
                    selected_services = st.multiselect(
                        "Select Services",
                        options=[svc["name"] for svc in services]
                    )
                    if st.form_submit_button("Create"):
                        try:
                            result = oci_manager.create_service_gateway(
                                selected_compartment_id,
                                vcn_options[selected_vcn_name],
                                sgw_name,
                                selected_services
                            )
                            st.success(f"Service Gateway {sgw_name} created successfully!")
                            st.session_state.show_create_sgw = False
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error creating service gateway: {str(e)}")
            # List Gateways for each VCN
            for vcn in vcns:
                st.markdown(f"### Gateways in VCN: {vcn['name']}")
                igws = oci_manager.list_internet_gateways(selected_compartment_id, vcn["id"])
                if igws:
                    st.write("**Internet Gateways**")
                    for igw in igws:
                        st.write(f"- {igw['name']} (Enabled: {igw['enabled']})")
                natgws = oci_manager.list_nat_gateways(selected_compartment_id, vcn["id"])
                if natgws:
                    st.write("**NAT Gateways**")
                    for natgw in natgws:
                        st.write(f"- {natgw['name']} (Blocked: {natgw['enabled']})")
                sgws = oci_manager.list_service_gateways(selected_compartment_id, vcn["id"])
                if sgws:
                    st.write("**Service Gateways**")
                    for sgw in sgws:
                        st.write(f"- {sgw['name']} (Services: {', '.join(sgw['services'])})")
        else:
            st.info("Please search for and select a compartment to manage network resources.")
    except Exception as e:
        st.error(f"Error: {str(e)} 😬")

# Instance Management Tab
with tabs[2]:
    st.markdown("# **Instance Management 🖥️**")
    try:
        oci_manager = OCIManager(region=st.session_state["oci_region"])
        selected_compartment_id = st.session_state["oci_compartment_id"]
        if selected_compartment_id:
            if st.button("Create Compute", key="create_compute_button"):
                st.session_state.show_create_compute = True
            if st.session_state.get('show_create_compute', False):
                with st.form("create_compute_form"):
                    st.subheader("Create Compute Instance 🆕")
                    instance_name = st.text_input("Instance Name")
                    images = oci_manager.list_images(selected_compartment_id)
                    image_options = {img["name"]: img["id"] for img in images}
                    image_name = st.selectbox("Image", options=list(image_options.keys()))
                    shapes = oci_manager.list_shapes(selected_compartment_id)
                    shape_options = [shape["name"] for shape in shapes]
                    shape_name = st.selectbox("Shape", options=shape_options)
                    subnets = []
                    vcns = oci_manager.list_vcns(selected_compartment_id)
                    for vcn in vcns:
                        subnets.extend(oci_manager.list_subnets(selected_compartment_id, vcn["id"]))
                    subnet_options = {subnet["name"]: subnet["id"] for subnet in subnets}
                    subnet_name = st.selectbox("Subnet", options=list(subnet_options.keys()))
                    ssh_key = st.text_area("SSH Public Key")
                    boot_volume_size = st.number_input("Boot Volume Size (GB, optional)", min_value=0, value=0)
                    shape_config = None
                    if ".Flex" in shape_name:
                        st.markdown("**This is a Flex shape. Please specify OCPUs and Memory (GB).**")
                        ocpus = st.number_input("OCPUs", min_value=1, value=1, step=1)
                        memory = st.number_input("Memory (GB)", min_value=1, value=6, step=1)
                        shape_config = {"ocpus": ocpus, "memory_in_gbs": memory}
                    if st.form_submit_button("Create"):
                        try:
                            result = oci_manager.launch_instance(
                                compartment_id=selected_compartment_id,
                                display_name=instance_name,
                                image_id=image_options[image_name],
                                shape=shape_name,
                                subnet_id=subnet_options[subnet_name],
                                ssh_public_key=ssh_key,
                                boot_volume_size_in_gbs=boot_volume_size if boot_volume_size > 0 else None,
                                shape_config=shape_config
                            )
                            st.success(f"Instance {instance_name} created successfully!")
                            st.session_state.show_create_compute = False
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error creating instance: {str(e)}")
            # Instance Overview (no expander)
            st.markdown("## Instances Overview 🖥️")
            instances = oci_manager.list_instances(selected_compartment_id)
            if instances:
                st.markdown("Here are your mighty compute warriors! ⚔️")
                cols = st.columns([3, 2, 2, 2, 2, 3])
                headers = ["Name", "State", "Shape", "Private IP", "Public IP", "Actions"]
                for col, header in zip(cols, headers):
                    col.write(f"**{header}**")
                for instance in instances:
                    cols = st.columns([3, 2, 2, 2, 2, 3])
                    cols[0].write(instance["name"])
                    state = instance["state"]
                    state_color = {
                        "RUNNING": "green",
                        "STOPPED": "red",
                        "STARTING": "orange",
                        "STOPPING": "orange",
                        "TERMINATED": "gray"
                    }.get(state, "black")
                    cols[1].write(f":{state_color}[{state}]")
                    cols[2].write(instance["shape"])
                    cols[3].write(instance["private_ip"])
                    cols[4].write(instance["public_ip"])
                    action_col = cols[5]
                    if state == "RUNNING":
                        if action_col.button("Stop", key=f"stop_{instance['id']}"):
                            try:
                                oci_manager.stop_instance(instance["id"])
                                st.success(f"Stopping instance {instance['name']}")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error stopping instance: {str(e)}")
                    elif state == "STOPPED":
                        if action_col.button("Start", key=f"start_{instance['id']}"):
                            try:
                                oci_manager.start_instance(instance["id"])
                                st.success(f"Starting instance {instance['name']}")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error starting instance: {str(e)}")
                    if action_col.button("Terminate", key=f"term_{instance['id']}"):
                        if st.warning(f"Are you sure you want to terminate {instance['name']}?"):
                            try:
                                oci_manager.terminate_instance(instance["id"])
                                st.success(f"Terminating instance {instance['name']}")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error terminating instance: {str(e)}")
            else:
                st.info("No instances found in this compartment. 🤷‍♂️")
        else:
            st.info("Please search for and select a compartment to manage instances.")
    except Exception as e:
        st.error(f"Error: {str(e)} 😬")

# Autonomous Database Tab
with tabs[3]:
    st.markdown("# **Autonomous Database Management 🍀**")
    try:
        oci_manager = OCIManager(region=st.session_state["oci_region"])
        selected_compartment_id = st.session_state["oci_compartment_id"]
        if selected_compartment_id:
            if st.button("Create Autonomous Database", key="create_adb_button"):
                st.session_state.show_create_adb = True
            if st.session_state.get('show_create_adb', False):
                with st.form("create_adb_form"):
                    st.subheader("Create Autonomous Database 🆕")
                    adb_name = st.text_input("Display Name")
                    db_name = st.text_input("Database Name (4-30 alphanumeric characters)")
                    db_workload = st.selectbox("Workload", ["OLTP", "DW", "JSON", "APEX"])
                    db_version = st.selectbox("Database Version", ["19c", "23ai"])
                    cpu_cores = st.number_input("OCPUs", min_value=1, value=1)
                    storage_tbs = st.number_input("Storage (TB)", min_value=1, value=1)
                    admin_password = st.text_input("Admin Password", type="password")
                    auto_scaling = st.checkbox("Enable Auto Scaling", value=True)
                    is_free_tier = st.checkbox("Free Tier", value=False)
                    is_developer_edition = st.checkbox("Developer Edition", value=False)
                    if st.form_submit_button("Create"):
                        try:
                            result = oci_manager.create_autonomous_database(
                                compartment_id=selected_compartment_id,
                                display_name=adb_name,
                                db_name=db_name,
                                admin_password=admin_password,
                                cpu_core_count=cpu_cores,
                                data_storage_size_in_tbs=storage_tbs,
                                db_workload=db_workload,
                                is_auto_scaling_enabled=auto_scaling,
                                is_free_tier=is_free_tier,
                                is_developer_edition=is_developer_edition,
                                db_version=db_version
                            )
                            st.success(f"Autonomous Database {adb_name} created successfully!")
                            st.session_state.show_create_adb = False
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error creating Autonomous Database: {str(e)}")
            # Autonomous Databases Overview (no expander)
            st.markdown("## Autonomous Databases Overview 🍀")
            dbs = oci_manager.list_autonomous_databases(selected_compartment_id)
            if dbs:
                st.markdown("Your smart databases are ready to serve! 🧠")
                cols = st.columns([3, 2, 2, 2, 2, 3])
                headers = ["Name", "State", "Workload", "OCPUs", "Storage (TB)", "Actions"]
                for col, header in zip(cols, headers):
                    col.write(f"**{header}**")
                for db in dbs:
                    cols = st.columns([3, 2, 2, 2, 2, 3])
                    cols[0].write(db["display_name"])
                    cols[0].write(f"ORDS URL: {db.get('service_console_url')}")
                    state = db["lifecycle_state"]
                    state_color = {
                        "AVAILABLE": "green",
                        "STOPPED": "red",
                        "STARTING": "orange",
                        "STOPPING": "orange",
                        "TERMINATED": "gray",
                        "TERMINATING": "orange"
                    }.get(state, "black")
                    cols[1].write(f":{state_color}[{state}]")
                    cols[2].write(db["db_workload"])
                    cols[3].write(str(db["cpu_core_count"]))
                    cols[4].write(str(db["data_storage_size_in_tbs"]))
                    action_col = cols[5]
                    if db.get("service_console_url"):
                        ords_url = db["service_console_url"]
                        action_col.markdown(f"[Open ORDS]({ords_url}){{:target=\"_blank\"}}", unsafe_allow_html=True)
                    if state == "AVAILABLE":
                        if action_col.button("Stop", key=f"stop_db_{db['id']}"):
                            try:
                                oci_manager.stop_autonomous_database(db["id"])
                                st.success(f"Stopping database {db['display_name']}")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error stopping database: {str(e)}")
                    elif state == "STOPPED":
                        if action_col.button("Start", key=f"start_db_{db['id']}"):
                            try:
                                oci_manager.start_autonomous_database(db["id"])
                                st.success(f"Starting database {db['display_name']}")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error starting database: {str(e)}")
                    if state not in ["TERMINATING", "TERMINATED"]:
                        if action_col.button("Terminate", key=f"term_db_{db['id']}"):
                            if st.warning(f"Are you sure you want to terminate {db['display_name']}?"):
                                try:
                                    oci_manager.terminate_autonomous_database(db["id"])
                                    st.success(f"Terminating database {db['display_name']}")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error terminating database: {str(e)}")
            else:
                st.info("No Autonomous Databases found in this compartment. 📦")
        else:
            st.info("Please search for and select a compartment to manage Autonomous Databases.")
    except Exception as e:
        st.error(f"Error: {str(e)} 😬")

# Object Storage Tab
with tabs[4]:
    st.markdown("# **Object Storage Management 📦**")
    try:
        oci_manager = OCIManager(region=st.session_state["oci_region"])
        selected_compartment_id = st.session_state["oci_compartment_id"]
        
        if selected_compartment_id:
            # Create Bucket Section
            if st.button("Create New Bucket", key="create_bucket_button"):
                st.session_state.show_create_bucket = True
                
            if st.session_state.get('show_create_bucket', False):
                with st.form("create_bucket_form"):
                    st.subheader("Create New Bucket 🆕")
                    bucket_name = st.text_input("Bucket Name")
                    storage_tier = st.selectbox(
                        "Storage Tier",
                        ["Standard", "Archive", "InfrequentAccess"]
                    )
                    public_access = st.checkbox("Public Access", value=False)
                    
                    if st.form_submit_button("Create"):
                        try:
                            result = oci_manager.create_bucket(
                                compartment_id=selected_compartment_id,
                                name=bucket_name,
                                storage_tier=storage_tier,
                                public_access=public_access
                            )
                            st.success(f"Bucket {bucket_name} created successfully! 🎉")
                            st.session_state.show_create_bucket = False
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error creating bucket: {str(e)}")
            
            # List Buckets
            st.markdown("## Buckets Overview 📦")
            buckets = oci_manager.list_buckets(selected_compartment_id)
            
            if buckets:
                st.markdown("Your storage containers are ready! 🎯")
                for bucket in buckets:
                    with st.expander(f"📦 {bucket['name']} ({bucket['storage_tier']})"):
                        # File Upload Section
                        st.markdown("### Upload Files 📤")
                        uploaded_file = st.file_uploader(
                            "Choose a file to upload",
                            key=f"uploader_{bucket['name']}"
                        )
                        
                        if uploaded_file is not None:
                            upload_key = f"upload_{bucket['name']}"
                            
                            # Initialize dialog state if not exists
                            if f"show_upload_dialog_{upload_key}" not in st.session_state:
                                st.session_state[f"show_upload_dialog_{upload_key}"] = False
                            
                            # Show dialog if state is True
                            if st.session_state[f"show_upload_dialog_{upload_key}"]:
                                st.dialog("File Already Exists")
                                st.warning(f"A file named '{uploaded_file.name}' already exists in this bucket. What would you like to do? 🤔")
                                col1, col2, col3 = st.columns(3)
                                
                                if col1.button("Replace", type="primary"):
                                    try:
                                        oci_manager.upload_object(
                                            bucket_name=bucket['name'],
                                            object_name=uploaded_file.name,
                                            file_data=uploaded_file.getvalue()
                                        )
                                        st.success(f"File {uploaded_file.name} replaced successfully! 🎉")
                                        st.session_state[f"show_upload_dialog_{upload_key}"] = False
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error replacing file: {str(e)}")
                                
                                if col2.button("Keep Both"):
                                    try:
                                        # Add "copy" to the filename
                                        name_parts = uploaded_file.name.rsplit('.', 1)
                                        new_name = f"{name_parts[0]}_copy.{name_parts[1]}" if len(name_parts) > 1 else f"{name_parts[0]}_copy"
                                        
                                        # Check if the copy name already exists
                                        existing_objects = oci_manager.list_objects(bucket['name'])
                                        copy_exists = any(obj['name'] == new_name for obj in existing_objects)
                                        
                                        if copy_exists:
                                            # If copy exists, add a number to make it unique
                                            counter = 1
                                            while any(obj['name'] == f"{name_parts[0]}_copy{counter}.{name_parts[1]}" if len(name_parts) > 1 else f"{name_parts[0]}_copy{counter}" for obj in existing_objects):
                                                counter += 1
                                            new_name = f"{name_parts[0]}_copy{counter}.{name_parts[1]}" if len(name_parts) > 1 else f"{name_parts[0]}_copy{counter}"
                                        
                                        # Upload the file with the new name
                                        oci_manager.upload_object(
                                            bucket_name=bucket['name'],
                                            object_name=new_name,
                                            file_data=uploaded_file.getvalue()
                                        )
                                        st.success(f"File uploaded as {new_name} successfully! 🎉")
                                        st.session_state[f"show_upload_dialog_{upload_key}"] = False
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error uploading file: {str(e)}")
                                
                                if col3.button("Cancel"):
                                    st.session_state[f"show_upload_dialog_{upload_key}"] = False
                                    st.rerun()
                            
                            # Handle initial upload button click
                            if st.button("Upload", key=upload_key):
                                try:
                                    # Check if file already exists
                                    existing_objects = oci_manager.list_objects(bucket['name'])
                                    file_exists = any(obj['name'] == uploaded_file.name for obj in existing_objects)
                                    
                                    if file_exists:
                                        st.session_state[f"show_upload_dialog_{upload_key}"] = True
                                        st.rerun()
                                    else:
                                        # If file doesn't exist, upload directly
                                        oci_manager.upload_object(
                                            bucket_name=bucket['name'],
                                            object_name=uploaded_file.name,
                                            file_data=uploaded_file.getvalue()
                                        )
                                        st.success(f"File {uploaded_file.name} uploaded successfully! 🎉")
                                        st.rerun()
                                except Exception as e:
                                    st.error(f"Error uploading file: {str(e)}")
                                    st.rerun()
                        
                        # List Objects in Bucket
                        st.markdown("### Files in Bucket 📋")
                        objects = oci_manager.list_objects(bucket['name'])
                        
                        if objects:
                            cols = st.columns([4, 2, 2, 1])
                            headers = ["Name", "Size", "Last Modified", "Actions"]
                            for col, header in zip(cols, headers):
                                col.write(f"**{header}**")
                            
                            for obj in objects:
                                cols = st.columns([4, 2, 2, 1])
                                cols[0].write(obj['name'])
                                # Format file size with proper handling of None values
                                size = obj.get('size', 0)
                                if size is not None:
                                    if size < 1024:
                                        size_str = f"{size} B"
                                    elif size < 1024 * 1024:
                                        size_str = f"{size/1024:.2f} KB"
                                    elif size < 1024 * 1024 * 1024:
                                        size_str = f"{size/(1024*1024):.2f} MB"
                                    else:
                                        size_str = f"{size/(1024*1024*1024):.2f} GB"
                                else:
                                    size_str = "N/A"
                                cols[1].write(size_str)
                                cols[2].write(str(obj.get('time_modified', 'N/A')))
                                
                                # Delete button with confirmation dialog
                                delete_key = f"delete_{bucket['name']}_{obj['name']}"
                                if cols[3].button("🗑️", key=delete_key):
                                    st.session_state[f"show_delete_dialog_{delete_key}"] = True
                                
                                # Show confirmation dialog if delete was clicked
                                if st.session_state.get(f"show_delete_dialog_{delete_key}", False):
                                    st.dialog("Confirm Delete")
                                    st.warning(f"Are you sure you want to delete {obj['name']}? This action cannot be undone! 😱")
                                    col1, col2 = st.columns(2)
                                    if col1.button("Yes, Delete", type="primary"):
                                        try:
                                            oci_manager.delete_object(
                                                bucket_name=bucket['name'],
                                                object_name=obj['name']
                                            )
                                            st.success(f"File {obj['name']} deleted successfully! 🗑️")
                                            st.session_state[f"show_delete_dialog_{delete_key}"] = False
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Error deleting file: {str(e)}")
                                    if col2.button("Cancel"):
                                        st.session_state[f"show_delete_dialog_{delete_key}"] = False
                                        st.rerun()
                        else:
                            st.info("No files in this bucket. Time to upload some! 📤")
            else:
                st.info("No buckets found in this compartment. Create one to get started! 🚀")
        else:
            st.info("Please search for and select a compartment to manage Object Storage.")
    except Exception as e:
        st.error(f"Error: {str(e)} 😬")

# Uncomment the following to ensure main() is called
#    def main():
#     st.write("Main function called")

#    if __name__ == "__main__":
#     main()
