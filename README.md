# ☁️ OCI Resource Manager GUI

Your friendly neighborhood OCI management tool! Built with Python and Streamlit, this app makes managing your Oracle Cloud Infrastructure resources as easy as pie 🥧 (and much more fun than clicking through the console all day).

## ✨ Features

- 🌐 **Network Management**: Create and manage VCNs, Subnets, Security Lists, and more! It's like playing with digital LEGO blocks, but for cloud networking.
- 🖥️ **Compute Instance Launch**: Spin up new instances faster than you can say "cloud computing"!
- 🔄 **Instance Management**: Start, stop, and terminate instances with a click. No more hunting through menus!
- 🍀 **Autonomous Database**: Create and manage your smart databases with style.
- 🪣 **Object Storage**: Create and manage buckets, upload files, and organize your cloud storage like a pro! Perfect for storing everything from backups to cat photos.

## 🛠️ Prerequisites

Before you begin, ensure the following are in place:

- Python **3.8+**
- OCI CLI/SDK configuration (`~/.oci/config`)
- Valid OCI credentials with appropriate permissions

# 🔧 Setting Up Your OCI Config File

If you don’t already have a config file for the OCI CLI, follow these steps:

1. **Install the OCI CLI** (if not already installed):

   ```bash
   pip install oci-cli
   ```
   
3. **Run the CLI config command**:

   ```bash
   oci setup config
   ```
   
5. You will be prompted for:
    - Your tenancy OCID
    - Your user OCID
    - Your compartment OCID
    - Your region (e.g., us-ashburn-1)
    - The path to your private key (a new key pair will be generated if not provided)
6. The CLI will generate your ~/.oci/config file and keys

For detailed setup instructions, refer to the [OCI CLI Config File Documentation](https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/cliinstall.htm#configfile).

# 📦 Setup Instructions

1. **Clone the repository**:

   ```bash
   git clone https://github.com/mkowalik-git/oci-resource-manager-gui.git
   cd oci-resource-manager-gui
   ```
   
3. **Create and activate a virtual environment**:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
   
5. **Install the dependencies**:

   ```bash
   pip install -r requirements.txt
   ```
   
# 🎮 Running the Application

1. Make sure your OCI config file is properly set up at ~/.oci/config (no pressure, but this is important!)
2. Start the application (drumroll, please 🥁):
   
   ```bash
   streamlit run oci-gui-app.py
   ```
   
4. Open your browser and navigate to http://localhost:8501 (or whatever port Streamlit tells you)

# 🔒 Security Notes

- 🔐 All operations use your local OCI credentials (we're not storing anything, promise!)
- 🚫 No sensitive information is stored by the application (your secrets are safe with us)
- 🔑 SSH keys are only used temporarily during instance creation (like speed dating... for keys! They met, clicked, and then never saw each other again.)

# 🤝 Contributing

Found a bug? Want to add a feature? We'd love your help! Just:
1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

# 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

# 🙏 Acknowledgments

- Shoutout to Oracle Cloud Infrastructure for being awesome
- And you, for reading this far! You're the real MVP! 🏆 
