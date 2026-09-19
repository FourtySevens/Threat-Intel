import psycopg2
import select
import json
import subprocess

def notif_listen():
    conn = psycopg2.connect("host=localhost dbname=threatintel user=ti_user")
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

    cur = conn.cursor()
    cur.execute("LISTEN updates")
    print("waiting..")

    while True:
        if select.select([conn], [], [], 5) == ([], [], []):
            print("Still wating")
        else:
            conn.poll()
            while conn.notifies:
                notify = conn.notifies.pop(0)
                print(f"  Channel: {notify.channel}")
                print(f"  Payload: {notify.payload}")
                data = json.loads(notify.payload)
                handle_notif(data)

def handle_notif(data):
    id = data.get('id', 'N/A')
    item_1 = data.get('item_1', 'N/A')
    item_2 = data.get('item_2', 'N/A')
    item_3 = data.get('item_3', 'N/A')
    table = data.get('table', 'N/A')
    
    message = f"New Entry with ID:{id} added to {table} at {item_3}"
    
    print(f"Sending notification: {message}")
    
    subprocess.run([
        "ntfy",
        "publish",
        "test_alerts",
        message
    ])

 
if __name__ == "__main__":
    notif_listen()
