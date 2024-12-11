import subprocess
import os
import argparse

# Add ASCII art banner at the start
def print_banner():
    banner = """
           _____   __  __     _____   _____ ____ _______ _____ __   __
     /\   / _ \ \ / /  \ \   / / _ \ / ____|___ |__   __|  __ \\ \ / /
    /  \ | | | \ V _____\ \_/ | | | | (___   __) | | |  | |__) |\ V /
   / /\ \| | | |> |______\   /| | | |\___ \ |__ <  | |  |  _  /  > <
  / ____ | |_| / . \      | | | |_| |____) |___) | | |  | | \ \ / . \
 /_/    \_\___/_/ \_\     |_|  \___/|_____/|____/  |_|  |_|  \_/_/ \_\\
    """
    print("\033[1;32m" + banner + "\033[0m")

def run_subfinder(domains, output_file):
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

def run_crt_sh(domain):
    """Run crt.sh to check for certificates related to the domain."""
    print(f"Running crt.sh for domain: {domain}...")
    try:
        command = ["curl", "-s", f"https://crt.sh/?q={domain}&output=json"]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode == 0:
            crt_data = result.stdout
            if crt_data:
                with open(f"{domain}_crt_results.json", "w") as file:
                    file.write(crt_data)
                print(f"CRT results saved to {domain}_crt_results.json")
            else:
                print("No certificate data found for this domain.")
        else:
            print(f"Error running crt.sh for domain {domain}:")
            print(result.stderr)

    except FileNotFoundError:
        print("curl not found. Please ensure it is installed and added to PATH.")

def run_dnsrecon(domain):
    """Run dnsrecon on a domain."""
    print(f"Running dnsrecon for domain: {domain}...")
    try:
        command = ["dnsrecon", "-d", domain]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode == 0:
            dns_data = result.stdout
            if dns_data:
                with open(f"{domain}_dnsrecon_results.txt", "w") as file:
                    file.write(dns_data)
                print(f"Dnsrecon results saved to {domain}_dnsrecon_results.txt")
            else:
                print("No DNS data found for this domain.")
        else:
            print(f"Error running dnsrecon for domain {domain}:")
            print(result.stderr)

    except FileNotFoundError:
        print("dnsrecon not found. Please ensure it is installed and added to PATH.")

def save_to_file(filename, data):
    """Save data to a file after removing duplicates."""
    unique_data = sorted(set(data))  # Removing duplicates using set
    with open(filename, "w", encoding="utf-8") as file:
        file.write("\n".join(unique_data))
    print(f"Results saved to: {filename}")

def main():
    print_banner()  # Print the ASCII art banner when script starts

    parser = argparse.ArgumentParser(description="Subdomain enumeration tool.")
    parser.add_argument("-d", "--domain", help="Enter a single domain (e.g. example.com)")
    parser.add_argument("-L", "--list", help="Provide a list of domains (filename)")
    parser.add_argument("-f", "--filter", action="store_true", help="Filter results to include only status code 200")
    parser.add_argument("-c", "--crt", action="store_true", help="Run crt.sh on the given domain (only works for single domains)")
    parser.add_argument("-r", "--dnsrecon", action="store_true", help="Run dnsrecon on the given domain (only works for single domains)")

    args = parser.parse_args()

    # Determine if we are working with a single domain or a list
    if args.list:
        domain_list_file = args.list
        with open(domain_list_file, "r") as file:
            domain_list = file.read().splitlines()

        subdomains = []
        for domain in domain_list:
            subdomains.extend(run_subfinder(domain, None))  # Collect subdomains from subfinder
            subdomains.extend(run_assetfinder(domain))  # Collect subdomains from assetfinder

        # Remove duplicates and save the combined results
        save_to_file("all_subdomains.txt", subdomains)

    elif args.domain:
        domain = args.domain

        subdomains = []
        subdomains.extend(run_subfinder(domain, None))
        subdomains.extend(run_assetfinder(domain))

        # Remove duplicates and save the combined results
        save_to_file("all_subdomains.txt", subdomains)

        # Run dnsrecon if specified
        if args.dnsrecon:
            run_dnsrecon(domain)

        # Run crt.sh if specified
        if args.crt:
            run_crt_sh(domain)

    # Run httpx on the combined results
    httpx_output_file = "httpx_results.txt"
    httpx_output = run_httpx("all_subdomains.txt", httpx_output_file, filter_200=args.filter)

    # If filter_200 is True, save the filtered results as alive200.txt
    if args.filter and httpx_output:
        with open("alive200.txt", "w") as file:
            file.write(httpx_output)
        print("Filtered results with HTTP 200 saved to alive200.txt")

if __name__ == "__main__":
    main()