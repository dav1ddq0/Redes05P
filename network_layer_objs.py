

class Packet:
    def __init__(self, mac_ori , ori_ip, des_ip, data, ):
        self.ori_ip = ori_ip
        self.des_ip = des_ip
        self.data = data
        self.mac_ori = mac_ori
        self.mac_des = None

class Route:
    def __init__(self, destination:str, mask:str, gateway:str, interface: int) -> None:
        self.destination = destination
        self.mask = mask
        self.gateway = gateway
        self.interface =interface

class Interface:
    def __init__(self):
        self.ip = None
        self.mask = None
        self.mac = None
        self.packets= []
        self.frames =[]

    
    def setup_ip(self, ip, mask):
        self.ip = ip
        self.mask = mask
    
    def setup_mac(self, mac):
        self.mac = mac

