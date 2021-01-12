from app.session import Session
from app.slot import Slot
import time


SLOT_TYPE = 'DELIVERY'
REQUEST_INTERVAL = 15


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Please, enter login and password to print the slots, '
                                                 'if necessary add an interval as the third parameter.')
    parser.add_argument('--login', help='User login')
    parser.add_argument('--password', help='User password')
    parser.add_argument('--slot_type', default=SLOT_TYPE, help='Slot type (DELIVERY, COLLECT)')
    parser.add_argument('--interval', type=int, default=REQUEST_INTERVAL, help='Interval to check available slots(min)')
    parser.add_argument('--card_num', type=int, default=None, help='Last 4 card number digits')
    parser.add_argument('--card_cvv', type=int, default=None, help='CVV (last 3 digits on the back side of the card)')

    args = parser.parse_args()

    if args.card_num and not args.card_cvv:
        raise argparse.ArgumentTypeError(f'You have to provide cvv if card_num is specified (card_num ***{args.card_num})')

    cnt = 0

    while True:
        cnt += 1

        session = Session(args.login, args.password)
        slot = Slot(session=session, slot_type=args.slot_type)
        start_date, end_date = slot.get_current_slot()

        # if there is no booked slot
        if not start_date and not end_date:
            print(f'------ Attempt number {cnt} --------------')
            try:
                start_date, end_date = slot.book_first_available_slot()
            except ValueError:
                time.sleep(args.interval * 60)
                continue

        if session.is_trolley_empty():
            session.merge_order_to_trolley()

        if args.card_num:
            session.checkout_trolley(session.get_card_id(args.card_num), args.cvv)

        # all done, exit
        break
