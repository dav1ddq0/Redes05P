caller ={
        "create" : lambda args, time : create_parse(args, time) ,
        "connect" : lambda args, time : connect_parse(args, time),
        "send" : lambda args, time : send_parse(args, time),
        "disconnect" : lambda args, time :  disconnect_parse(args, time),
        "send_frame" : lambda args, time : send_frame_parse(args, time),
        "mac" : lambda args, time : mac_parse(args, time),
        "ip" : lambda args, time : ip_parse(args, time),
        "send_packet" : lambda args, time : send_packet_parse(args, time),
        "route": lambda args, time: route_parser(args, time),
        "ping" : lambda args, time: ping_parser(args, time)
        }



# parse de linne of the file
def parse(line : str):
    #remove the line jump
    line = line.strip()
    line = line.replace('\n', '')
    #divide the line in tokens
    codes = line.split(' ')

    try :
        instruction_time = int(codes[0])
    except ValueError:
        print("Invalid parameter")

    codes = codes[1:]

    if codes[0] not in caller.keys():
        print(f"{codes[0]} is invalid command")
        return
    else:
        return caller[codes[0]](codes, instruction_time)

def __check_binary(string):
    s = set(string)
    p = {'0' , '1'}

    if s == p or s == {'0'} or s == {'1'}:
        return True

    return False

def create_parse(args : list, time: int):
    if args[1] == "hub":
        ports_amount = 0
        try :
            ports_amount = int(args[3])
        except ValueError:
            print("Invalid parameter")
        if len(args) == 4:
                # hub,name,ports_amount,time
                return args[1], [args[2], ports_amount, time]
        else: 
            print("Invalid amount of arguments")

        
    elif args[1] == "host":
        if len(args) == 3:
            return args[1], [args[2], time]
    elif args[1] == "switch":
        ports_amount = 0
        try:
            ports_amount = int(args[3])
        except ValueError:
            print("Invalid parameter")
        if len(args) == 4:
            return args[1], [args[2], ports_amount, time]
        else:
            print("Invalid amount of arguments")
    elif args[1] =="router":
        ports_amount = 0
        try:
            ports_amount = int(args[3])
        except ValueError:
            print("Invalid parameter")
        if len(args) == 4:
            return args[1], [args[2], ports_amount, time]
        else : print("Invalid amount of arguments")
    else:
        print("invalida create command")


def mac_parse(args: list, time:int):
    if len(args) == 3:
        t = args[1]
        host = None
        interface = None
        if ':' in t:
            host,interface = t.split(':')
        else:
            host = t
        if interface=='' or interface == None:
            interface = 1
        else:
            interface = int(interface)            
        return args[0], [host, interface, args[2], time]

    else:
        print("Invalid amount of arguments")

def send_frame_parse(args: list, time: int):
    if len(args) == 4:
        return args[0], [args[1], args[2], args[3], time]
    else:
        print("Invalid amount of arguments")          

def connect_parse(args: list, time: int):

    if args[1].find('_') != -1 and args[2].find('_') != -1:
            split1 = args[1].split('_')
            split2 = args[2].split('_')
            device1_port = split1[len(split1)-1]
            device2_port = split2[len(split2)-1]

            try:
                device1_port = int(device1_port)
                device2_port = int(device2_port)
            except ValueError:
                print("Invalid parameters")
            
            if len(args) == 3:
                # connect,port1,port2
                return args[0], [args[1], args[2], time]
            else : 
                print("Invalid amount of arguments")
    else:
        print("the name format of the portame is invalid")


def send_parse(args: list, time: int):
    if len(args) == 3:
        if __check_binary(args[2]):
            return args[0], [args[1], args[2], time]
        else : print("The data to send must be a binary code")

# sintax error of insr time disconnect
def disconnect_parse(args: list,time: int):
    if args[1].find('_'):
        _, device_port = args[1].split('_')
            
        try:
            device_port = int(device_port)
        except ValueError:
            print("Invalid parameters")
        if len(args) == 2: 
            # disconnect,port
            return args[0], [args[1], time]
        else : print("Invalid amount of arguments")
    else:
        print("Invalid format")    

def ip_parse(args:list, time:int):
    if len(args) == 4:
        t = args[1]
        host = None
        interface = None
        if ':' in t:
            host,interface = t.split(':')
        else:
            host = t
        if interface=='' or interface == None:
            interface = 1
        else:
            interface = int(interface)            
        return args[0], [host, interface, args[2], args[3], time]
    else:
        print("Invalid amount of arguments")

# send_packet <host> <ip destino> <data>
def send_packet_parse(args:list, time:int):
    if len(args) == 4:
        return args[0], [args[1], args[2], args[3], time]
    else:
        print("Invalid amount of arguments")

def route_parser(args:list, time:int):
    
    if args[1] == "reset" and len(args) == 2:
        return args[1],[args[2], time]
    elif args[1] == 'add':
        interface = 0
        try :
            interface = int(args[6])
        except ValueError:
            print("Invalid parameter")
            return
        return args[1],[args[2],args[3],args[4], args[5], interface, time]
    elif args[1] == "delete":
        interface = 0
        try :
            interface = int(args[6])
        except ValueError:
            print("Invalid parameter")
            return
        return args[1],[args[2],args[3],args[4], args[5], interface, time]

    else:
        print("Invalid amount of arguments")


# <time> ping <host> <ip-address>
def ping_parser(args:list, time:int):
    if len(args) ==3:
        return args[0],[args[1], args[2], time]
    else:
        print("Invalid amount of arguments")