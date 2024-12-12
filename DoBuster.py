import subprocess
import os
import argparse

# Add ASCII art banner at the start
def print_banner():
    banner = """
           _____   __  __     _____   _____ ____ _______ _____ __   __
     /\   / _ \ \ / /  \ \   / / _ \ / ____|___ |__   __|  __ \\ \ / /
    /  \ | | | \ V /     \ \_/ / | | | (___   __) | | |  | |__) |\ V / 
   / /\ \| | | |> |______\   /| | | |\___ \ |__ <  | |  |  _  /  > <  
  / ____ | |_| / . \      | | | |_| |____) |___) | | |  | | \ \ / . \ 
 /_/    \_\___/_/ \_\     |_|  \___/|_____/|____/  |_|  |_|  \_/_/ \_\
                                                                     
                                                                     
    """
    print("\033[1;32m" + banner + "\033[0m")

# Function to check and install tools if they are not installed
def check_and_install_tools():
    tools = ["subfinder", "assetfinder", "httpx", "curl"]
    for tool in tools:
        if not is_tool_installed(tool):
            print(f"{tool} is not installed. Installing...")
            install_tool(tool)

def is_tool_installed(tool):
    """Check if a tool is installed by trying to call it in the terminal."""
    try:
        subprocess.run([tool, "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return True
    except FileNotFoundError:
        return False

def install_tool(tool):
    """Attempt to install a tool using appropriate package managers."""
    try:
        if tool == "subfinder":
            subprocess.run(["go", "install", "github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest"], check=True)
        elif tool == "assetfinder":
            subprocess.run(["go", "install", "github.com/tomnomnom/assetfinder@latest"], check=True)
        elif tool == "httpx":
            subprocess.run(["go", "install", "github.com/projectdiscovery/httpx/cmd/httpx@latest"], check=True)
        elif tool == "curl":
            subprocess.run(["sudo", "apt-get", "install", "curl", "-y"], check=True)
    except subprocess.CalledProcessError:
        print(f"Failed to install {tool}. Please install it manually.")
        exit(1)

def run_subfinder(domains):
    """Run subfinder on a domain or a list of domains."""
    subdomains = []
    if isinstance(domains, list):  # If input is a list of domains
        print(f"Running subfinder on list of domains...")
        try:
            command = ["subfinder", "-dL", *domains]  # Using -dL for list of domains
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            if result.returncode == 0:
                subdomains = result.stdout.splitlines()
                print(f"subfinder results added to the list.")
            else:
                print(f"Error running subfinder on list of domains:")
                print(result.stderr)
        except FileNotFoundError:
            print("subfinder not found. Please ensure it is installed and added to PATH.")
    else:
        print(f"Running subfinder on domain: {domains}...")
        try:
            command = ["subfinder", "-d", domains]  # Using -d for single domain
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            if result.returncode == 0:
                subdomains = result.stdout.splitlines()
                print(f"subfinder results added to the list.")
            else:
                print(f"Error running subfinder on domain {domains}:")
                print(result.stderr)
        except FileNotFoundError:
            print("subfinder not found. Please ensure it is installed and added to PATH.")

    return subdomains

def run_assetfinder(domain):
    """Run assetfinder on a domain."""
    print(f"Running assetfinder on domain: {domain}...")
    try:
        command = ["assetfinder", "--subs-only", domain]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode == 0:
            return result.stdout.splitlines()
        else:
            print(f"Error running assetfinder on domain {domain}:")
            print(result.stderr)
            return []
    except FileNotFoundError:
        print("assetfinder not found. Please ensure it is installed and added to PATH.")
        return []

def run_httpx(subdomains_file, output_file, filter_200=False):
    """Run httpx on a list of subdomains with the requested flags."""
    print(f"Running httpx on file: {subdomains_file}...")
    try:
        # Define the command with or without the -f filter
        command = ["httpx", "-l", subdomains_file, "-sc", "-title", "-td"]
        if filter_200:
            command.append("-f")  # Add filter for status code 200

        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode == 0:
            with open(output_file, "w") as file:
                file.write(result.stdout)
            print(f"httpx results saved to: {output_file}")
            return result.stdout
        else:
            print(f"Error running httpx on file {subdomains_file}:")
            print(result.stderr)
            return None
    except FileNotFoundError:
        print("httpx not found. Please ensure it is installed and added to PATH.")
        return None

def save_to_file(filename, data):
    """Save data to a file after removing duplicates."""
    unique_data = sorted(set(data))  # Removing duplicates using set
    with open(filename, "w", encoding="utf-8") as file:
        file.write("\n".join(unique_data))
    print(f"Results saved to: {filename}")

def main():
    print_banner()  # Print the ASCII art banner when script starts

    check_and_install_tools()  # Check and install tools if not installed

    parser = argparse.ArgumentParser(description="Subdomain enumeration tool.")
    parser.add_argument("-d", "--domain", help="Enter a single domain (e.g. example.com)")
    parser.add_argument("-L", "--list", help="Provide a list of domains (filename)")
    parser.add_argument("-f", "--filter", action="store_true", help="Filter results to include only status code 200")
    parser.add_argument("-c", "--crt", action="store_true", help="Run crt.sh on the given domain (only works for single domains)")

    args = parser.parse_args()

    # Determine if we are working with a single domain or a list
    if args.list:
        domain_list_file = args.list
        with open(domain_list_file, "r") as file:
            domain_list = file.read().splitlines()

        subdomains = []
        for domain in domain_list:
            subdomains.extend(run_subfinder(domain))  # Collect subdomains from subfinder
            subdomains.extend(run_assetfinder(domain))  # Collect subdomains from assetfinder

        # Remove duplicates and save to file
        subdomains = sorted(set(subdomains))  # Removing duplicates using set
        save_to_file("allSub.txt", subdomains)

        # Run httpx with filtering
        run_httpx("allSub.txt", "httpx_results.txt", filter_200=args.filter)
    elif args.domain:
        domain = args.domain
        subdomains = []
        subdomains.extend(run_subfinder(domain))  # Collect subdomains from subfinder
        subdomains.extend(run_assetfinder(domain))  # Collect subdomains from assetfinder

        # Remove duplicates and save to file
        subdomains = sorted(set(subdomains))  # Removing duplicates using set
        save_to_file("allSub.txt", subdomains)

        # Run httpx with filtering
        run_httpx("allSub.txt", "httpx_results.txt", filter_200=args.filter)

if __name__ == "__main__":
    main()
