from network_layer_objs import Interface, Packet, Route
import link_layer_utils as linkl
import re

handler = None
# actualiza los packets temporales en los host y chequea si ya es posible enviar el packet
def check_PackageCondition(host):
    for packet in host.packets:
        if packet.mac_des != None:
            setupFrameFromPacket(packet, host)
            host.remove_packet(packet)

def check_PackageCondition_From_Router(interface, port, router):
    for packet in interface.packets:
        if packet.mac_des != None:
            setupFrameFromPacketRouter(packet, router, interface, port)
            interface.remove_packet(packet)

def setupFrameFromPacketRouter(packet, router, interface, port):
    data = ip_package(packet.ori_ip,packet.des_ip, packet.data, packet.ttl, packet.protocol)
    new_frame = linkl.get_frame(packet.mac_des,interface.mac,data)
    interface.add_frame(new_frame)
    if not interface.transmitting and not interface.stopped:
        nextbit = interface.next_bit()
        if nextbit != None:
            handler.devices_visited.clear()
            router.init_transmission(nextbit, port, handler.devices_visited, handler.time)
            
# revisa si la cadena de bits cumple con el formato del protocolo ARP
def checkARP(host, des_mac, bits):
    if len(bits) == 64: #cumple el formato de 4 bytes ARPR | ARPQ 4bytes IP
        ip = get_ip_from_bin(bits[32:]) # convert bits chunk to {}.{}.{}.{} ip format 
        word = get_ascii_from_bin(bits[0:32]) # convert
        if word == 'ARPQ' and ip == host.ip:
            arpqFrame = linkl.get_frame(des_mac, host.mac, ARPResponse(ip))
            host.add_frame(arpqFrame)
            if not host.transmitting and not host.stopped:
                nextbit = host.next_bit()
                if nextbit != None:
                    handler.devices_visited.clear()
                    host.init_transmission(handler.devices_visited, nextbit, handler.time)

        if word == 'ARPR':
            for packet in host.packets:
                if packet.ip_connect == ip:
                    packet.mac_des = des_mac
            check_PackageCondition(host)   

# verifica si el paquete ip correspone con un icmp tipo ping (payload =8)
def is_ping(host, ip_packet):
    des_ip = get_ip_from_bin(ip_packet[0:32])
    protocol = int(ip_packet[72:80],2)
    payload = linkl.bin_to_hex(ip_packet[88:])
    return protocol == 1 and payload == '8' and host.ip == des_ip

def pong(host,ip_packet):
    des_ip = get_ip_from_bin(ip_packet[0:32])
    new_des_ip = get_ip_from_bin(ip_packet[32:64])
    bin_data = linkl.setup_data('0')
    route = search_match_route(new_des_ip, host.routes)
    if route != None:
        ip_connect = route.gateway if route.gateway != '0.0.0.0' else des_ip
        host.add_packet(ip_connect, new_des_ip, bin_data, 1)
        search_ip(host, 'FFFF', ip_connect)

def checkARPP_Router(router, interface,port,des_mac, bits):
    if len(bits) == 64: #cumple el formato de 4 bytes ARPR | ARPQ 4bytes IP
        ip = get_ip_from_bin(bits[32:]) # convert bits chunk to {}.{}.{}.{} ip format 
        word = get_ascii_from_bin(bits[0:32]) # convert
        if word == 'ARPQ' and ip == interface.ip:
            new_frame = linkl.get_frame(des_mac,interface.mac,ARPResponse(ip))
            interface.add_frame(new_frame)
            if not interface.transmitting and not interface.stopped:
                nextbit = interface.next_bit()
                if nextbit != None:
                    handler.devices_visited.clear()
                    router.init_transmission(nextbit, port, handler.devices_visited, handler.time)
                        
        if word == 'ARPR':
            for packet in interface.packets:
                if packet.ip_connect == ip:
                    packet.mac_des = des_mac
            check_PackageCondition_From_Router(interface, port, router)  

# revisa si la data puede ser un ip_packet
def is_ip_packet(data):
    if len(data) > 88:
        payload_size = int(data[80:88],2) *8
        payload = data[88:]
        return payload_size == len(payload)
    return False

def get_packet_from_frame(frame:str):
    data = linkl.get_data_from_frame(frame)
    des_ip = get_ip_from_bin(data[0:32])    
    ori_ip = get_ip_from_bin(data[32:64])
    ttl = int(data[64:72],2)
    protocol = int(data[72:80])
    payload = data[88:]
    
    return [des_ip, ori_ip, ttl, protocol, payload]
    



def search_ip(host, des_mac, des_ip):
    q = ARPQuery(des_ip)
    handler.send_frame(host.name, des_mac, q, handler.time)

def seach_ip_from_router(interface, des_mac, des_ip):
    q = ARPQuery(des_ip)
    frame = linkl.get_frame(des_mac, interface.mac, q)
    return frame


# obtiene ip format {Int}.{Int}.{Int}.{Int} de una cadena de bits donde cada byte(8bits) representa numero del ip
def get_ip_from_bin(binIP):
    a = f"{int(binIP[0:8],2)}.{int(binIP[8:16],2)}.{int(binIP[16:24],2)}.{int(binIP[24:32],2)}"
    return a

# Dado un ip {}.{}.{}.{} convierte a una cadena de bits donde cada byte representa un numero de los 4 del ip
def get_bin_from_ip(ip):
    bin_ip =''
    for n in ip.split('.'):
        bin_ip += format(int(n),'08b')
    return bin_ip

