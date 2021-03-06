from enum import Enum
import queue
import random
import errors_algs
import network_layer_utils as netl
import network_layer_objs as neto
import link_layer_utils as linkl
handler = None
class Data(Enum):
    Null = "Null"
    One = "1"
    Zero = "0"



class Cable:
    def __init__(self):
        # conozco la informacion qu esta pasando por el cable
        self.data = Data.Null  # 0 1 Null son los tres estados en los que puede estar el cable

class CableDuplex:
    def __init__(self) -> None:
        # un cable duplex se representaria como dos cables normales 
        self.cableA = Cable()  
        self.cableB = Cable() 

class Port:
    def __init__(self, name: str, device) -> None:
        # nombre del puerto
        self.name = name
        # con esta propiedad conozco si un cable conectado al puerto
        self.cable = None
        self.read_channel = None
        self.write_channel = None
        # un puerto sabe de que dispositvo es
        self.device = device
        # un puerto conoce con que puerto esta conectado
        self.next = None

class Router:
    def __init__(self, name:str, ports_amount:int)->None:
        self.name = name
        self.ports= []
        # port:interface{ip,mask}
        self.interfaces={}
        for i in range(ports_amount):
            portname = f"{name}_{i + 1}"
            port = Port(portname, self)
            self.ports.append(port)
            self.interfaces[portname] = neto.Interface()
        
        # tabla de rutas del router
        self.routes =[]

    def reset_table(self):
        self.routes.clear()
    
    def get_port_from_name(self, name):
        for port in self.ports:
            if port.name == name:
                return port
        return False

    #add a new route to the router<name> <destination> <mask> <gateway> <interface>
    def add_new_route(self, destination:str, mask:str, gateway:str, interface:int):
        self.routes = netl.add_route(self.routes.copy(), destination, mask, gateway, interface)
    
    def delete_route(self, destination:str, mask:str, gateway:str, interface:int):
        self.routes = netl.delete_route(self.routes.copy(), destination, mask, gateway, interface)

    def setup_ip(self, ip, mask, port):
        self.interfaces[port].setup_ip(ip ,mask)

    def setup_mac(self, mac, port):
        self.interfaces[port].setup_mac(mac)


    def receive(self, bit, incoming_port, devices_visited, time):
        # interface de entrada
        rinterface = self.interfaces[incoming_port.name]
        rinterface.rframe += bit
        frame =  rinterface.rframe
        # es probable que sea un frame
        if len(frame) > 48:
            #obtengo la cantidad de bits que debe de tener la data del frame            
            nsizebits = int(frame[32:40], 2) * 8 # size in bytes 8*size = size en bits
            ori_mac = linkl.get_hex_ori_mac_from_frame(frame)
            des_mac = linkl.get_hex_des_mac_from_frame(frame)

            len_verification_data = int(frame[40:48], 2) * 8 # longitud de los datos de verificacion en bits
            
            data_plus_verificationd = frame[48:]
            # la trama que llego al router es una trama valida
            if len(data_plus_verificationd) == nsizebits + len_verification_data:
                #obtengo en hexadecimal la data 
                data = linkl.get_data_from_frame(frame)
                netl.checkARPP_Router(self, rinterface,incoming_port, ori_mac,data)

                if netl.is_ip_packet(data) and des_mac != 'FFFF':
                    des_ip = netl.get_packet_from_frame(frame)[0]
                    ori_ip = netl.get_packet_from_frame(frame)[1]
                    route = netl.search_match_route(des_ip, self.routes)
                    #ninguna ruta puede enrutar dicho paquete
                    if route == None:
                        icmp3 = netl.icmp_host_unreachable_frame(frame, rinterface)
                        rinterface.add_frame(icmp3)
                        if not rinterface.transmitting and not rinterface.stopped:
                            nextbit = rinterface.next_bit()
                            if nextbit != None:
                                self.init_transmission(nextbit, incoming_port, devices_visited, time)
                        # se debe enviar aca al host origen un paquete icmp
                    else:
                        # interface de salida
                        
                        sportname = f'{self.name}_{route.interface}'
                        sinterface = self.interfaces[sportname]
                        ip_connect = route.gateway if route.gateway != '0.0.0.0' else des_ip
                        packet = netl.get_package_from_frame_in_router(frame, sinterface, ip_connect)
                        sinterface.add_packet(packet)
                        sport = self.get_port_from_name(sportname)
                        arpq = netl.seach_ip_from_router(sinterface,'FFFF',ip_connect)
                        sinterface.add_frame(arpq)
                        if not sinterface.transmitting and not sinterface.stopped:
                            nextbit = sinterface.next_bit()
                            if nextbit != None:
                                handler.devices_visited.clear()
                                self.init_transmission(nextbit, sport, handler.devices_visited, time)

                rinterface.rframe = ""
                
    def colision_protocol(self, port, time):
        einterface = self.interface[port.name]
        einterface.transmitting = False
        # el host no puede enviar en este momento la sennal pues se esta transmitiendo informacion por el canal o no tiene canal para transmitir la informacion
        einterface.stopped = True
        # aumenta la cantidad de intentos fallidos
        einterface.failed_attempts += 1 
        # notifica que hubo una colision y la informacion no pudo enviarse
        # el rango se duplica en cada intento fallido
        
        nrand = random.randint(1, 2*einterface.failed_attempts*10)
        # dada una colision espero un tiempo cada vez mayor para poder volverla a enviar
        einterface.stopped_time = nrand * handler.slot_time
        


    def send(self, bit, incoming_port, devices_visited, time):
        nextport = incoming_port.next
        nextport.device.receive(bit, nextport, devices_visited, time)
        

    def put_data(self, data: str, port: Port):
        if port.cable == None or port.write_channel.data != Data.Null or port.next == None:
            return False
        else:
            port.write_channel.data = data
            self.interfaces[port.name].bit_sending = data
            return True


    
    
    def init_transmission(self, nextbit, incoming_port, devices_visited, time):
        interface = self.interfaces[incoming_port.name]
        interface.bit_sending = nextbit
        interface.stopped = False
        if self.put_data(nextbit, incoming_port):
            interface.transmitting = True
            interface.transmitting_time = 0
            self.send(nextbit, incoming_port, devices_visited, time)
        else:
            self.colision_protocol(incoming_port, time)
            
            
    
    def check_transmitting(self):
        return any(interface.transmitting for interface in self.interfaces.values())
    
    def check_stopped(self):
        return any(interface.stopped for interface in self.interfaces.values())
    
    def missing_data(self,incoming_port, device_visited):
        return
    
    def death_short(self, incoming_port, time):
        interface = self.interfaces[incoming_port.name]
        if interface.transmitting:
            self.colision_protocol(incoming_port, time)
