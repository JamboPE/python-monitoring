import subprocess
import os
import datetime
import socket

# Bash stuff

def run_bash_command(command):
    return subprocess.check_output(command, shell=True)

def bash_to_string(command):
    return str(command).replace("b'","").replace("'","")[:-2]

# Check Satistics

def mem_check(return_type):
    # Returns RAM: %usage, free, total
    mem_info = bash_to_string(run_bash_command("cat /proc/meminfo | grep -E 'MemTotal|MemFree' | awk '{print $2}'")).split("\\n")
    mem_total = round(int(mem_info[0])*0.0009765625*0.0009765625,1)
    mem_free = round(int(mem_info[1])*0.0009765625*0.0009765625,1)
    mem_percent = (mem_free/mem_total)*100
    if return_type == "basic":
        return str(round(mem_percent,1))
    else:
        return "RAM: " + str(round(mem_percent,1))+"%" + " " + str(mem_free)+"GB" + "/" + str(mem_total)+"GB"

def cpu_check(time_avg,return_type):
    # time_avg can be 1, 5, or 15 (in minutes)
    # Returns CPU: %usage, temp
    if time_avg == 1:
        avg = "1"
    elif time_avg == 5:
        avg = "2"
    elif time_avg == 15:
        avg = "3"
    else:
        avg = "1"
    cpu_load = bash_to_string(run_bash_command("cat /proc/loadavg | awk '{print $"+avg+"}'"))
    cpus = bash_to_string(run_bash_command("lscpu | grep 'CPU(s):' | grep -v 'NUMA' | awk '{print $2}'"))
    cpu_temp = str(round(int(bash_to_string(run_bash_command("cat /sys/class/thermal/thermal_zone0/temp")))/1000,1))+"degC"
    cpu_usage = str(round(float(cpu_load)/float(cpus)*100,1))+"%"
    if return_type == "basic":
        return [cpu_usage,cpu_temp]
    else:
        return "CPU: " + cpu_usage +" "+ cpu_temp

def disk_check(disk,return_type):
    # Returns DISK: %usage, free, total
    def get_disk_info(awk_no):
        return bash_to_string(run_bash_command("df -h '"+disk+"' | grep '/' | awk '{print $"+str(awk_no)+"}'"))
    disk_device = str(get_disk_info(1))
    disk_mount = str(get_disk_info(6))
    disk_avail = str(get_disk_info(4))
    disk_used = str(get_disk_info(3))
    disk_size = str(get_disk_info(2))
    disk_percent = str(get_disk_info(5))
    if return_type == "basic":
        return disk_percent[:-1]
    else:
        return "DISK: " + disk_device +" MOUNT:'"+ disk_mount +"' | "+ disk_percent +" "+ disk_avail + "B/" + disk_size+"B"

def network_check(interface):
    # Returns NET: %usage, rx, tx
    def get_net_info(awk_no):
        return bash_to_string(run_bash_command("cat /proc/net/dev | grep '"+interface+"' | awk '{print $"+str(awk_no)+"}'")).replace("\\n","")
    net_rx = get_net_info(2)
    net_tx = get_net_info(10)
    return "NET: rx " + str(round(float(net_rx)*9.3132257461548E-10,2)) +"GB | tx "+ str(round((float(net_tx)*9.3132257461548E-10),2)) +"GB"

def dns_check():
    # Returns DNS: %usage, ping
    dns_ping = bash_to_string(run_bash_command("ping -c 1 google.co.uk")).split('\\n')[4].split(',')[2]
    return "DNS: " + dns_ping + " to google.co.uk"

def swap_check(return_type):
    # Returns SWAP: %usage, free, total
    swap_info = str(bash_to_string(run_bash_command("cat /proc/swaps | grep 'swapfile' | awk '{print $3,$4}'")).replace("\\t"," ")).split(" ")
    swap_total = round(int(swap_info[0])*0.0009765625*0.0009765625,1)
    swap_free = round(int(swap_info[1])*0.0009765625*0.0009765625,1)
    swap_percent = (swap_free/swap_total)*100
    if return_type == "basic":
        return str(round(swap_percent,1))
    else:
        return "SWAP: " + str(round(swap_percent,1))+"%" + " " + str(swap_free)+"GB" + "/" + str(swap_total)+"GB"

