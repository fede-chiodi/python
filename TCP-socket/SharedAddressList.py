from lib.socketClasses import SocketServer, SocketClient

users = list()

class User():
    def __init__(self, name, surname, email, cell):
        self.name = name
        self.surname = surname
        self.email = email
        self.cell = cell

    def change_cell_email(self, newcell, newmail):
        self.cell = newcell
        self.email = newmail

class Rubrica(SocketClient):
    def __init__(self, conn, addr, clients):
        super().__init__(conn, addr, clients)
        self.show_menu()

    def manage(self, msg):
        parts = msg.strip().split(' ')
        if not parts:
            self.send("Comando non riconosciuto. Digita /help per vedere tutti i comandi.\r\n")
            return
        cmd = parts[0]
        match cmd:
            case "/add":
                user_details = parts[1].split(',')
                self.add_user(user_details[0], user_details[1], user_details[2], user_details[3])
            case "/mod":
                user_details = parts[1].split(',')
                self.mod_user(user_details[0], user_details[1], user_details[2], user_details[3])  
            case "/list":
                self.list_users()     
            case "/search":
                params = parts[1:]
                self.search_info(params)  
            case "/del":
                user_details = parts[1].split(',')
                self.delete_user(user_details[0], user_details[1])
            
    def add_user(self, name, surname, email, cell):
        users.append(User(name, surname, email, cell))
        self.send(f"✅ Utente {name} {surname} aggiunto in rubrica ({email}, {cell})\r\n\n")

    def mod_user(self, name, surname, email, cell):
        for user in users:
            if user.name == name and user.surname == surname:
                user.change_cell_email(cell, email)
                self.send(f"✅ Modifica apportata all'utente {name} {surname} ({email}, {cell})\r\n\n")

    def list_users(self):
        if not users:
            self.send("Rubrica vuota.\r\n")
            return

        header = (
            "+----+------------+------------+--------------------------------+--------------+\r\n"
            "| #  | Nome       | Cognome    | Email                          | Cellulare    |\r\n"
            "+----+------------+------------+--------------------------------+--------------+\r\n"
        )

        rows = ""
        for i, user in enumerate(users, start=1):
            rows += (
                f"| {i:<2} | "
                f"{user.name:<10} | "
                f"{user.surname:<10} | "
                f"{user.email:<30} | "
                f"{user.cell:<12} |\r\n"
            )

        footer = "+----+------------+------------+--------------------------+--------------+\r\n"

        self.send(header + rows + footer)

    def search_info(self, params):
        if not users:
            self.send("Rubrica vuota.\r\n")
            return
        
        criteria = {}

        for p in params:
            if '=' in p:
                key, value = p.split('=', 1)
                criteria[key.lower()] = value

        if not criteria:
            self.send("⚠️ Nessun criterio di ricerca fornito.\r\n")
            return
        
        found = False
        for user in users:
            # * con questa condizione se viene chiesto di effettuare la ricerca su un parametro, viene controllato il campo specifico in criteria e deve corrispondere.
            # * altrimenti, nel caso non viene chiesto di controllare il campo, si passa avanti
            # * True - True/False (True) --> non analizzato, campo non presente tra i criteri di ricerca
            # * False - True (True) ---> campo presente tra i criteri di ricerca, corrisponde anche il valore
            # * False - False (False) ---> campo presente tra i criteri di ricerca, non corrisponde il valore 
            if (
                ('name' not in criteria or user.name == criteria['name']) and
                ('surname' not in criteria or user.surname == criteria['surname']) and
                ('email' not in criteria or user.email == criteria['email']) and
                ('cell' not in criteria or user.cell == criteria['cell'])
            ):
                self.send( f"🔍 {user.name} {user.surname} - {user.email} - {user.cell}\r\n")
                found = True
        
        if not found:
            self.send("❌ Nessun utente trovato.\r\n")

    def delete_user(self, name, surname):
        if not users:
            self.send("Rubrica vuota.\r\n")
            return
        for user in users:
            if user.name == name and user.surname == surname:
                self.send(f"✅ Utente {user.name} {user.surname} eliminato dalla rubrica\r\n")
                users.remove(user)

    def show_menu(self):
        menu = [
            ("/add <name>,<surname>,<email>,<cell>", "Aggiungi utente alla Rubrica"),
            ("/mod <name>,<surname>,<email>,<cell>", "Modifica utente della Rubrica"),
            ("/list", "Lista utenti della Rubrica"),
            ("/search <name>:<s_name> <surname>:<s_surnmame> <email>:<s_email> <cell>:<s_cell>", ""),
            ("/del <name>,<surname>", "Rimuovi un utente dalla rubrica")
        ]

        self.send("Comandi disponibili:\r\n")
        max_len = max(len(cmd) for cmd, desc in menu)
        for cmd, desc in menu:
            self.send(f"{cmd.ljust(max_len)}  - {desc}\r\n")


if __name__ == "__main__":
    server = SocketServer("0.0.0.0", 50000, Rubrica)
    server.activate()
