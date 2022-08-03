#!/usr/bin/python3

from sys import platform
if platform == "linux" or platform == "linux2":
    import distro
    if distro.id() != 'kali':
        print('[!] This code will only work on Kali Linux')
        quit()
else:
    print('[!] This code will only work on Kali Linux')
    quit()


#Import required modules
import subprocess, requests, re, sys
import operator
import apt, os
import threading
from shutil import copyfile

#Check if user is root first.
if os.getuid() != 0:
    print('[!] Please run with sudo')
    quit()


#Def Show Banner
import pyfiglet
ascii_banner = pyfiglet.figlet_format("Apt Update Fixer")
print(ascii_banner)
print('                      Fix Kali Linux slow apt update')
print('                     Find all the available Repo list')
print('                  Check latency and find out best mirror\n')
print('                     Script written by Hrishikesh7665')
print('                       NB: ONLY WORK FOR KALI LINUX\n')

#Try to install apt-transport-https
cache = apt.Cache()
cache.open()
package = "apt-transport-https"
print("[*] Checking if '" + package + "' package is installed.")
try:
    if cache[package].is_installed:
        print('[+] '+package+" is installed\n")
    else:
        print("[-] "+package+" is NOT installed.\n[*]Attempting to install ...")
        cache[package].mark_install()
        print("[+] Installing "+package+"\n")
        try:
            cache.commit()
            print("\n[+] "+package+" installed successfully")
        except Exception as e:
            print("[!] package "+package+" is failing to install")
            print("\n[Debug Info:]\n"+str(e))
except KeyError as e:
    print("[!] The package \"" + package + "\" could not found in local apt cache. You may need to install it manually later after you've done update kali.")
    quit()


result_url = []
ping_result = []
mirrors = {}
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36'}


def ask(a):
    print('[?] '+str(a)+" (y/n) : ", end="")
    f = ''
    while True:
        x = input('')
        if x != '':
            if x.lower() == 'yes' or x.lower() == 'y':
                f = True
                break
            elif x.lower() == 'no' or x.lower() == 'n':
                f = False
                break
            else:
                print('Invalid Input\n')
                print(str(a)+" : ", end="")
                continue
        else:
            print('Please give an answer\n')
            print(str(a)+" : ", end="")
    return f

class fetch_thread(threading.Thread):
    def __init__(self, count, url,schema):
        threading.Thread.__init__(self)
        self.count = count + 1
        self.url = url
        self.schema = schema
    def run(self):
        try:
            response = requests.get(self.schema+self.url, headers=headers).status_code
            if response == 200:
                result_url.append(self.url)
            else:
                print("[!] " + self.url + " doesn't support " + self.schema)
        except Exception as e:
            print("\n[!] Failed to establish a connection to host " + self.schema + self.url)

def fetch_url(urls,schema):
    threads = []
    for count, url in enumerate(urls):
        count = fetch_thread(count, url,schema)
        threads.append(count)
    for i in threads:
        i.start()
    for i in threads:
        i.join()
    return result_url

