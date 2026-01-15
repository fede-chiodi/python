from lib.socketClasses import SocketServer, SocketClient

rooms = dict()
users = list()

class Room():
    def __init__(self, room_name):
        self.room_name = room_name
        self.users_list = []

    def join_room(self, user, user_client):
        if user not in self.users_list:
            self.users_list.append((user, user_client))

    def leave_room(self, user_nick):
        for user in self.users_list:
            if user_nick == user[0]:
                self.users_list.remove(user)

class Chat(SocketClient):
    def __init__(self, conn, addr, clients):
        super().__init__(conn, addr, clients)
        self.nickname = ""
        self.room_name = ""
        self.hist = []
        self.blocked_users = []
        self.send("=== Benvenuto nella chat! ===\r\n")
        self.show_menu()

    def manage(self, msg):
        parts = msg.strip().split(' ')
        if not parts:
            self.send("Comando non riconosciuto. Digita /help per vedere tutti i comandi.\r\n")
            return
        cmd = parts[0]
        match cmd:
            case "/help":
                self.show_menu()

            case "/nick":
                if len(parts) < 2:
                    self.send("Errore: devi specificare un nickname: /nick <nickname>.\r\n")
                    return
                if parts[1] not in users:
                    self.nickname = parts[1]
                    users.append((self.nickname, self))
                else:
                    self.send("❌ Utente con stesso nickname già registrato \r\n")
                  
            case "/join":
                if len(parts) < 2:
                    self.send("❌ Devi specificare una stanza: /join <stanza>\r\n")
                    return
                if self.nickname == "":
                    self.send("❌ Devi registrarti prima con /nick <tuo_nickname>.\r\n")
                    return
                room_name = parts[1]
                self.room_name = room_name
                if room_name not in rooms:
                    rooms[room_name] = Room(room_name)

                rooms[room_name].join_room(self.nickname, self)

                self.send(f"🏠 {self.nickname} entrato nella stanza '{room_name}'!\r\n")

            case "/leave":
                if len(parts) < 2:
                    self.send("❌ Devi specificare una stanza: /join <stanza>\r\n")
                    return
            
                room_name = parts[1]
                rooms[room_name].leave_room(self.nickname)
                self.room_name = ""
                self.send(f"🏠❌ {self.nickname}, hai abbandonato la stanza '{room_name}'!\r\n")

            case "/hist":
                counter = 0
                self.send("== MESSAGE HISTORY ==\r\n")
                for msg in self.hist:
                    counter += 1
                    self.send(f"Messaggio {counter}: {msg[0]} - {msg[1]}\r\n")

            case "/msg":
                if not self.nickname:
                    self.send("❌ Devi registrarti prima con /nick <tuo_nickname>.\r\n")
                    return
                if not self.room_name:
                    self.send("❌ Devi prima entrare in una stanza con /join <stanza>.\r\n")
                    return
                if len(parts) < 2:
                    self.send("❌ Devi scrivere un messaggio.\r\n")
                    return
                message = ' '.join(parts[1:])
                self.broadcast_message(message)

            case "/send":
                if len(parts) < 3:
                    self.send("❌ Sintassi corretta: /send <utente> <messaggio>\r\n")
                    return
                target_nickname = parts[1]
                message = ' '.join(parts[2:])
                self.send_private_message(target_nickname, message)

            case "/block":
                if len(parts) < 2:
                    self.send("❌ Sintassi corretta: /block <user>\r\n")
                    return
                target_user = parts[1]
                self.block_user(target_user)

            case "/unblock":
                if len(parts) < 2:
                    self.send("❌ Sintassi corretta: /unblock <user>\r\n")
                    return
                target_user = parts[1]
                self.unblock_user(target_user)

            case "/blocked":
                if not self.blocked_users:
                    self.send("📃 Non hai bloccato nessun utente.\r\n")
                else:
                    self.send("📃 Utenti bloccati:\r\n")
                    for nick, _ in self.blocked_users:
                        self.send(f"- {nick}\r\n")


    def broadcast_message(self, msg):
        if self.room_name not in rooms:
            self.send("❌ Non sei in nessuna stanza.\r\n")
            return

        for nickname, client in rooms[self.room_name].users_list:
            if nickname != self.nickname:
                if any(nick_block == nickname for nick_block, _ in self.blocked_users):
                    continue
                if any(nick_block == self.nickname for nick_block, _ in client.blocked_users):
                    continue
                client.send(f"[Broadcast] {self.nickname}: {msg}\r\n")
        self.send(f"[Tu -> Tutti]: {msg}\r\n")
        self.hist.append(("[BROADCAST]", msg))

    def send_private_message(self, user_nickname, msg):
        for nickname, client in users:
            if nickname == user_nickname:
                if any(nick_block == nickname for nick_block, _ in self.blocked_users):
                    self.send(f"🚫 Utente '{nickname}' bloccato, non puoi inviare messaggi.\r\n")
                    return
                if any(nick_block == self.nickname for nick_block, _ in client.blocked_users):
                    self.send(f"🚫 L'utente '{nickname}' ti ha bloccato, non puoi inviare messaggi.\r\n")
                    return
                client.send(f"[Privato] {self.nickname}: {msg}\r\n")
                self.send(f"[Tu -> {nickname}]: {msg}\r\n")
                self.hist.append(("[PRIVATO]", msg))
                return

        self.send(f"❌ Utente '{user_nickname}' non trovato.\r\n")


    def block_user(self, user_nickname):
        for nick, user in users:
            if nick == user_nickname:
                if (nick, user) not in self.blocked_users:
                    self.blocked_users.append((nick, user))
                    self.send(f"🚫 Utente '{user_nickname}' bloccato.\r\n")
                else:
                    self.send(f"⚠️ Utente '{user_nickname}' già bloccato.\r\n")
                return

        self.send(f"❌ Utente '{user_nickname}' non trovato.\r\n")

    def unblock_user(self, user_nickname):
        for blocked in self.blocked_users:
            nick, user = blocked
            if nick == user_nickname:
                self.blocked_users.remove(blocked)
                self.send(f"✅ Utente '{user_nickname}' sbloccato.\r\n")
                return

        self.send(f"❌ L'utente '{user_nickname}' non è nella lista dei bloccati.\r\n")

    def show_menu(self):
        self.send("Comandi disponibili\r\n")
        self.send("/help                        - Mostra questo menu\r\n")
        self.send("/nick <nickname>             - Registrati con un nickname\r\n")
        self.send("/join <stanza>               - Partecipa ad una stanza nel server\r\n")
        self.send("/leave <stanza>              - Abbandona una stanza\r\n")
        self.send("/msg <message>               - Invia messaggio broadcast alla stanza\r\n")
        self.send("/send <user> <message>       - Messaggio privato da utente a utente\r\n")
        self.send("/hist                        - Mostra la history dei messaggi di un utente\r\n")
        self.send("/block <user>                - Blocca un utente\r\n")
        self.send("/unblock <user>              - Sblocca un utente\r\n")
        self.send("/blocked                     - Lista degli utenti boccati\r\n")


if __name__ == "__main__":
    server = SocketServer("0.0.0.0", 50000, Chat)
    server.activate()
