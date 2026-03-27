from backend.models import MatingEvent

print('Testing MatingEvent...')
try:
    events = MatingEvent.get_all()
    print(f'Found {len(events)} events')
    if events:
        print('Event details:')
        for i, event in enumerate(events):
            print(f'Event {i+1}:')
            print(f'  ID: {event[0]}')
            print(f'  Camera ID: {event[1]}')
            print(f'  Pen ID: {event[2]}')
            print(f'  Barn ID: {event[3]}')
            print(f'  Start Time: {event[4]}')
            print(f'  End Time: {event[5]}')
            print(f'  Duration: {event[6]}s')
            print(f'  Avg Confidence: {event[7]:.2f}')
            print(f'  Max Confidence: {event[8]:.2f}')
            print(f'  Screenshot1: {event[9]}')
            print(f'  Screenshot2: {event[10]}')
            print(f'  Screenshot3: {event[11]}')
            print(f'  Created At: {event[12]}')
            print()
except Exception as e:
    print('Error:', e)
