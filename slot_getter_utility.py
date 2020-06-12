from session import Session
from slot_getter import SlotGetter
import time
import json


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Please, enter login and password to print the slots, if necesssary add an interval as the third parameter.')
    parser.add_argument('--login', help='User login')
    parser.add_argument('--password', help='User password')
    parser.add_argument('--fulfilment_type', default='DELIVERY', help='Fulfilment type')
    parser.add_argument('--postcode', default='E14 3TJ', help='Post code')
    parser.add_argument('--interval', type=int, default=15, help='Interval to check available slots (in minutes)')

    args = parser.parse_args()

    cnt = 0

    while True:
        cnt += 1

        my_session = Session(args.login, args.password)

        my_slot_getter = SlotGetter(session=my_session, fulfilment_type=args.fulfilment_type, postcode=args.postcode)
        available_slots = my_slot_getter.get_available_slots_full()

        print(f'------ Attempt number {cnt} --------------')

        if len(available_slots) == 0:
            time.sleep(args.interval*60)
        else:
            print(json.dumps(available_slots,indent=2))
            break
