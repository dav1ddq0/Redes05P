# <center>Informe Redes05P Capa de Red Parte 2</center>
<center>David Orlando De Quesada Oliva C311</center>

<center>Javier Domínguez C312</center>

### Para ejecuar el proyecto:

```
python main.py -f file.txt
```



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

Si se escribe el comando 

