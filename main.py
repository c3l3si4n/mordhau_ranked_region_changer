import json
import os
import asyncio
from mitmproxy import options
from mitmproxy.tools import dump
import dns.resolver
import pyuac
import ctypes
from tkinter import simpledialog
from graceful_shutdown import ShutdownProtection
from graceful_shutdown import configure_shutdown_manager

dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
dns.resolver.default_resolver.nameservers = ['1.1.1.1']
MessageBox = ctypes.windll.user32.MessageBoxW

REGION = "South_America"
class ChangeRegion:
    def request(self, flow):
        # https://12d56.playfabapi.com/Match/CreateMatchmakingTicket?sdk=UE4MKPL-1.104.221107
        if "12d56.playfabapi.com" in flow.request.pretty_url.lower():
            flow.request.host = str(dns.resolver.query("12d56.playfabapi.com", 'A')[0])
            flow.request.headers["Host"] = "12d56.playfabapi.com"
        if "/Match/CreateMatchmakingTicket" in flow.request.pretty_url:
            originalBody = json.loads(flow.request.text)
            originalBody["Creator"]["Attributes"]["DataObject"]["Region"] = REGION
            originalBody["Creator"]["Attributes"]["DataObject"]["Pings"][0]["Region"] = "Brazil"
            originalBody["Creator"]["Attributes"]["DataObject"]["Pings"][0]["Latency"] = 10

            flow.request.text = json.dumps(originalBody)
            print(flow.request.text)


def add_hosts():
    with open("c:/Windows/System32/Drivers/etc/hosts", "a") as f:
        f.write("\n127.0.0.1 12D56.playfabapi.com")


def del_hosts():
    with open("c:/Windows/System32/Drivers/etc/hosts", "r") as f:
        hosts_file = [x.strip() for x in f.readlines()]
    new_hosts_file = ""
    for line in hosts_file:
        if not line.strip():
            continue
        if "12D56.playfabapi.com" in line:
            continue
        new_hosts_file += "\n" + line.strip()
    with open("c:/Windows/System32/Drivers/etc/hosts", "w") as f:
        f.seek(0)
        f.write(new_hosts_file)


async def start_proxy(host, port):
    opts = options.Options(listen_host=host, listen_port=port, ssl_insecure=True)
    os.system("""certutil -addstore "Root" %userprofile%"/.mitmproxy/mitmproxy-ca-cert.pem" """)
    master = dump.DumpMaster(
        opts,

    )
    master.addons.add(ChangeRegion())
    MessageBox(None, 'The ranked region changer is now running. You may now click OK, then open MORDHAU.' , 'MORDHAU: Ranked Region Changer', 0)

    print("""\n\n\n\n\n
==========================
Press Ctrl+C to gracefully shutdown the application.
==========================
""")
    await master.run()


    return master




if __name__ == '__main__':
    configure_shutdown_manager(before_hup=del_hosts, before_termination=del_hosts)

    add_hosts()
    if not pyuac.isUserAdmin():
        pyuac.runAsAdmin()
    with ShutdownProtection(1) as protected_block:
        try:
            asyncio.run(start_proxy("127.0.0.1", 443))
        except (SystemExit, KeyboardInterrupt) as e:
            print("Cleanly exiting...")
            del_hosts()
