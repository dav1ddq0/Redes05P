import sys, argparse
import device_handler as dh
import myParser

#load the configurable signal_time
slot_time = int(open('./signal_time.txt', 'r').readline())
# load the configurable error_detection
error_detection = open('./config.txt', 'r').readline().replace('\n','')

handler = dh.Device_handler(slot_time, error_detection)
# dicc that func like a launcher to the principal methods
caller ={
        "hub" : lambda args:  handler.create_hub(args[0], args[1], args[2]),
        "host" : lambda args : handler.create_pc(args[0], args[1]),
        "switch" : lambda args: handler.create_switch(args[0], args[1],args[2]),
        "connect": lambda args : handler.setup_connection(args[0],args[1], args[2]),
        "send": lambda args : handler.send(args[0], args[1], args[2]),
        "disconnect": lambda args :  handler.shutdown_connection(args[0], args[1]),
        "mac" : lambda args : handler.setup_mac(args[0], args[1], args[2]),
        "send_frame" : lambda args : handler.setup_send_frame(args[0], args[1],args[2], args[3]),
        "ip" : lambda args : handler.setup_ip(args[0], args[1], args[2], args[3], args[4]),
        "send_packet" : lambda args : handler.send_packet(args[0],args[1],args[2], args[3])
        }

# main :D
def main():
    
    parser = argparse.ArgumentParser(description="Instrucciones del script")
    parser.add_argument('-f', dest='textfile', default=True)
    args = parser.parse_args()
    filename = args.textfile

    f = open(filename, 'r')
    # has un recorrido por cada linea del file.txt
    for line in f.readlines():
        try:
            instruction, args2 = myParser.parse(line)
        except TypeError:
            print("Parse Error wrong sintax")
            return
        try:
            caller[instruction](args2)
        except ValueError:
            print("Excution Error")
            return
    # sigue recorriendo la red luego de leer todas las instrucciones de entrada 
    # para ver si quedo alguna actividad de los host por hacer
    handler.finished_network_transmission()
    
if __name__== "__main__":
    main()
