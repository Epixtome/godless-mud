import socket

def is_port_open(port):
    for host in ["127.0.0.1", "::1"]:
        try:
            with socket.socket(socket.AF_INET if host == "127.0.0.1" else socket.AF_INET6, socket.SOCK_STREAM) as s:
                s.settimeout(1.0) # Longer timeout
                res = s.connect_ex((host, port))
                print(f"Check {host}:{port} -> {res}")
                if res == 0:
                    return True
        except Exception as e:
            print(f"Check {host}:{port} -> Error: {e}")
            continue
    return False

print(f"Final: {is_port_open(3000)}")
