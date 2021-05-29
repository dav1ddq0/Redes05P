import queue

class Packet:
    def __init__(self, ip_connect, mac_ori, ori_ip, des_ip, data, protocol=0, ttl=0):
        self.ori_ip = ori_ip
        self.des_ip = des_ip
        self.data = data
        self.mac_ori = mac_ori
        self.mac_des = None
        self.ip_connect =ip_connect
        self.protocol = protocol
        self.ttl = ttl 

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
        self.sframe_pending = queue.Queue()
        # receive frame that is being put together
        self.rframe = ""
        # sending frame 
        self.sframe = ""
        self.bit_sending = None
        self.transmitting_time = 0
        self.transmitting = False
        self.stopped = False
        self.stopped_time = 0
        self.failed_attempts = 0
        
    
    def next_bit(self):
        n = len(self.sframe)
        if n > 0:
            next = self.sframe[0]
            self.sframe = self.sframe[1:]
            return next

        if self.sframe_pending.qsize() > 0:
            self.sframe = self.sframe_pending.get()
            return self.next_bit()    

        return None
    
    def setup_ip(self, ip, mask):
        self.ip = ip
        self.mask = mask
    
    def setup_mac(self, mac):
        self.mac = mac

    def add_frame(self, frame):
        if self.sframe == "":
            self.sframe = frame
        else:
            self.sframe_pending.put(frame)
    
    def add_packet(self, packet):
        self.packets.append(packet)
    
    def remove_packet(self, packet):
        self.packets.remove(packet)
    
