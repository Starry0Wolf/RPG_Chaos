from Cogs.start import connect
from Cogs.Commands import handle_command

def main():
    sock = connect()
    tasksHuman = []
    
    while True:
        data = sock.recv(2048).decode()
        if data.startswith('PING'):
            sock.send("PONG :tmi.twitch.tv\r\n".encode())
            continue

        if 'PRIVMSG' not in data:
            continue

        # Extract channel from message
        channel = data.split('PRIVMSG')[1].split(':', 1)[0].strip().split(' ')[0]
        user = data.split('!', 1)[0][1:]
        msg = data.split('PRIVMSG', 1)[1].split(':', 1)[1].strip()
        print(f"{user}@{channel}: {msg}")

        # Handle all commands through the command handler
        handle_command(user, channel, msg, sock, tasksHuman)

if __name__ == "__main__":
    print("Starting bot. Press Ctrl+C to stop.")
    main()