def service_check(service,return_type):
    # Returns SERVICE: (active/inactive) (enabled/disabled)
    try:
        service_active_status = bash_to_string(run_bash_command("systemctl is-active "+service))
    except:
        service_active_status = "inactive"
    try:
        service_enabled_status = bash_to_string(run_bash_command("systemctl is-enabled "+service))
    except:
        service_enabled_status = "disabled"
    if return_type == "basic":
        return [service_active_status,service_enabled_status]
    return "SERVICE ("+service+"): Active? " + service_active_status + " | Enabled? " + service_enabled_status

# Other

def rw_file(rw,line_no,data,filename):
    if rw == "r":
        file = open(filename,rw)
        i = 1
        for line in file:
            if i == line_no:
                return line[0]
            elif i > 7:
                return "Error: Line number too high"
            i += 1
        file.close()
        return "Done"
    elif rw == "w":
        file_content = ""
        i = 1
        file = open(filename,"r")
        for line in file:
            if i == line_no:
                file_content += data+"\n"
            elif i == 8:
                file_content += "#mem,cpu,cpu_temp,disk,swap,service_active,service_enabled"
            else:
                file_content += line[0]+"\n"
            i += 1
        file.close()
        file = open(filename,"w")
        file.write(file_content)
        file.close()

def discord_webhook(bash_script,title,host,infomation_title,infomation,status,discord_webhook_url):
    if status == "up":
        status = "✅"
    elif status == "critical":
        status = "❗"
    else:
        status = "❌"
    title = status+" "+title+" "+status
    text="**Host**\\n"+host+"\\n\\n**"+infomation_title+"**\\n"+infomation+"\\n\\n**Time**\\n"+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    subprocess.check_output(bash_script+" '"+title+"' '"+text+"' '"+discord_webhook_url+"'", shell=True)

def kuma_push(push_url,ping,status):
    #status can be up, down, or critical
    if status == "up":
        subprocess.check_output("curl "+push_url+"ping="+ping, shell=True)
    else:
        subprocess.check_output("curl "+push_url+"status=down", shell=True)

