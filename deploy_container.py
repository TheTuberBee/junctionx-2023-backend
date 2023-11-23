import os
import sys
import hashlib
import dotenv

dotenv.load_dotenv("/usr/local/share/junctionx/.env")

def get_port(branch: str):
    return int.from_bytes(hashlib.sha256(branch.encode()).digest(), signed=False) % 50000 + 10000

branches = []
with open("/etc/nginx/branches", "r") as file:
    for branch in file.read().split("\n"):
        if branch != "":
            branches.append(branch)

new = sys.argv[1]
new_port = get_port(new)

if new not in branches:
    branches.append(new)

print(branches)

config = ""

os.system(f"docker stop junctionx_{new}")
os.system(f"docker rm junctionx_{new}")

os.system(f"docker build -t junctionx .")
os.system("""
    docker run -d -p %s:7000 --name junctionx_%s 
    -e DB_HOST=%s
    -e DB_PORT=%s
    -e DB_USER=%s
    -e DB_PASSWORD=%s
    -e DB_DATABASE=%s
    junctionx
""" % (
    new_port, 
    new, 
    os.environ["DB_HOST"], 
    os.environ["DB_PORT"], 
    os.environ["DB_USER"], 
    os.environ["DB_PASSWORD"], 
    os.environ["DB_DATABASE"]
))

for branch in branches:
    port = get_port(branch)

    config += ("""
        location ~ ^/junctionx/%s/(.*)$ {
            rewrite ^/junctionx/%s/(.*) /$1 break;
            proxy_pass http://127.0.0.1:%s;
        }
    """ % (branch, branch, port))

with open("/etc/nginx/nginx.conf", "w") as file:

    with open("/etc/nginx/nginx.conf.begin", "r") as begin:
        file.write(begin.read())

    file.write(config)

    with open("/etc/nginx/nginx.conf.end", "r") as end:
        file.write(end.read())

os.system("sudo /usr/sbin/nginx -s reload")

with open("/etc/nginx/branches", "w") as file:
    for branch in branches:
        file.write(branch + "\n")
