from lib.socketClasses import SocketClient, SocketServer
import time
import threading

riders = {
    "R101": "MOTO_45",
    "R102": "BICI_12",
    "R103": "AUTO_09",
    "R104": "SCOOTER_23",
    "R105": "FURGONE_34",
    "R106": "EBIKE_17",
    "R107": "MOTO_88",
    "R108": "BICI_56",
    "R109": "AUTO_42",
    "R110": "DRONE_11",
    "R111": "SCOOTER_07",
    "R112": "FURGONE_99",
    "R113": "EBIKE_64",
    "R114": "MONOPATTINO_21",
    "R115": "AUTO_30"
}

pending_orders = ["1014", "1015", "1016"]
orders = dict()

def add_order_periodically():
    order_id = 1017
    while True:
        time.sleep(30)
        pending_orders.append(str(order_id))
        print(f"Nuovo ordine aggiunto: {order_id}")
        order_id += 1

threading.Thread(target=add_order_periodically, daemon=True).start()

class Logistics(SocketClient):
    def __init__(self, conn, addr, clients):
        super().__init__(conn, addr, clients)
        self.send("=== WELCOME TO THE LOGISTIC SERVER ===\r\n")
        self.commands_list()
        self.rider_isAuth = False
        self.rider_code = ""
        self.rider_vehicle = ""
        self.rider_isFree = True
        self.current_order_code = ""
        self.current_order_status = ""
        self.orders_managed = list()

    def manage(self, msg):
        parts = msg.strip().split(" ")
        cmd = parts[0]
        match cmd:
            case "/login":
                self.auth_function(parts[1], parts[2])
            case "/order":
                if self.rider_isAuth:
                    self.take_in_charge_order()
                else:
                    self.send("Please, authenticate first\r\n\n")
            case "/update":
                if self.rider_isAuth:
                    if not self.rider_isFree:
                        new_status = " ".join(parts[1:])
                        self.update_order_status(new_status)
                    else:
                        self.send(f"Il rider {self.rider_code} non è occupato in nessun ordine\r\n\n")
                else:
                    self.send("Please, authenticate first\r\n\n")
            case "/history":
                if self.rider_isAuth:
                    self.show_current_order_history()
                else:
                    self.send("Please, authenticate first\r\n\n")
            case "/summary":
                if self.rider_isAuth:
                    self.show_orders_summary()
                else:
                    self.send("Please, authenticate first\r\n\n")


    def auth_function(self, rider_code, vehicle_code):
        if rider_code not in riders or riders[rider_code] != vehicle_code:
            self.send("Authentication Denied, pleas retry\r\n\n")
        else:
            self.send(f"Authentication as {rider_code} Successfull\r\n\n")
            self.rider_isAuth = True
            self.rider_code = rider_code
            self.rider_vehicle = vehicle_code

    def take_in_charge_order(self):
        if self.rider_isFree and pending_orders:
            order_date = time.localtime()
            order_code = pending_orders.pop(0)
            self.current_order_code = order_code
            self.current_order_status = "preso in carico"
            self.orders_managed.append((self.current_order_code, self.current_order_status, order_date))
            orders[self.current_order_code] = [(self.current_order_status, order_date)]
            self.send(f"Il rider {self.rider_code} ha preso in carico l'ordine {self.current_order_code} il {order_date.tm_mday}-{order_date.tm_mon}-{order_date.tm_year} alle {order_date.tm_hour}:{order_date.tm_min} \r\n\n")
            self.rider_isFree = False
        else:
            self.send(f"Il rider {self.rider_code} sta gestendo già l'ordine {self.current_order_code}\r\n\n")

    def update_order_status(self, new_status):
        self.current_order_status = new_status
        order_date = time.localtime()
        
        orders[self.current_order_code].append((self.current_order_status, order_date))

        for i, order in enumerate(self.orders_managed):
            if order[0] == self.current_order_code:
                self.orders_managed[i] = (order[0], self.current_order_status, order_date)

        """ rubrica = [
                dato[0] dato[1] dato[2] dato[3]
                (nome, cognome, email, cell) ---> indice 0
                (nome, cognome, email, cell) ---> indice 1
                (nome, cognome, email, cell) ---> indice 2
            ]"""

        self.send(f"Ordine {self.current_order_code} aggiornato a '{self.current_order_status}' il {order_date.tm_mday}-{order_date.tm_mon}-{order_date.tm_year} alle {order_date.tm_hour}:{order_date.tm_min}\r\n\n")
        
        if self.current_order_status == "consegnato":
            self.rider_isFree = True
            self.send(f"Il rider {self.rider_code} ha consegnato l'ordine {self.current_order_code} e ora può gestire nuovi ordini\r\n\n")

    def show_current_order_history(self):
        self.send(f"=== HISTORY DELL'ORDINE {self.current_order_code} ===\r\n")
        for status, date in orders[self.current_order_code]:
            self.send(f"{status}, {date.tm_mday}-{date.tm_mon}-{date.tm_year} ({date.tm_hour}:{date.tm_min})\r\n")

    def show_orders_summary(self):
        self.send(f"=== REGISTRO ORDINI DEL RIDER {self.rider_code} ===\r\n")
        for order, status, date in self.orders_managed:
            self.send(f"Ordine {order}: {status}, {date.tm_mday}-{date.tm_mon}-{date.tm_year} ({date.tm_hour}:{date.tm_min})\r\n")

    def commands_list(self):
        self.send("Comandi disponibili\r\n")
        self.send("/login <rider_code> <vehicle_code>   - Autenticazione del rider\r\n")
        self.send("/order                               - Assegnazione di un ordine al rider\r\n")
        self.send("/update <status>                     - Modifica dello stato dell'ordine corrente\r\n")
        self.send("/history                             - Mostra la history di tutti gli stati e dei corrispettivi orari dell'ordine corrente (anche se appena stato consegnato)\r\n")
        self.send("/summary                             - Mostra il registro di tutti gli ordini (compreso quello corrente)\r\n\n")

if __name__ == "__main__":
    server = SocketServer("0.0.0.0", 50000, Logistics)
    server.activate()