class Host:
    def __init__(self, name: str, error_detection) -> None:
        self.name = name
        portname = f"{name}_1"
        port = Port(portname, self)
        self.port = port
        self.file = f"./Devices_Logs/Hosts/{name}.txt"
        self.data = ""
        # guarda todos los bloques de cadenas que aun no han sido enviados
        self.data_pending = queue.Queue()
        self.data_frame_penfing = queue.Queue()
        # muestra informacion sobre el bit que se esta transmitiendo cuando el host esta enviando informacion
        self.bit_sending = None
        self.bit_format = None
        self.transmitting_time = 0
        self.transmitting = False
        self.stopped = False
        self.stopped_time = 0
        self.failed_attempts = 0
        # bits que han sido recibidos por el host y que podrian ser una trama 
        self.rframe =""
        # me permite conecer  si una PC esta transmitiendo o no en un momento determinado informacion
        # direccion mac que tendria la PC
        self.mac = None
        # se escribiran solamente los datos recibidos por esta PC y quien los recibio
        self.file_d =f"./Devices_Logs/Hosts/{name}_data.txt"
        self.payload =f"./Devices_Logs/Hosts/{name}_payload.txt"
        self.incoming_frame =""
        self.slot_time = 3
        self.error_detection = error_detection
        self.ip = None
        self.mask = None
        self.broadcast = None
        self.packets = []
        self.routes =[]
        self.pings =[]
        # make txt files
        f = open(self.file, 'w')
        f.close()
        f = open(self.file_d, 'w')
        f.close()
        f = open(self.payload,'w')
        f.close()
        
    # def add_route(self, <destination> <mask> <gateway> <interface>):
        
    def reset_table(self):
        self.routes.clear()

    def add_new_route(self, destination, mask, gateway, interface):
        self.routes = netl.add_route(self.routes.copy(), destination, mask, gateway, interface)
    
    def delete_route(self, destination:str, mask:str, gateway:str, interface:int):
        self.routes = netl.delete_route(self.routes.copy(), destination, mask, gateway, interface)

    def add_packet(self, ip_connect, des_ip, data, protocol=0,ttl=0):
        p = neto.Packet(ip_connect,self.mac, self.ip, des_ip, data, protocol, ttl)
        self.packets.append(p)
            
    def add_ping(self, ping):
        self.pings.append(ping)
        
    def pings_remain(self):
        return len(self.pings) > 0
    
    def update_pings(self):
        self.pings = [ping for ping in self.pings if ping.remaining_messages != 0]
    
    def remove_packet(self, packet):
        self.packets.remove(packet)

    def setup_ip(self, ip, mask):
        self.ip = ip
        self.mask = mask
        self.broadcast = netl.get_host_broadcast(self.ip, self.mask)

    def __update_file(self, message, file):
        f = open(file, 'a')
        f.write(message)
        f.close()

    def log_hamming(self, source_mac, time, data_fixed):
        message = f"{time} {source_mac} {data_fixed} corrected by hamming"
        self.__update_file(message, self.file_d)

    def log(self, data, action, time, collison=False):
        terminal = "collision" if collison else "ok"
        message = f"{time} {self.port.name} {action} {data} {terminal}\n"
        self.__update_file(message, self.file)
    
    def log_frame(self, source_mac, datahex, time,corrupted=False):
        
        if corrupted:
            message = f"{time} {source_mac} the information{datahex} is corrupt\n"
        else:
            message = f"{time} {source_mac} {datahex}\n"
        self.__update_file(message, self.file_d)

    def log_payload(self, data, time):
        des_ip = netl.get_ip_from_bin(data[0:32])
        protocol = int(data[72:80])
        ori_ip = netl.get_ip_from_bin(data[32:64])
        payload = '{:X}'.format(int(data[88:],2))
        icmp = netl.message_log_icmp(payload) if protocol == 1 else  ""
        message = f"{time} {ori_ip} {payload} {icmp}\n"
        self.__update_file(message, self.payload)

    
    def data(self, origin_mac, data_frame, time):
        message = f"{time} {origin_mac} {data_frame}"
        self.__update_file(message)

    def colision_protocol(self, time):
            self.transmitting = False
            # el host no puede enviar en este momento la sennal pues se esta transmitiendo informacion por el canal o no tiene canal para transmitir la informacion
            self.stopped = True
            # aumenta la cantidad de intentos fallidos
            self.failed_attempts += 1 
            # notifica que hubo una colision y la informacion no pudo enviarse
            self.log(self.bit_sending, "send", time, True)
            # el rango se duplica en cada intento fallido
            if self.failed_attempts < 16:
                nrand = random.randint(1, 2*self.failed_attempts*10)
                # dada una colision espero un tiempo cada vez mayor para poder volverla a enviar
                self.stopped_time = nrand * self.slot_time
            else:
                # se cumplio el maximo de intentos fallidos permitidos por lo que se decide perder esa info                 
                self.stopped = True
                next_bit = self.next_bit()
                if next_bit != None:
                    self.bit_sending = next_bit
                    self.stopped = True
                    self.stopped_time = 1
                    self.failed_attempts = 0
                else:
                    self.stopped = False
        # en caso que no haya colision empiezo a regar la informacion  desde el host por toda la red de cables interconectados 
        # alcanzables por el host             


    def add_frame(self, frame:str):
        if self.data != "":
            # agrego esa nueva informacion a una cola de datos sin enviar
            self.data_pending.put(frame)
        else:
            self.data = frame

    def put_data(self, data: int):
        if self.port.cable == None or self.port.write_channel.data != Data.Null:
            return False
        else:
            self.port.write_channel.data = data
            self.bit_sending = data
            return True

    def next_bit(self):
        n = len(self.data)
        if n > 0:
            next = self.data[0]
            self.data = self.data[1:]
            return next

        if self.data_pending.qsize() > 0:
            self.data = self.data_pending.get()
            return self.next_bit()    

        return None

    # comprueba si la mac destino coincide con la mac del frame o es broadcast
    def is_for_me(self, mac):
        return mac == 'FFFF' or mac==self.mac
    
    def receive(self, bit, incoming_port, devices_visited, time):
        self.log(bit, "receive", time)
        self.rframe +=bit
        if len(self.rframe) > 48:
            #obtengo la mac de la pc que mando el frame origen
            origin_mac = '{:X}'.format(int(self.rframe[16:32], 2))
            #obtengo la mac destino del frame
            des_mac ='{:X}'.format(int(self.rframe[0:16], 2))
            #obtengo la cantidad de bits que debe de tener la data del frame            
            nsizebits = int(self.rframe[32:40], 2) * 8 # size in bytes 8*size = size en bits
            
            len_verification_data = int(self.rframe[40:48], 2) * 8 # longitud de los datos de verificacion en bits
            
            data_plus_verificationd = self.rframe[48:]
            # la trama que llego a la pc es valida
            if len(data_plus_verificationd) == nsizebits + len_verification_data :
                
                #obtengo en hexadecimal la data 
                # print(f"{origin_mac}--{des_mac} vs {self.mac}")
                data = self.rframe[48:48+nsizebits]
            

                verification_data = self.rframe[48+nsizebits:]
                datahex = '{:X}'.format(int(data,2))
                self.rframe =""
                
                if self.is_for_me(des_mac):
                    if self.error_detection =='crc':
                        data_to_verify = data + verification_data
                        decode = format(int(errors_algs.CRCDecode(data_to_verify), base = 2), '08b')
                        errors = errors_algs.CheckError(decode)
                        if errors:
                            self.log_frame(origin_mac, datahex, time, True)
                            return
                        else:
                            # guardo en el file _data.txt la trama que recibio la pc
                            self.log_frame(origin_mac, datahex, time)
                    else:
                        encoded_data,_ = errors_algs.hamming_encode(data)
                        errors,error_index = errors_algs.detect_error(encoded_data, int(verification_data,2))
                        if errors:
                            self.log_frame(origin_mac, datahex, time,True)
                            original_error_index = errors_algs.calc_error_bit_pos(error_index)
                            original_fixed = errors_algs.fix_bit(data, original_error_index)
                            original_fixed_hex = '{:X}'.format(int(original_fixed,2))
                            self.log_hamming(origin_mac, time, original_fixed_hex)
                            return
                        else:
                            # guardo en el file _data.txt la trama que recibio la pc
                            self.log_frame(origin_mac, datahex, time)    

                    # check if a frame es from ARP Protocol
                    netl.checkARP(self, origin_mac, data)
                    # if frame es ip packet
                    if netl.is_ip_packet(data):
                        if netl.is_ping(self,data):
                            netl.pong(self, data)
                        self.log_payload(data, time)
                


    def send(self, data, incoming_port, devices_visited, time):
        if self in devices_visited:
            return
        else:
            devices_visited.append(self)

        self.transmitting = True
        self.log(data, "send", time)
        self.transmitting_time = 0
        if self.port.next != None:
            self.port.next.device.receive(data, self.port.next, devices_visited, time)
                

    def death_short(self, incoming_port, time):
        if self.transmitting:
            self.colision_protocol(time)

    def missing_data(self,incoming_port, devices_visited):
        return

    def init_transmission(self, devices_visited, bit,time):
        self.stopped = False
        self.transmitting = True
        self.bit_sending = bit
        if self.put_data(bit):
            self.send(bit, self.port, devices_visited, time)
        else:
            self.colision_protocol(time)    
        

