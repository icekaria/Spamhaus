import subprocess
import re
import ipaddress
import dns.resolver
import threading

# Regular expression pattern to match an IPv4 address
ipv4_pattern = r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"

# Function to check if an IP address is listed in Spamhaus
def check_ip_in_spamhaus(ip):
    # Construct the reverse DNS lookup query for the Spamhaus PBL list
    query = ".".join(reversed(ip.split("."))) + ".zen.spamhaus.org"

    try:
        # Perform the DNS query
        response = dns.resolver.resolve(query, 'A')
        
        # If the response contains any IP address, the IP is listed in Spamhaus
        for rdata in response:
            return True
    except dns.resolver.NXDOMAIN:
        # If the domain does not exist, the IP is not listed
        return False
    except dns.resolver.Timeout:
        # Handle DNS query timeout
        print("DNS query timed out")
    except dns.resolver.NoNameservers:
        # Handle no nameservers available to answer the query
        print("No nameservers available")
    except Exception as e:
        # Handle other exceptions
        print("An error occurred:", e)
    
    return False

# Run the netstat command and capture its output
netstat_output = subprocess.run(["netstat", "-ano"], capture_output=True, text=True).stdout

# Split the output into lines
lines = netstat_output.splitlines()

# Create a list to store IP addresses
ip_addresses = []

# Iterate over each line in the output
for line in lines:
    # Use regular expression to find all IPv4 addresses in the line
    ips_in_line = re.findall(ipv4_pattern, line)

    # Iterate over found IP addresses
    for ip in ips_in_line:
        # Check if the IP address is not in the local range, not 0.0.0.0
        if not ipaddress.ip_address(ip).is_private and ip != "0.0.0.0":
            ip_addresses.append(ip)

# Function to check IP addresses in Spamhaus using threading
def check_ip_thread(ip, lock):
    with lock:
        if check_ip_in_spamhaus(ip):
            print(f"{ip}: Listed in Spamhaus")
        else:
            print(f"{ip}: Not listed in Spamhaus")

# Create a lock for synchronizing access to standard output
lock = threading.Lock()

# Create and start threads for each IP address
threads = []
for ip in ip_addresses:
    thread = threading.Thread(target=check_ip_thread, args=(ip, lock))
    thread.start()
    threads.append(thread)

# Wait for all threads to finish
for thread in threads:
    thread.join()
