
import objs
import string
import errors_algs
import re
import network_layer_utils as netl
errors = {1 : "do not has a cable connected", 2: "does not exist", 3: "is not free", 4: "the device must be a host",
        5: "host busy (collision)", 6: "has a cable connected, but its other endpoint is not connected to another device" }
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class Device_handler:
    

    def __init__(self, slot_time: int, error_detection:str) -> None:
        self.hosts = []
        self.switches = []
        self.routers = []
        self.time = 0
        self.slot_time = slot_time
        self.error_detection = error_detection
        # diccionario que va a guardar todos los puertos de todos los devices para poder acceder de manera rapida a los mismo en 
        # las operaciones necesarias
        self.ports = {}
        self.devices_visited = []
        objs.handler = self
        netl.handler = self


    def __validate_send(self, host) -> bool:

        port_name = host+"_1"
        if port_name not in self.ports.keys():
            print(f"{bcolors.WARNING} send error {bcolors.ENDC} the device {bcolors.OKBLUE} {host} {bcolors.ENDC} {errors[2]}")
            return False

        port = self.ports[port_name]
        if not isinstance(port.device, objs.Host):
            print(f"{bcolors.WARNING} send error {bcolors.ENDC} the device {bcolors.OKBLUE} {host} {bcolors.ENDC} {errors[4]}")
            return False

        
        return True

    def __validate_disconnection(self, name_port):
        
        if name_port not in self.ports.keys():
            print(f"{bcolors.WARNING}invalid disconnection{bcolors.ENDC} port {bcolors.OKGREEN}{name_port} {bcolors.ENDC} {errors[2]}")
            return False
        port = self.ports[name_port]
        if port.cable == None:
                print(f"{bcolors.WARNING} invalid disconnection{bcolors.ENDC} port{bcolors.OKGREEN} {name_port} {bcolors.ENDC} {errors[1]}")
                return False

        return True

    def __validate_connection(self, name_port): # Private method to identify wether a device is a hub or a host
        

        if name_port not in self.ports.keys():
            print(f"{bcolors.WARNING} invalid connection{bcolors.ENDC} port  {bcolors.OKGREEN}{name_port} {bcolors.ENDC} {errors[2]}")
            return False

        port = self.ports[name_port]
        
        if  port.cable != None:
                print(f"{bcolors.WARNING} invalid connection {bcolors.ENDC} port  {bcolors.OKGREEN}{name_port} {bcolors.ENDC}{errors[3]}")
                return False

        device = port.device
        if isinstance(device, objs.Host) and device.mac == None:
            print(f"{device.name} not has a network card connected")
            return False        

        return True

    def __validate_setup_mac(self,pc, mac:str):
        port = pc + "_1"
        if not all(c in string.hexdigits for c in mac):
            print(f"{bcolors.WARNING} invalid mac assign{bcolors.ENDC}  {bcolors.OKGREEN}{mac} {bcolors.ENDC} not in hexadecimal")
            return False

        if port not in self.ports.keys():
            print(f"{bcolors.WARNING} invalid mac assign{bcolors.ENDC} PC {bcolors.OKGREEN}{pc} {bcolors.ENDC} {errors[2]}")
            return False
        
        return True    

    def __validate_send_packet(self, host_name, des_ip, data):
        if not any(h.name == host_name for h in self.hosts):
            return False
        if not netl.ValidIP(des_ip):
            return False
        if not all(c in string.hexdigits for c in data):
            return False
        return True            

    def __valid_mac(self,mac) -> bool:                                #broadcast
        return any(host.mac == mac for host in self.hosts)  or mac == 'FFFF'

    def __validate_send_frame(self,host, destiny_mac):
        if not any(host == h.name for h in self.hosts):
            return False
        if not self.__valid_mac(destiny_mac):
            return False
        
        return True            

    def __validate_data_hex(self,data):
        if not all(c in string.hexdigits for c in data):
            return False
        return True    

    def __validate_ip(self, name, ip, mask):
        if all(h.name != name for h in self.hosts) and all(r.name != name for r in self.routers):
            return False
        if not netl.ValidIP(ip) or not netl.ValidIP(mask):
            return False
        return True

    


    def finished_network_transmission(self):
        # al no quedar mas instruccionens por ejecutar
        # mantengo recorrido de los devices mientras haya alguna
        # actividad de los host      
        while any(host.transmitting or host.stopped for host in self.hosts) or any(switch.check_transmitting() for switch in self.switches):
            self.time += 1
            self.__update_devices()


    def __update_network_status(self, time: int):
        # actualizo la red hasta el time de la instruccion actual
        while self.time < time:
            self.time += 1
            self.__update_devices()
        self.time = time

    def create_pc(self, name: str, time: int):
        # actualiza la red hasta que llegues al time en que vino la nueva instruccion
        self.__update_network_status(time)
        newpc = objs.Host(name,self.error_detection)
        self.hosts.append(newpc)
        # agrego el unico puerto que tiene un host al dicc que contiene todos los puertos de la red
        self.ports[newpc.port.name] = newpc.port

    def create_hub(self, name: str, ports, time: int):
        # actualiza la red hasta que llegues al time en que vino la nueva instruccion
        self.__update_network_status(time)    
        newhub = objs.Hub(name, ports)
        # agrego cada puerto que tiene un hub al dicc que contiene todos puertos de la red
        for port in newhub.ports:
            self.ports[port.name] = port
    
    def create_switch(self,name: str, ports: int, time: int):
        self.__update_network_status(time)
        newswitch = objs.Switch(name, ports)
        self.switches.append(newswitch)
        for port in newswitch.ports:
            self.ports[port.name] = port

    def setup_ip(self, name, interface, ip, mask, time):
        self.__update_network_status(time)
        if self.__validate_ip(name, ip, mask):
            if any(h.name == name for h in self.hosts):
                self.ports[f"{name}_1"].device.setup_ip(ip,mask)
            else:
                return None


            

    def setup_mac(self, host, address, time: int):
        
        if self.__validate_setup_mac(host,address):

            self.ports[f"{host}_1"].device.mac = address


    def setup_connection(self, name_port1: str, name_port2: str, time: int):
        # actualiza la red hasta que llegues al time en que vino la nueva instruccion
        self.__update_network_status(time)

        if self.__validate_connection(name_port1) and self.__validate_connection(name_port2):
            port1 = self.ports[name_port1]
            port2 = self.ports[name_port2]
            device1 = port1.device
            device2 = port2.device
            if device1 == device2:
                print("Ports of the same device is not possible connected")
                
            else:
                port1.next = port2
                port2.next = port1
                newcable = objs.CableDuplex()
                port1.cable = newcable
                port2.cable = newcable
                port1.write_channel = newcable.cableA
                port2.read_channel  = newcable.cableA
                port2.write_channel = newcable.cableB
                port1.read_channel  = newcable.cableB
                
                # si los dispositvos  pertenecientes a los puertos estan transmitiendo informacion a la vez
                #
                # en caso que conecte un hub a otro hub que estan retransmitiendo la informacion desde distintos host
                # se manda un sennal para tumbar la transmision en ambos lados y los host volveraran a intentar 
                # transmitir la informacion luego de un tiempo aleatorio en cada uno 
                
                if isinstance(device1, objs.Hub) and device1.bit_sending and isinstance(device2, objs.Hub) and device2.bit_sending:
                    device1.death_short(port1, time)
                    device2.death_short(port2, time)

                if isinstance(device1, objs.Switch) and isinstance(device2, objs.Host):
                    device1.map[device2.mac] = port1

                if isinstance(device1, objs.Hub) and device1.bit_sending:
                    port1.write_channel.data = device1.bit_sending
                    self.devices_visited.clear()
                    device2.receive(device1.bit_sending, port2, self.devices_visited, time)
                
                if isinstance(device2,objs.Switch) and isinstance(device1,objs.Host):
                    device2.map[device1.mac] = port2

                if isinstance(device2, objs.Hub) and device2.bit_sending:
                    port2.write_channel.data = device2.bit_sending
                    self.devices_visited.clear()
                    device1.receive(device2.bit_sending, port1, self.devices_visited, time)


    def shutdown_connection(self, name_port: str, time: int):
        self.__update_network_status(time)

        if self.__validate_disconnection(name_port):
            port1 = self.ports[name_port]
            if  port1.next != None:                
                port2 = port1.next
                # en caso que desde el puerto 1 se este enviando informacion
                if port1.write_channel.data != objs.Data.Null:
                    # en caso que la informacion provenga a traves del port1
                    # esta deja de llegar desde el port2 a todas las conexiones que partan de el
                    port1.write_channel.data = objs.Data.Null
                    self.devices_visited.clear()
                    port2.device.missing_data(port2, self.devices_visited)
                
                # en caso que desde el puerto 2 se este enviando informacion
                if port2.write_channel.data != objs.Data.Null:
                    # en caso que la informacion provenga a traves del port2
                    # esta deja de llegar desde el port2 a todas las conexiones que partan de el
                    port2.write_channel.data = objs.Data.Null
                    port1.device.missing_data(port2, self.devices_visited)
                    
                # como los cables son duplex ambos casos pueden ocurrir a la vez    
    
                


                # tengo que remover el cable del puerto port1 pues este quedaria todavia conectado al puerto 2
                port1.cable = None
                # al desconectar una de las puntas del cable 1 se perderia la conexion entre estos dos cables        
                port1.next =  None
                port2.next =  None
            else:
                port1.cable = None    

    # de esta forma se revisa si host que esta transmitiendo dejo de hacerlo y por ende toda la informacion desaparece de los cables
    # a los que pueda llegar desde el otra

    def __update_devices(self):
        for host in self.hosts:
            # en caso que el host no haya podido enviar una informacion previamente producto de una colision
            # por la forma del carrier sense el va a esperar un tiempo aleatorio  para volver a enviar
            # esa informacion y el host esta en modo stopped
            if host.stopped:
                host.stopped_time -= 1
                if host.stopped_time == 0:
                    self.devices_visited.clear()
                    # vuelve a intentar enviar el bit que habia fallado previamente
                    host.stopped = False
                    host.init_transmission(self.devices_visited, host.bit_sending, self.time)
            # en caso que el host este transmitiendo un informacion
            elif host.transmitting:
                host.transmitting_time += 1
                # compruebo si la informacion vencio el maximo time que puede estar en el canal
                if host.transmitting_time % self.slot_time == 0:
                    if host.port.cable != None:
                        host.port.write_channel.data = objs.Data.Null
                    host.bit_sending = None    
                    # dame el proximo bit a enviar por el host
                    nex_bit = host.next_bit()                   
                    
                    if host.port.next != None:
                        nextdevice = host.port.next.device
                        
                        # limpia el camino para enviar el proximo bit
                        self.devices_visited.clear()
                        host.port.next.device.missing_data(host.port.next, self.devices_visited)
                        
                    # intenta enviar el proximom bit 
                    if nex_bit != None:
                        
                        self.devices_visited.clear()
                        host.init_transmission(self.devices_visited, nex_bit,  self.time)
                        
                    else:
                        host.transmitting = False
                        host.transmitting_time = 0    

        for switch in self.switches:
            for port in switch.ports:
                portbuff = switch.buffers[port.name]
                if portbuff.stopped:
                    portbuff.stopped_time -= 1
                    self.devices_visited.clear()
                    port.device.init_transmission(portbuff.bit_sending, port, self.devices_visited, self.time)

                elif portbuff.transmitting:
                    portbuff.transmitting_time += 1
                    if portbuff.transmitting_time % self.slot_time == 0:
                        port.write_channel.data = objs.Data.Null
                        self.devices_visited.clear()
                        port.next.device.missing_data(port.next, self.devices_visited) 
                        nextbit = portbuff.next_bit()
                        if nextbit != None:
                            self.devices_visited.clear()
                            switch.init_transmission(nextbit, port, self.devices_visited, self.time)
                        else:
                            portbuff.transmitting = False
                            portbuff.bit_sending = None                     





    def add_more_zeros(self, data:str):
        # devuelve el reste que deja el multiplo de 8 (8q) mas cercano al len de data que es >= que len(data)
        near_mul = lambda pow8, number : pow8% number if pow8 > number else near_mul(pow8+8, number)
        for i in range(near_mul(8, len(data))):
            data = '0' +data
        return data
        
    def setup_data(self,data):
        databin = format(int(data, base = 16), '08b')
        return  self.add_more_zeros(databin)   

    def setup_send_frame(self, origin_pc, destiny_mac, datahex, time):
        if self.__validate_data_hex(datahex):
            data_bin = self.setup_data(datahex)
            self.send_frame(origin_pc, destiny_mac, data_bin, time)
        else:
            print('Data not in hex')


    def send_frame(self ,origin_pc, destiny_mac:str, data:str, time: int):
        # actualiza primero la red por si todavia no ha llegado a time
        self.__update_network_status(time)

        if self.__validate_send_frame(origin_pc, destiny_mac):
            host = self.ports[f'{origin_pc}_1'].device
            if self.error_detection == 'crc':
                encode = self.add_more_zeros(format(int(errors_algs.CRCEncode(data), base = 2), '08b'))
            else:
                _,redundant_bits_amount = errors_algs.hamming_encode(data)
                encode = self.add_more_zeros(format(redundant_bits_amount, '08b'))
            data_frame = format(int(destiny_mac, base = 16), '016b') + format(int(host.mac, base=16), '016b') + format(len(data)//8, '08b') + format(len(encode)//8, '08b') + data + encode
            host.add_frame(data_frame)
            # en caso que el host este disponible para enviar pues el mismo puede estar
            # en medio de una transmision o estar esperando producto de una colision a enviar un dato fallido 
            if not host.stopped and not host.transmitting:
                nextbit = host.next_bit()
                self.devices_visited.clear()
                host.init_transmission(self.devices_visited, nextbit, time)

    def send(self, origin_pc, data, time):
        # actualiza primero la red por si todavia no ha llegado a time 
        self.__update_network_status(time)

        if self.__validate_send(origin_pc):  # El send es valido
            host = self.ports[origin_pc+'_1'].device
            # agrego el la data la PC
            host.add_frame(data)
            # en caso que el host este disponible para enviar pues el mismo puede estar
            # en medio de una transmision o estar esperando producto de una colision a enviar un dato fallido 
            if not host.stopped and not host.transmitting:
                nextbit = host.next_bit()
                self.devices_visited.clear()
                host.init_transmission(self.devices_visited, nextbit, time)

                
    def send_packet(self, host_name, des_ip,  data, time):
        self.__update_network_status(time)
        if self.__validate_send_packet(host_name, des_ip, data):
            host = self.ports[host_name+'_1'].device
            bin_data = self.setup_data(data)
            host.add_packet(des_ip, bin_data)
            netl.search_ip(host, 'FFFF', des_ip)
        