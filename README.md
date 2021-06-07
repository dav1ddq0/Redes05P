# <center>Informe Redes05P Capa de Red Parte 2</center>
<center>David Orlando De Quesada Oliva C311</center>

<center>Javier Domínguez C312</center>

### Para ejecuar el proyecto:

```
python main.py -f file.txt
```



### Informe :

Cada host y cada router tiene una lista llamada routers donde se van agregando o eliminado las rutas. Para representar la ruta usamos la clase Route definiada:

```
class Route:
    def __init__(self, destination:str, mask:str, gateway:str, interface: int) -> None:
        self.destination = destination
        self.mask = mask
        self.gateway = gateway
        self.interface =interface
```



Esta lista funciona a modo de priority queue donde la prioridad es la cantidad de unos que tenga la mascara en su representación binaria por ejemplo si tuviera una ruta con mask `0.0.0.0` y otra con mask `255.255.255.0` al recorrer la lista aparecería primero la que tiene mask `255.255.255.0`  cuya representación binaria es `11111111111111111111111100000000` teniendo 24 unos en cambio la representación binaria de `0.0.0.0` es `00000000000000000000000000000000` con 0 unos por lo que tiene menor prioridad.

Si se escribe el comando `route add <name> <destination> <mask> <gateway> <interface` se crea una instancia de Route con los parámetros `<destination> <mask> <gateway> <interface>` y se agrega a la lista de routes que tiene el device `<name>` que puede ser tanto un host como un router.

Si se escribe el comando  `route delete <name> <destination> <mask> <gateway> <interface>`  se busca el device con nombre `<name>`  sea un host o un router se busca en su lista de routes la instancia de Route r tal que `r.destination == <destination>  r.mask == mask r.gateway == <gateway> y r.interface == interface` y se elimina r de routes.

Si se escribe el comando `route reset <name>` se busca el device con nombre  `<name>` sea un host o un router y se borran todas las rutas almacenadas en su lista routes :

```
routes.clear()
```



Un router lo representamos con la clase Router. La clase Router tiene como propiedades name que indica el nombre del router una lista la instancia de todos los puertos que tiene dicho router , un diccionario `<port_name: Interface>` que tiene para cada puerto del router la interface correspondiente,  la lista `routes` que representa la tabla de rutas. La interface está representado con la clase Interface que tiene como propiedades la `mac, ip,mask, packets, rframe` que representa el frame que se esta recibiendo, `sframe` que representa el frame que se está enviando, `sframe_pending` que es una cola que representa los frames pendientes que deben enviarse en orden luego que se termine con el que está en sframe, `bit_sending` que en caso que sea distinto de None representa el bit que se está enviando en ese momento por esa interface, `transmitting_time` el tiempo que  lleva enviando un bit por la interface, `transmitting` si se está transmitiendo algo por esa interface, `stopped` si ocurrió una colisión y se detuve el envio por un tiempo, `stopped_time` el tiempo que lleva detenido el envio , `failed_attempts` el número de intentos fallidos que ha tenido el envio de ese bit, `packets` la lista de packet que deben ser enviando por esa interface.

Dado que ahora un paquete puede pasar por varios routers antes de llegar a su host destino le agregamos la propiedad a la clase Packet `ip_connect` que nos dice el ip al  cual tenemos que enviar el frame que contiene el ip_packet luego que haga haga arp para obtener la mac des ,que corresponde al ip `ip_connect` , a la que se va a enviar el frame.

Ahora un paquete se envia solamente desde un host o router si tiene una ruta que enrute con él en caso contrario el paquete no se envia y se envia al host origen un mensaje icmp con payload 3 ( destination host unreachable) . Ahora los host escriben en su file _payload.txt en caso que sea un mensaje icmp (protocol =1) seguido de lo que escribía anteriormente en dependecia de su payload echo reply(0) , destination host unreachable(3) o echo request (8).

 Al hacer ping desde host a un des_ip se envia paquete ip con protocolo icmp y payload =8  igual que cualquier otro paquete lo que con la peculiaridad de que ahora cada 100ms se tiene que vovler a enviar este paquete ip 3 veces más. Para hacer esto tenemos la clase Ping con propiedades remaining_messages, des_ip, remaining_time . Un host tiene una lista de Ping que permite enviar cada 100ms los restantes paquetes ip con protocolo ICMP y  payload =8 que queden producto de un ping. Si un Ping de la lista tiene remaining_messeges = 0 se elimina de la lista pues eso significa que ya se enviaron los 4 mensajes ICMP  con payload =8 al IP especificado en des_ip del Ping.

