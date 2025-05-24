from threading import Thread, Lock
import requests
from queue import Queue
from colorama import Fore, Style, init

UNDERLINE = '\033[4m'
init(autoreset=True)

class Share:
    q = Queue()
    ends = []
    lock = Lock()
    datas = {}
    ranking_serieA = {}

class Game:
    def __init__(self, team_1, team_2, team_1_score, team_2_score):
        self.team_1 = team_1
        self.team_2 = team_2
        self.team_1_score = team_1_score
        self.team_2_score = team_2_score

def Producer(p_id, url, year):
    response = requests.get(url)
    if response.status_code == 200:
        response = response.content.decode().splitlines()[1:]
        for line in response:
            line = line.split(",")
            if Share.ends[p_id]:
                break
            with Share.lock:
                Share.q.put((year, line))
    Share.ends[p_id] = True

def Consumer():
    while not all(Share.ends) or not Share.q.empty():
        if not Share.q.empty():
            year, line = Share.q.get()
            try:
                home = line[2]
                away = line[3]
                home_score = int(line[4])
                away_score = int(line[5])
            except (IndexError, ValueError):
                continue

            with Share.lock:
                if home not in Share.datas:
                    Share.datas[home] = {}
                if year not in Share.datas[home]:
                    Share.datas[home][year] = {"punti": 0, "vittorie": 0, "sconfitte": 0, "pareggi": 0, "goal_fatti": 0, "goal_subiti": 0, "games": []}

                if away not in Share.datas:
                    Share.datas[away] = {}
                if year not in Share.datas[away]:
                    Share.datas[away][year] = {"punti": 0, "vittorie": 0, "sconfitte": 0, "pareggi": 0, "goal_fatti": 0, "goal_subiti": 0, "games": []}

                Share.datas[home][year]["goal_fatti"] += home_score
                Share.datas[home][year]["goal_subiti"] += away_score
                Share.datas[away][year]["goal_fatti"] += away_score
                Share.datas[away][year]["goal_subiti"] += home_score

                if home_score > away_score:
                    Share.datas[home][year]["punti"] += 3
                    Share.datas[home][year]["vittorie"] += 1
                    Share.datas[away][year]["sconfitte"] += 1
                elif home_score == away_score:
                    Share.datas[home][year]["punti"] += 1
                    Share.datas[home][year]["pareggi"] += 1
                    Share.datas[away][year]["punti"] += 1
                    Share.datas[away][year]["pareggi"] += 1
                else:
                    Share.datas[away][year]["punti"] += 3
                    Share.datas[away][year]["vittorie"] += 1
                    Share.datas[home][year]["sconfitte"] += 1

                game = Game(home, away, home_score, away_score)
                Share.datas[home][year]["games"].append(game)
                Share.datas[away][year]["games"].append(game)

if __name__ == "__main__":
    threads = []
    yi = int(input("Anno di inizio (min: 2003): "))
    yf = int(input("Anno di fine (max: 2017): "))

    year_range = list(range(yi, yf + 1))
    Share.ends = [False for _ in year_range]

    for i, year in enumerate(year_range):
        url = f"https://raw.githubusercontent.com/TdP-datasets/serie_a/refs/heads/master/file%20originali/I1%20({year}).csv"
        producer = Thread(target=Producer, args=(i, url, year))
        producer.start()
        threads.append(producer)

    consumer = Thread(target=Consumer)
    consumer.start()

    for t in threads:
        t.join()
    consumer.join()

    for team, value in Share.datas.items():
        for year, datas in value.items():
            if year not in Share.ranking_serieA:
                Share.ranking_serieA[year] = []
            Share.ranking_serieA[year].append((
                team,
                datas['punti'],
                datas['vittorie'],
                datas['pareggi'],
                datas['sconfitte'],
                datas['goal_fatti'],
                datas['goal_subiti']
            ))

    Share.ranking_serieA = sorted(Share.ranking_serieA.items())

    for year, ranking in Share.ranking_serieA:
        ranking.sort(key=lambda x: (x[1], x[5] - x[6], x[5]), reverse=True)

        print(f"\n{Fore.CYAN + Style.BRIGHT}Classifica Serie A - {year}{Style.RESET_ALL}")
        print(f"{'Pos':<4}{'Squadra':<25}{'Punti':<8}{'V':<4}{'N':<4}{'P':<4}{'GF':<5}{'GS':<5}{'Diff':<5}")
        for i, (team, punti, vittorie, pareggi, sconfitte, gf, gs) in enumerate(ranking, start=1):
            diff = gf - gs
            print(f"{i:<4}{team:<25}{punti:<8}{vittorie:<4}{pareggi:<4}{sconfitte:<4}{gf:<5}{gs:<5}{diff:<5}")

    while True:
        team = input("\nDi quale squadra vuoi vedere i dati? (digita 'exit' per uscire): ")
        if team.lower() in ("exit", "q", "esci"):
            print("Uscita dal programma.")
            break

        try:
            year = int(input("Anno: "))
        except ValueError:
            print(f"{Fore.RED}Inserisci un anno valido.{Style.RESET_ALL}")
            continue

        if team in Share.datas and year in Share.datas[team]:
            print(f"\n{Fore.YELLOW + Style.BRIGHT}Dati relativi a {team.upper()}{Style.RESET_ALL}")
            print(f"Punti       : {Share.datas[team][year]['punti']}")
            print(f"Vittorie    : {Share.datas[team][year]['vittorie']}")
            print(f"Pareggi     : {Share.datas[team][year]['pareggi']}")
            print(f"Sconfitte   : {Share.datas[team][year]['sconfitte']}")
            print(f"Goal Fatti  : {Share.datas[team][year]['goal_fatti']}")
            print(f"Goal Subiti : {Share.datas[team][year]['goal_subiti']}")

            for game in Share.datas[team][year]['games']:
                winner = None
                if game.team_1_score > game.team_2_score:
                    winner = game.team_1
                elif game.team_2_score > game.team_1_score:
                    winner = game.team_2

                def format_team(t):
                    style = ""
                    if t == winner:
                        style += Fore.GREEN + Style.BRIGHT
                    if t == team:
                        style += UNDERLINE
                    return f"{style}{t}{Style.RESET_ALL}"

                home = format_team(game.team_1)
                away = format_team(game.team_2)

                print(f"  Partita: {home} - {away}  {game.team_1_score} - {game.team_2_score}")

        else:
            print(f"{Fore.RED + Style.BRIGHT}Dati non disponibili per {team} nel {year}{Style.RESET_ALL}")
