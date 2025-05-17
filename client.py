import socket

HOST = '127.0.0.1'
PORT = 12345

def start_client():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))
    print(f"Connected to server at {HOST}:{PORT}")

    try:
        while True:
            # Receive message from the server
            server_message = client.recv(1024).decode('utf-8')
            print(f"Server: {server_message}")

            if "Type 'LOGIN' to log in or 'REGISTER'" in server_message:
                action = input("Enter 'LOGIN' or 'REGISTER': ").strip().upper()
                client.send(action.encode('utf-8'))

            elif "Choose a username:" in server_message:
                username = input("Enter your username: ").strip()
                client.send(username.encode('utf-8'))

            elif "Choose a password:" in server_message:
                password = input("Enter your password: ").strip()
                client.send(password.encode('utf-8'))

            elif "Enter your username:" in server_message:
                username = input("Enter your username: ").strip()
                client.send(username.encode('utf-8'))

            elif "Enter your password:" in server_message:
                password = input("Enter your password: ").strip()
                client.send(password.encode('utf-8'))

            elif "Invalid credentials" in server_message:
                print("Invalid credentials. Try again.")
                continue

            elif "Username already exists" in server_message:
                print("This username is already taken. Try again.")
                continue

            elif "Registration successful" in server_message:
                print("Registration was successful. Please log in to continue.")
                continue

            elif "Login successful" in server_message:
                print("Login successful! You are now authenticated.")
                break

            else:
                print(f"Server -in auth- : {server_message}")
                continue

        # Gameplay loop (after successful authentication)
        while True:
            server_message = client.recv(1024).decode('utf-8')
            print(f"Server: {server_message}")


            if "Your turn" in server_message:
                command = input("Enter your action (PLAY_CARD <index>, DRAW_CARD, CALL_UNO): ").strip()
                client.send(command.encode('utf-8'))

            elif "Waiting for your turn" in server_message:
                print("Waiting for other players...")

            elif "Game over" in server_message:
                print(server_message)
                break

            elif "Invalid command" in server_message or "Invalid card" in server_message:
                print(f"Server: {server_message}")
                print("Try again during your turn.")

            elif "calls UNO!" in server_message or "played" in server_message:
                print(server_message)

            else:
                print(f"Unexpected message -in game loop-: {server_message}")


    except ConnectionError:
        print("Connection lost to the server.")
    finally:
        client.close()

if __name__ == "__main__":
    start_client()