Los host tienen un campo broadcast que identifca el ip que se considera de broadcast producto de hacer not(mask) or ip. Si el ip des del packet que se quiere mandar coincide con  la dirección de broadcast del host entonces se manda directo el ip packet sin hacer ARPQ  en un frame con mac des =`FFFF`   

En el caso que sea un broadcast el router  no lo propaga

## Ejemplo: 

```
1 create router rt1 3
2 mac rt1:2 AA12
3 ip rt1:2 10.6.122.1 255.255.255.0
4 create host pc1 
5 create host pc2 
6 mac pc1 AA2A
7 ip pc1 10.6.122.2 255.255.255.0
8 route add pc1 10.7.122.0 255.255.255.0 10.6.122.1 1
9 route add pc1 10.7.123.0 255.255.255.0 10.6.122.1 1
10 route add pc1 0.0.0.0 0.0.0.0 0.0.0.0 1
11 route add pc2 10.6.122.0 255.255.255.0 10.7.122.1 1
12 route add pc2 0.0.0.0 0.0.0.0 0.0.0.0 1
13 mac pc2 A2F1
14 mac rt1:1 B2FA
15 ip pc2 10.7.122.2 255.255.255.0
16 ip rt1:1 10.7.122.1 255.255.255.0
17 connect pc1_1 rt1_2
18 connect pc2_1 rt1_1
19 route add rt1 10.7.122.0 255.255.255.0 0.0.0.0 1
20 route add rt1 10.6.122.0 255.255.255.0 0.0.0.0 2
```



Esto crea la siguiende red:

![](/home/davido/Documents/Proyectos/Redes05/Redes05P/images/fig_4_1.png)

Vamos a probar enviar un paquete desde pc1:

```
21 send_packet pc1 10.7.122.2 A
```

primero buscamos el host que corresponde al name pc1

luego buscamos una ruta que enrute con el ip destino  para eso ejecutamos lo siguiente:

```
route = netl.search_match_route(des_ip, host.routes)
```

esto devuelve la primera ruta que enrute con el ip destino en el recorrido de la lista routes usando el siguiente método:

```
def match_route(route:Route, ip):
    andOp = get_and_ip_op(route.mask, ip) 
    return andOp == route.destination

def search_match_route(ip,routes:'list[Route]'):
    for route in routes:
        if match_route(route, ip):
            return route
    return None
```

En este caso como las rutas se guardan en una cola de prioridad donde la prioridad es la cantidad de uno de la máscara la primera ruta que enruta con **10.7.122.2**  es`Route { destination = 10.7.122.0 mask = 255.255.255.0 gateway 10.6.122.1 interface = 1}` por tanto se debe construir un frame con data ip_packet que tenga como mac_des la mac del gateway de la ruta que es **10.6.122.1**, para esto se procede a realizar un arpq con ip_des = **10.6.122.1** al llegar ese frame al router a traves del puerto `rt1_2` que es el que conecta con `pc1_1` y comprobar que la ip de la interface de `rt1_2 ` corresponde con la del arpq le devuelve un arpr a pc1 con la mac de la interface luego que se tiene la mac se procede a enviar el ip_packet mediante un frame con mac origen la mac de pc1 AA2A , mac des la mac de la interface de rt1_2  B2FA y data el ip_packet. Una vez que este frame llega al router mediante el puerto rt1_2 se detecta que es un ip_packet y se procede a buscar la ruta  que enrute con el ip des del ip_packet que es 10.7.122.2 . La primera ruta que enruta con 10.7.122.2.2 es  `Route{destination = 10.7.122.0 mask = 255.255.255.0 gateway = 0.0.0.0  interface = 1}` por lo que se envía por el puerto `rt1_1` al gateway **0.0.0.0**  pero como el gateway es **0.0.0.0** quiere decir que se envia directo por lo que la mac del ip des que tiene que buscar es la que corresponde con el ip **10.7.122.2** , se hace un arpq desde la interface de `rt1_1` buscando la mac que corresponda con el ip **10.7.122.2** al llegar el arpq a pc2 este responde con un arpr y le envia la mac y al llegar el arpr a la interface de `rt1_1` se procede a enviar el ip_packet con mac origen **AA12** que es la de la interface de `rt1_1` y mac des **A2F1** que es la de pc2 al llegar el packet a pc2 se escribe en el payload la información correspondiente:

```
10.6.122.2 A 
```

 