class Hub:
    def __init__(self, name: str, ports_amount: int) -> None:
        self.name = name
        self.connections = [None] * ports_amount
        self.file = f"./Devices_Logs/Hubs/{name}.txt"
        self.ports = []  # instance a list of ports
        # con esto se si el hub esta retrasmitiendo la informacion proveniente de un host que esta enviando info y que informacion
        # es resulta util para detectar colisiones
        self.bit_sending = None
        for i in range(ports_amount):
            portname = f"{name}_{i + 1}"
            port = Port(portname, self)
            self.ports.append(port)
        # make the hub file
        f = open(self.file, 'w')
        f.close()

    def __update_file(self, message: str) -> None:
        f = open(self.file, 'a')
        f.write(message)
        f.close()

    def log(self, data, action, port, time) -> None:
        message = f"{time} {port.name} {action} {data}\n"
        self.__update_file(message)

    def put_data(self, data: str, port: Port):
        if port.write_channel.data == Data.Null:
            port.write_channel.data = data
            return True
        else:
            return False    

    def receive(self, bit, incoming_port, devices_visited, time):
        self.log(bit, "receive", incoming_port, time)
        self.bit_sending = bit
        self.send(bit, incoming_port, devices_visited, time)

    def send(self, bit, incoming_port, devices_visited, time):
        if self in devices_visited:
            return
        else:
            devices_visited.append(self)
        
        for _port in self.ports:
            if _port != incoming_port and  _port.cable !=None and _port.next != None:
                if not self.put_data(bit, _port):
                    self.death_short(incoming_port, time)
                    return
                _port.write_channel.data = bit
                self.log(bit, "send", _port, time)
                _port.next.device.receive(bit, _port.next, devices_visited, time)


    def death_short(self, incoming_port: Port, time: int):
        self.bit_sending = None
        incoming_port.read_channel.data = Data.Null
        incoming_port.write_channel.data = Data.Null
        incoming_port.next.device.death_short(incoming_port.next, time)
        
        # se manda a parar a todo los demas host que esten enviando por el hub
        for port in self.ports:
            if port != incoming_port and port.cable != None:
                port.read_channel.data = Data.Null
                port.write_channel.data =  Data.Null
                if port.next != None:
                    nextport = port.next
                    nextport.device.death_short(nextport, time)
        
        
            
    def missing_data(self, incoming_port, devices_visited):
        self.bit_sending = None
        if self in devices_visited:
            return
        else:
            devices_visited.append(self)
        
        for port in [p for p in self.ports if p != incoming_port and p.next != None]:
            port.write_channel.data = Data.Null
            if port.next != None:
                port.next.device.missing_data(port.next, devices_visited)


