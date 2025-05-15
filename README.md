# ☁️ OCI Resource Manager GUI

A lightweight, locally hosted GUI for managing Oracle Cloud Infrastructure (OCI) resources — no cloud console hopping required. Built with **Python** and **Streamlit**, this tool brings simplicity and visibility to your cloud environment right from your terminal.

## 🚀 Features

Easily perform common cloud operations through a user-friendly interface:

- 🔧 **Network Management** — Create and manage VCNs, subnets, route tables, security lists, and more.
- 🖥️ **Compute Management** — Launch, start, stop, and terminate compute instances with ease.
- 📈 **Instance Monitoring** — View and track instance statuses in real time.

## 🛠️ Prerequisites

Before you begin, ensure the following are in place:

- Python **3.8+**
- OCI CLI/SDK configuration (`~/.oci/config`)
- Valid OCI credentials with appropriate permissions

### 🔧 Setting Up Your OCI Config File

If you don’t already have a config file for the OCI CLI, follow these steps:

1. **Install the OCI CLI** (if not already installed):
   ```bash
   pip install oci-cli
   ```
2. **Run the CLI config command**:
   ```bash
   oci setup config
   ```
3. You will be prompted for:
    - Your tenancy OCID
    - Your user OCID
    - Your compartment OCID
    - Your region (e.g., us-ashburn-1)
    - The path to your private key (a new key pair will be generated if not provided)
4. The CLI will generate your ~/.oci/config file and keys

For detailed setup instructions, refer to the [OCI CLI Config File Documentation](https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/cliinstall.htm#configfile).

### 📦 Setup Instructions

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/oci-resource-manager-gui.git
   cd oci-resource-manager-gui
   ```
2. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```
### 🖥️ Running the Application

1. Make sure your OCI config file is present at ~/.oci/config
2. Launch the app:
   ```bash
   streamlit run app.py
   ```
3. Open your browser to http://localhost:8501 and start managing your OCI resources visually.

# 🔐 Security Notes

- The application uses your local OCI credentials to authenticate; no credentials are stored or transmitted externally.
- SSH keys used during compute instance creation are generated and used locally and temporarily.
- You remain in full control — this app runs entirely on your machine.

🙌 **Contributing**

Contributions, suggestions, and improvements are welcome! Feel free to fork the repo and submit a pull request. For feature requests or issues, please open an issue ticket.

📄 **License**

This project is licensed under the **MIT License**.