if __name__ == "__main__":
    bash_script = "/bin/bash "+str(os.path.dirname(os.path.abspath(__file__)))+"/discord_webhook.sh"
    filename = str(os.path.dirname(os.path.abspath(__file__)))+"/prev_states"
    
    #Change these
    discord_webhook_url = #https://discord.com/api/webhooks/"
    hostname = socket.gethostname()
    # Kuma push URLs
    mem_push_url = #"https://uptime.kuma.com/api/push/key?&" #ping=num #status=up #message=OK
    cpu_push_url = #"https://uptime.kuma.com/api/push/key?&" #ping=num #status=up #message=OK
    cpu_temp_push_url = #"https://uptime.kuma.com/api/push/key?&" #ping=num #status=up #message=OK
    disk_push_url = #"https://uptime.kuma.com/api/push/key?&" #ping=num #status=up #message=OK
    swap_push_url = #"https://uptime.kuma.com/api/push/key?&" #ping=num #status=up #message=OK
    service_push_url = #"https://uptime.kuma.com/api/push/key?&" #ping=num #status=up #message=OK

    # Thresholds
    mem_threshold = 80
    cpu_threshold = 80
    cpu_temp_threshold = 70
    disk_threshold = 90
    swap_threshold = 70
    service1 = "docker"
    disk1 = "/"
    
    # Check memory
    mem = mem_check("basic")
    if float(mem) > mem_threshold:
        kuma_push(mem_push_url,mem,"down")
        if rw_file("r",1,"dummy",filename) != "0":
            rw_file("w",1,"0",filename)
            discord_webhook(bash_script,"RAM Usage Above "+str(mem_threshold)+"%",hostname,"RAM Usage",mem+"%","critical",discord_webhook_url)
    else:
        kuma_push(mem_push_url,mem,"up")
        if rw_file("r",1,"dummy",filename) != "1":
            rw_file("w",1,"1",filename)
            discord_webhook(bash_script,"RAM Usage Below "+str(mem_threshold)+"%",hostname,"RAM Usage",mem+"%","up",discord_webhook_url)

    # Check cpu load
    cpu = cpu_check(1,"basic")[0][:-1]
    if float(cpu) > cpu_threshold:
        kuma_push(cpu_push_url,cpu,"down")
        if rw_file("r",2,"dummy",filename) != "0":
            rw_file("w",2,"0",filename)
            discord_webhook(bash_script,"CPU Load Above "+str(cpu_threshold)+"%",hostname,"CPU Load",cpu+"%","critical",discord_webhook_url)
    else:
        kuma_push(cpu_push_url,cpu,"up")
        if rw_file("r",2,"dummy",filename) != "1":
            rw_file("w",2,"1",filename)
            discord_webhook(bash_script,"CPU Load Below "+str(cpu_threshold)+"%",hostname,"CPU Load",cpu+"%","up",discord_webhook_url)
    
    # Check cpu temp
    cpu_temp = cpu_check(1,"basic")[1][:-4]
    if float(cpu) > cpu_temp_threshold:
        kuma_push(cpu_temp_push_url,cpu_temp,"down")
        if rw_file("r",3,"dummy",filename) != "0":
            rw_file("w",3,"0",filename)
            discord_webhook(bash_script,"CPU Temp Above "+str(cpu_temp_threshold)+"%",hostname,"CPU Temp",cpu_temp+"°C","critical",discord_webhook_url)
    else:
        kuma_push(cpu_temp_push_url,cpu_temp,"up")
        if rw_file("r",3,"dummy",filename) != "1":
            rw_file("w",3,"1",filename)
            discord_webhook(bash_script,"CPU Temp Below "+str(cpu_temp_threshold)+"%",hostname,"CPU Temp",cpu_temp+"°C","up",discord_webhook_url)

    # Check / disk
    disk = disk_check(disk1,"basic")
    if float(disk) > disk_threshold:
        kuma_push(disk_push_url,disk,"down")
        if rw_file("r",4,"dummy",filename) != "0":
            rw_file("w",4,"0",filename)
            discord_webhook(bash_script,"Disk Space Usage Above "+str(disk_threshold)+"%",hostname,"Disk Space Usage",disk+"%","critical",discord_webhook_url)
    else:
        kuma_push(disk_push_url,disk,"up")
        if rw_file("r",4,"dummy",filename) != "1":
            rw_file("w",4,"1",filename)
            discord_webhook(bash_script,"Disk Space Usage Below "+str(disk_threshold)+"%",hostname,"Disk Space Usage",disk+"%","up",discord_webhook_url)

    # Check swap
    swap = swap_check("basic")
    if float(swap) > swap_threshold:
        kuma_push(swap_push_url,swap,"down")
        if rw_file("r",5,"dummy",filename) != "0":
            rw_file("w",5,"0",filename)
            discord_webhook(bash_script,"Swap Usage Above "+str(swap_threshold)+"%",hostname,"Swap Usage",swap+"%","critical",discord_webhook_url)
    else:
        kuma_push(swap_push_url,disk,"up")
        if rw_file("r",5,"dummy",filename) != "1":
            rw_file("w",5,"1",filename)
            discord_webhook(bash_script,"Swap Usage Below "+str(swap_threshold)+"%",hostname,"Swap Usage",swap+"%","up",discord_webhook_url)

    # Check service
    service_active = service_check(service1,"basic")[0]
    service_enabled = service_check(service1,"basic")[1]

    if service_active == "inactive" or service_enabled == "disabled":
        kuma_push(service_push_url,"0","down")
        if rw_file("r",6,"dummy",filename) != "0":
            rw_file("w",6,"0",filename)
            if service_enabled == "disabled" and service_active == "inactive":
                discord_webhook(bash_script,"Service '"+service+"' Inactive & Disabled",hostname,"Service",service+"\\n\\n**Service Status**\\n"+service_active+" ❌\\n"+service_enabled+" ❗","down",discord_webhook_url)
            elif service_active == "inactive":
                discord_webhook(bash_script,"Service '"+service+"' Inactive",hostname,"Service",service+"\\n\\n**Service Status**\\n"+service_active+" ❌\\n"+service_enabled+" ✅","down",discord_webhook_url)
            elif service_enabled == "disabled":
                discord_webhook(bash_script,"Service '"+service+"' Disabled",hostname,"Service",service+"\\n\\n**Service Status**\\n"+service_active+" ✅\\n"+service_enabled+" ❗","critical",discord_webhook_url)            
    else:
        kuma_push(service_push_url,"0","up")
        if rw_file("r",6,"dummy",filename) != "1":
            rw_file("w",6,"1",filename)
            discord_webhook(bash_script,"Service '"+service+"' Active & Enabled",hostname,"Service",service+"\\n\\n**Service Status**\\n"+service_active+" ✅\\n"+service_enabled+" ✅","up",discord_webhook_url)

    ##print(network_check("wlp5s0"))
    ##print(dns_check())