class Buffer:
    def __init__(self):
        self.sending_frame_pending = queue.Queue()
        # cadena de informacion que el switch ira transmitiendo por ese puerto hacia otro dispositivos
        self.sending_frame = ""
        # cadena de informacion que va recibiendo el switch bit a bit por ese puerto hasta que pueda completar el formato de una trama y decidir para donde
        # lo envia 
        self.incoming_frame = ""
        self.transmitting = False
        self.receiving = False
        self.bit_sending = None
        self.transmitting_time = 0
        self.failed_attempts = 0
        self.stopped = False
        self.stopped_time = 0

        
    def add_frame(self, frame):
        if self.sending_frame == "":
            self.sending_frame = frame
        else:
            self.sending_frame_pending.put(frame)
        
    def next_bit(self):
        n = len(self.sending_frame)
        if n > 0:
            next = self.sending_frame[0]
            self.sending_frame = self.sending_frame[1:]
            return next

        if self.sending_frame_pending.qsize() > 0:
            self.sending_frame = self.sending_frame_pending.get()
            return self.next_bit()    

        return None

class Switch:
    def __init__(self, name: str, ports_amount: int) -> None:
        self.name = name
        self.file = f"./Devices_Logs/Switches/{name}.txt"
        self.ports = []  # instance a list of ports
        # con esto se si el hub esta retrasmitiendo la informacion proveniente de un host que esta enviando info y que informacion
        
        # diccionario de la forma key = mac value = port of device mac
        self.map = {}
        self.buffers = {}
        self.frames = []
        for i in range(ports_amount):
            portname = f"{name}_{i + 1}"
            self.buffers[portname] = Buffer()
            port = Port(portname, self)
            self.ports.append(port)
        # make the hub file
        f = open(self.file, 'w')
        f.close()
        self.slot_time = 3

    def __update_file(self, message: str) -> None:
        f = open(self.file, 'a')
        f.write(message)
        f.close()

    def log(self, data, action, port, time, colision = False) -> None:
        if colision:
            message = f"{time} {port} {action} {data} colision\n"
        else:
            message = f"{time} {port} {action} {data}\n"
        self.__update_file(message)

    def receive(self, bit, incoming_port, devices_visited, time):
        self.log(bit, "receive", incoming_port.name, time)
        buffer = self.buffers[incoming_port.name]
        buffer.incoming_frame += bit
        rframe = buffer.incoming_frame
        
        ## cumple el formato de una trama 16bit outmac 16 inmac 8 bit len 8bit0 data
        if len(rframe) > 48:
            ori_mac = linkl.get_hex_ori_mac_from_frame(rframe)
            des_mac = linkl.get_hex_des_mac_from_frame(rframe)
            lendatabits = int(rframe[32:40], 2) * 8
            len_verification_data = int(rframe[40:48], 2) * 8
            checkrest = rframe[48:]
            
            
            if len(checkrest) == lendatabits + len_verification_data:
                
                # en caso que la mac este guardada en la tabla de del switch
                if des_mac not in self.map.keys():
                    
                    for port in self.ports:
                        if port != incoming_port:
                            newbuffer =  self.buffers[port.name]
                            newbuffer.add_frame(rframe)
                            if not newbuffer.transmitting and not newbuffer.stopped:
                                nextbit = newbuffer.next_bit()
                                if nextbit != None:
                                    self.init_transmission(nextbit, port, devices_visited, time)
                        
                else:
                    nextport = self.map[des_mac]
                    sbuffer = self.buffers[nextport.name]
                    sbuffer.add_frame(rframe)
                    if not sbuffer.transmitting and not sbuffer.stopped:
                        nextbit = sbuffer.next_bit()
                        if nextbit != None:
                            self.init_transmission(nextbit, nextport, devices_visited, time)
                
                buffer.incoming_frame = ""

    def put_data(self, data: str, port: Port) -> bool:
        if port.cable == None or port.write_channel.data != Data.Null or port.next == None:
            return False
        else:
            port.write_channel.data = data
            return True

    def colision_protocol(self, switch_port, nextbit, time):
        pbuffer = self.buffers[switch_port.name]
        pbuffer.transmitting = False
        # el host no puede enviar en este momento la sennal pues se esta transmitiendo informacion por el canal o no tiene canal para transmitir la informacion
        pbuffer.stopped = True
        # aumenta la cantidad de intentos fallidos
        pbuffer.failed_attempts += 1 
        # notifica que hubo una colision y la informacion no pudo enviarse
        self.log(nextbit, "send", switch_port.name, time, True)
        # el rango se duplica en cada intento fallido
        if pbuffer.failed_attempts < 16:
            nrand = random.randint(1, 2*pbuffer.failed_attempts*10)
            # dada una colision espero un tiempo cada vez mayor para poder volverla a enviar
            pbuffer.stopped_time = nrand * self.slot_time
        else:
            # se cumplio el maximo de intentos fallidos permitidos por lo que se decide perder esa info                 
            pbuffer.stopped = True
            next_bit = pbuffer.next_bit()
            if next_bit != None:
                pbuffer.bit_sending = next_bit
                pbuffer.stopped = True
                pbuffer.stopped_time = 1
                pbuffer.failed_attempts = 0
            else:
                pbuffer.stopped = False


    def init_transmission(self, nextbit, incoming_port, devices_visited, time):
        buffer = self.buffers[incoming_port.name]
        buffer.stopped = False
        buffer.bit_sending = nextbit
        if self.put_data(nextbit, incoming_port):
            buffer.transmitting = True
            buffer.transmitting_time = 0
            buffer.bit_sending = nextbit
            self.send(nextbit, incoming_port, devices_visited, time)
        else:
            self.colision_protocol(incoming_port, nextbit, time)    



    def send(self, bit, incoming_port, devices_visited, time):

        self.log(bit, "send", incoming_port.name, time)
        nextport = incoming_port.next
        nextport.device.receive(bit, nextport, devices_visited, time)
        


    def death_short(self, incoming_port, time):
        buffer = self.buffers[incoming_port.name]
        if buffer.transmitting:
            self.colision_protocol(incoming_port, buffer.bit_sending, time)
        
        
    def missing_data(self,incoming_port, device_visited):
        return         

    def check_transmitting(self):
        return any(buffer.transmitting for buffer in self.buffers.values())
        
    def check_stopped(self):
        return any(buffer.stopped for buffer in self.buffers.values())