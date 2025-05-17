import socket
import threading
import json
import os
from game_logic import UnoGame

HOST = '127.0.0.1'
PORT = 12345
clients = []
usernames = []

# Game instance and state
uno_game = None
game_active = False

USER_DATA_FILE = 'users_data.json'


def load_user_data():
    if not os.path.exists(USER_DATA_FILE):
        print(f"{USER_DATA_FILE} not found. Creating a new file.")
        return {}
    try:
        with open(USER_DATA_FILE, 'r') as file:
            return json.load(file)
    except (json.JSONDecodeError, IOError):
        print(f"Error reading {USER_DATA_FILE}. Resetting...")
        return {}


def save_user_data(users):
    with open(USER_DATA_FILE, 'w') as file:
        json.dump(users, file, indent=4)


def authenticate_client(client_socket):
    users = load_user_data()
    client_socket.send("Welcome! Type 'LOGIN' to log in or 'REGISTER' to create a new account.".encode('utf-8'))

    while True:
        action = client_socket.recv(1024).decode('utf-8').strip().upper()
        if action == "LOGIN":
            client_socket.send("Enter your username:".encode('utf-8'))
            username = client_socket.recv(1024).decode('utf-8').strip()
            client_socket.send("Enter your password:".encode('utf-8'))
            password = client_socket.recv(1024).decode('utf-8').strip()
            if username in users and users[username]['password'] == password:
                client_socket.send("Login successful!".encode('utf-8'))
                return username
            else:
                client_socket.send("Invalid credentials. Try again.".encode('utf-8'))
        elif action == "REGISTER":
            client_socket.send("Choose a username:".encode('utf-8'))
            username = client_socket.recv(1024).decode('utf-8').strip()
            if username in users:
                client_socket.send("Username already exists. Try again.".encode('utf-8'))
                continue
            client_socket.send("Choose a password:".encode('utf-8'))
            password = client_socket.recv(1024).decode('utf-8').strip()
            users[username] = {"password": password, "wins": 0, "losses": 0}
            save_user_data(users)
            client_socket.send("Registration successful! Please log in.".encode('utf-8'))
        else:
            client_socket.send("Invalid action. Type 'LOGIN' or 'REGISTER'.".encode('utf-8'))


def handle_client(client_socket, address):
    global uno_game, game_active
    print(f"New connection from {address}")
    username = None
    try:
        username = authenticate_client(client_socket)
        print(f"User '{username}' authenticated.")
        clients.append(client_socket)
        usernames.append(username)

        client_socket.send("You are authenticated! Waiting for more players to join...".encode('utf-8'))

        if len(clients) >= 2 and not game_active:
            uno_game = UnoGame(len(clients))
            game_active = True
            broadcast(f"Game started! Initial card: {uno_game.current_card}")
            send_game_state()

        while game_active:
            if uno_game.current_player.player_id == usernames.index(username):
                player = uno_game.players[usernames.index(username)]
                client_socket.send(f"Your turn. Current card: {uno_game.current_card}\nYour hand: {player.hand}".encode('utf-8'))
                command = client_socket.recv(1024).decode('utf-8').strip()
                process_command(client_socket, username, command)
            else:
                client_socket.send("Waiting for your turn...".encode('utf-8'))

    except ConnectionError:
        print(f"Connection with {address} closed.")
    finally:
        client_socket.close()
        if username in usernames:
            clients.remove(client_socket)
            usernames.remove(username)


def broadcast(message, sender_socket=None):
    for client in clients:
        if client != sender_socket:
            try:
                client.send(message.encode('utf-8'))
            except ConnectionError:
                clients.remove(client)


def send_game_state():
    for client, username in zip(clients, usernames):
        player = uno_game.players[usernames.index(username)]
        client.send(f"Game State:\nCurrent card: {uno_game.current_card}\nYour hand: {player.hand}\n".encode('utf-8'))


def process_command(client_socket, username, command):
    global uno_game, game_active
    player_index = usernames.index(username)

    if command.startswith("PLAY_CARD"):
        try:
            card_index = int(command.split()[1])
            uno_game.play(player=player_index, card=card_index)
            broadcast(f"{username} played {uno_game.current_card}.")
            check_game_over()
            send_game_state()
        except (ValueError, IndexError):
            client_socket.send("Invalid card. Try again.".encode('utf-8'))

    elif command == "DRAW_CARD":
        uno_game.play(player=player_index, card=None)
        broadcast(f"{username} drew a card.")
        send_game_state()

    elif command == "CALL_UNO":
        player = uno_game.players[player_index]
        if len(player.hand) == 1:
            broadcast(f"{username} calls UNO!")
        else:
            uno_game._pick_up(player, 2)
            client_socket.send("Failed to call UNO! Penalty applied.".encode('utf-8'))
        send_game_state()

    else:
        client_socket.send("Invalid command. Please try again.".encode('utf-8'))


def check_game_over():
    if not uno_game.is_active:
        winner = uno_game.winner
        broadcast(f"Game over! {winner} wins!")
        global game_active
        game_active = False


def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"Server started on {HOST}:{PORT}")

    while True:
        client_socket, address = server.accept()
        thread = threading.Thread(target=handle_client, args=(client_socket, address))
        thread.start()


if __name__ == "__main__":
    start_server()
