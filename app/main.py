from app.utils import Session, Slot
import time
import json
from datetime import datetime

POSTCODE = 'EC1M 6EB' # 'E14 3TJ'
FULFILMENT_TYPE = 'DELIVERY'
REQUEST_INTERVAL = 15
BRANCH_ID = 199 # 753

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Please, enter login and password to print the slots, '
                                                 'if necesssary add an interval as the third parameter.')
    parser.add_argument('--login', help='User login')
    parser.add_argument('--password', help='User password')
    parser.add_argument('--fulfilment_type', default=FULFILMENT_TYPE, help='Fulfilment type')
    parser.add_argument('--postcode', default=POSTCODE, help='Post code')
    parser.add_argument('--interval', type=int, default=REQUEST_INTERVAL, help='Interval to check available slots(min)')

    args = parser.parse_args()

    cnt = 0

    while True:
        cnt += 1

        session = Session(args.login, args.password)

        slot = Slot(session=session, fulfilment_type=args.fulfilment_type, postcode=args.postcode)

        start_date, end_date = slot.get_current_slot()

        # if we already have a booked slot then nothing
        if start_date and end_date:
            print(f'The slot "{start_date} - {end_date}" has already been booked')
        else:
            available_slots = slot.get_available_slots()

            print(f'------ Attempt number {cnt} --------------')

            if not available_slots:
                time.sleep(args.interval*60)
            else:
                print(json.dumps(available_slots, indent=2))

                # we book the first available slot
                for cur_slot in available_slots.values():
                    start_date = cur_slot['startDateTime']
                    end_date = cur_slot['endDateTime']

                    print(f'---------------- BOOKING ATTEMPT FOR THE SLOT "{start_date} - {end_date}" ----------------')

                    # 1. booking
                    try:
                        book = slot.book_slot(branch_id=BRANCH_ID,
                                              postcode=POSTCODE,
                                              address_id=slot.last_address_id,
                                              slot_type=FULFILMENT_TYPE,
                                              start_date_time=datetime.strptime(start_date, '%Y-%m-%dT%H:%M:%SZ'),
                                              end_date_time=datetime.strptime(end_date, '%Y-%m-%dT%H:%M:%SZ'))
                        print(f'The slot "{start_date} - {end_date}" has been SUCCESSFULLY booked')
                    except:
                        print(f'Booking for the slot "{start_date} - {end_date}" failed, trying to book the next slot')
                        continue

                    # slot has been booked, exit
                    break

        # if a basket is empty then adding items from the last order
        print(session.merge_last_order_to_basket())
        print(session._get_payment_cards())
        print(session.checkout_order(33505187324, 825))

        # all done, exit
        break