class ping_thread(threading.Thread):
    def __init__(self, count, hostname):
        super(ping_thread, self).__init__()
        self.count = count + 1
        self.hostname = hostname
    def run(self):
        p = subprocess.Popen(['ping','-c 3', self.hostname], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        p = [str(x.decode('utf-8')) for x in p]
        if not p[0].strip():
            print("[!] Error: Something went wrong ...")
            print(p[1].strip())
            response = ask("Stuck at finding mirror latency. Do you want to retry[y] or skip[n]?",'n')
            if response:
                run(self.hostname)
        else:
            try:
                if "100% packet loss" in p[0].strip():
                    average = "[!] Drop requests (ICMP)"
                else:
                    average = p[0].strip().splitlines()[-1].split('=')[1].split('/')[1]
                    mirrors[self.hostname] = str(str(average).zfill(7))
            except Exception as e:
                if not ask("[!] Something went wrong. would you like to try again [y] or [n].",'y'):
                    print('[!] Shutting down the script for now')
                    sys.exit(1)
            print("{0:30} : {1}".format(self.hostname,average))

def ping_s(hostname):
    threads = []
    for count, hostname in enumerate(hostname):
        count = ping_thread(count, hostname)
        threads.append(count)
    for i in threads:
        i.start()
    for i in threads:
        i.join()
    return ping_result



#Function to make backup of current source list
def make_backup():
    print("\n[*] Making a backup file ....")
    if os.path.exists('/etc/apt/sources.list.bk'):
        print('[-] A source list backup file already exist it will be replaced\n')
        var = input('Hit enter to proceed.....')
        if var == '':
            print('[-] Old source list backup file is deleted')
            copyfile('/etc/apt/sources.list', '/etc/apt/sources.list.bk')
            print("\n[+] Backed-up source list /etc/apt/sources.list.bk\n")
            return True
        else:
            print('[!] Shutting down the script for now')
            return False
    else:
        copyfile('/etc/apt/sources.list', '/etc/apt/sources.list.bk')
        print("\n[+] Backed-up source list /etc/apt/sources.list.bk\n")
        return True

def update_source_list(mode,n):
    print("[*] Checking sources.list for older entries ...")
    contents = []
    file = open("/etc/apt/sources.list", "r+")
    print("[-] Commenting older entries ...")
    i = ''
    for line in file.readlines():
            if (re.search(r'^deb http(?:s|)://http\.kali\.org/kali', line, re.I)) or (re.search(r'^deb-src http(?:s|)://http\.kali\.org/kali', line, re.I)):
                newline = "#" + line
                file.write(newline)
                contents.append(newline)
            elif re.search(r'^# Autogenerated by KaliSlowUpdateFixer script; Script Author Hrishikesh7665', line, re.I):
                print("[*] Found previous applies! Commenting it out ...")
                contents.append(line)
                i = 1
            elif i == 1:
                if not line.startswith("#"):
                    newline = "#" + line
                    file.write(newline)
                    contents.append(newline)
                else:
                    contents.append(line)
                i = i+1
            elif i == 2:
                if not line.startswith("#"):
                    newline = "#" + line
                    file.write(newline)
                    contents.append(newline)
                else:
                    contents.append(line)
                i = 0
            else:
                contents.append(line)
    file.seek(0)
    file.truncate()
    file.seek(0)
    for line in contents:
        file.write(line)
    file.close()
    print("[+] Done\n")
    print("[+] Updating sources.list with new entry ...")
    if mode=='checked':
        matching = [s for s in urls if sorted_mirrors[0][0] in s]
        new_mirror = schema + matching[0]
        print("[!] Your new mirror: " + new_mirror + "\n")
    elif mode=='unchecked':
        #print(urls[n])
        new_mirror = 'https' + urls[n-1]
        print("[!] Your new mirror: " + new_mirror + "\n")



    temp = "sh -c \'echo \"\n# Autogenerated by KaliSlowUpdateFixer script; Script Author Hrishikesh7665\" >> /etc/apt/sources.list\'"
    subprocess.Popen(temp, shell=True, stdout=subprocess.PIPE).stdout.read()

    line = "deb " + new_mirror + " kali-rolling main contrib non-free"
    temp = "sh -c \'echo %s >> /etc/apt/sources.list\'"
    subprocess.Popen(temp % line, shell=True, stdout=subprocess.PIPE).stdout.read()

    line = "deb-src " + new_mirror + " kali-rolling main contrib non-free"
    ans = (ask("Do want to 'add deb-src' ?"))
    if ans == False:
        line = "#" + line
    temp = "sh -c \'echo \"%s\" >> /etc/apt/sources.list\'"
    subprocess.Popen(temp % line, shell=True, stdout=subprocess.PIPE).stdout.read()
    print("[+] Done!")
    print("\n[++]Run 'sudo apt clean && sudo apt update' for the changes to load.\n")

#Try to getting mirror list
print("[*] Getting mirror list ...")
try:
    response = requests.get('https://http.kali.org/README.mirrorlist', headers=headers).text
    urls = re.findall(r'(?:href="http(?:s|))(.*)(?:/README")',response)[2:]
    print("\n[+] Found (" + str(len(urls)) + ") lists of mirrors:\n")
    i = 1
    for url in urls:
        print("["+str('%02d' % i)+"] https" + url)
        i = i+1
    print('')
except Exception as e:
    print("[!] Fetching mirror-list failed, check your internet connection\n\n[Debug Info:]\n"+str(e)+'\n')
    print('[!] Shutting down the script for now')
    quit()


#ask user for ping check
ans = (ask('Do want to check latency ?'))
if ans == True:
    #ping and latency check
    print("\n[*] Checking for Fastest Mirror\n")
    schema = 'https'
    new_urls = fetch_url(urls,schema)
    hosts = []
    for hostname in new_urls:
        hostname = hostname.split("//")[-1].split("/")[0].split('?')[0]
        hosts.append(hostname)
    if len(hosts) == 0:
        print('\n[!] No host found, Shutting down the script for now')
        print('[!] Retry after some times')
        quit()

    ping_s(hosts)
    # sorted to fastest mirror
    sorted_mirrors = sorted(mirrors.items(), key=operator.itemgetter(1))
    print("\n[+] Fastest mirror: " + str(sorted_mirrors[0]))
    make_backup()
    update_source_list('checked',0)
else:
    print('\n[-] Skipping latency check\n\n[?]Please enter a number from discoverd mirror lists')
    while True:
        user_input=input('Enter a mirror number : ')
        try:
            user_input = int(user_input)
            if user_input <= len(urls):
                flag = make_backup()
                if flag == False:
                    quit()
                else:
                    update_source_list('unchecked',user_input)
                    flag = False
                    quit()
                break
            else:
                print('Invalid Input\n')
                continue
        except:
            if flag==False:
                break
            else:
                print('Invalid Input\n')
                continue