# obtiene cad caracter de una cadena binaria doonde cada byte es el ascii del caracter
def get_ascii_from_bin(bits):
    return chr(int(bits[0:8],2)) + chr(int(bits[8:16],2)) + chr(int(bits[16:24],2)) + chr(int(bits[24:32],2))

def get_and_ip_op(ip1,ip2):
    ip1b = get_bin_from_ip(ip1)
    ip2b = get_bin_from_ip(ip2)
    result=''
    
    for i,j in zip(ip1b,ip2b) :
        result += f'{int(i) & int(j)}'
    
    return get_ip_from_bin(result)


def setupFrameFromPacket(packet, host):
    data = ip_package(packet.ori_ip,packet.des_ip, packet.data, packet.ttl, packet.protocol)
    handler.send_frame(host.name, packet.mac_des, data, handler.time)

# identifica si un ip es valido
def ValidIP(input:str):
    regex ="^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$"
    return True if re.search(regex,input) else False

# Dado una seria de caracteres devuelve en binario el codigo en ascii de cada caracter en cada byte
def get_bin_from_ascii(word):
    bin_ascii=''
    for c in word:
        bin_ascii += format(ord(c), '08b')
    return bin_ascii

#dada un ip te devuelve la data del
def ARPQuery(ip):
    return get_bin_from_ascii('ARPQ') + get_bin_from_ip(ip)

def ARPResponse(ip):
    return get_bin_from_ascii('ARPR') + get_bin_from_ip(ip)

# dada un ip te devuelve su representaci'on en binario
def bin_ip(ip):
    result= ""
    for n in ip.split('.'):
        result += format(int(n),'08b')
    return result

# obtenemos el ip_package 
def ip_package(ori_ip,des_ip, payload, ttl=0, protocol=0):
    package = ""
    package += bin_ip(des_ip) + bin_ip(ori_ip)
    package += format(ttl,'08b') + format(protocol, '08b')
    package += format(len(payload)//8, '08b')
    package += payload
    return package

# te devuelve un frame que corresponde al envia de un paquete ip con protocolo icmp y payload =3 que es cuando es unreachable el ip
def icmp_host_unreachable_frame(oldFrame, interface):
    des_mac = linkl.bin_to_hex(oldFrame[0:16])
    ori_mac = linkl.bin_to_hex(oldFrame[16:32])
    ip_packet_elems = get_ip_packet_elems(oldFrame)
    des_ip = get_ip_from_bin(ip_packet_elems[0])
    ori_ip = get_ip_from_bin(ip_packet_elems[1])
    new_ip_packet = ip_package(interface.ip, ori_ip, format(3,'08b'), 0, 1)
    new_frame = linkl.get_frame(ori_mac, des_mac, new_ip_packet)
    return new_frame


def get_ip_packet_elems(frame:str):
    data = linkl.get_data_from_frame(frame)
    des_ip = data[0:32]
    ori_ip = data[32:64]
    ttl = data[64:72]
    protocol = data[72:80]
    payload = data[88:]
    return (des_ip, ori_ip, ttl, protocol, payload)

def get_package_from_frame_in_router(frame:str, interface:Interface, ip_connect):
    ip_packet_elems = get_ip_packet_elems(frame)
    des_ip = get_ip_from_bin(ip_packet_elems[0])
    ori_ip = get_ip_from_bin(ip_packet_elems[1])
    ttl = int(ip_packet_elems[2])
    protocol = int(ip_packet_elems[3])
    payload = ip_packet_elems[4]
    packet = Packet(ip_connect, interface.mac, ori_ip, des_ip, payload, protocol, ttl)
    
    return packet

def get_new_packet_resquest_from_frame(frame:str, interface:Interface, newPayload):
    data = linkl.get_data_from_frame(frame)
    des_ip = data[0:32]
    ori_ip = data[32:64]
    ttl = data[64:72]
    protocol = data[72:80]
    payload = format(3, '08b')
    packet = Packet(interface.mac, ori_ip, des_ip, payload, protocol, ttl)
    return packet

# Devuelve la cantidad la cantidad de unos de la máscara de subred.
def get_1s_mask(mask:str):
    return get_bin_from_ip(mask).count('1')

# Actualiza la lista de rutas con una nueva ruta manteniendo el orden de prioridad por la cantidad de 1s de la mask 
def add_route(routes:'list[Route]', destination:str, mask:str, gateway:str, interface:int):
    route = route = Route(destination, mask, gateway, interface)
    for i,r in enumerate(routes):
        if get_1s_mask(route.mask) > get_1s_mask(r.mask):
            routes.insert(i, route)
            return routes
    routes.append(route)
    return routes

# eliminar una ruta de la lista de rutas 
def delete_route(routes:'list[Route]', destination:str, mask:str, gateway:str, interface:int):
    for route in routes:
        if route.destination == destination and route.mask == mask and route.gateway == gateway and route.interface == interface:
            routes.remove(route)
            return routes
    return routes

# devuelve True o False en dependencia de si la ruta enruta o no con el ip
# La ruta enruta con el ip si al hacer and entre el ip y la mask de la ruta te da el mismo ip que hay en destination
def match_route(route:Route, ip):
    andOp = get_and_ip_op(route.mask, ip) 
    return andOp == route.destination

def search_match_route(ip,routes:'list[Route]'):
    for route in routes:
        if match_route(route, ip):
            return route
    return None

# imprime un mensaje en dependencia del valor del payload en un paquete ip icmp
def message_log_icmp(number:str):
    if number == '0':
        return 'echo reply'
    elif number == '3':
        return 'destination host unreachable'
    elif number == '8':
        return 'echo request'
    return ''
