from app.utils import Session, Slot
import time
import json


POSTCODE = 'EC1M 6EB' # 'E14 3TJ'
SLOT_TYPE = 'DELIVERY'
REQUEST_INTERVAL = 15
BRANCH_ID = 199 # 753


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Please, enter login and password to print the slots, '
                                                 'if necessary add an interval as the third parameter.')
    parser.add_argument('--login', help='User login')
    parser.add_argument('--password', help='User password')
    parser.add_argument('--fulfilment_type', default=SLOT_TYPE, help='Fulfilment type')
    parser.add_argument('--postcode', default=POSTCODE, help='Post code')
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
        slot = Slot(session=session, fulfilment_type=args.fulfilment_type, postcode=args.postcode)
        start_date, end_date = slot.get_current_slot()

        # if there is no booked slot
        if not start_date and not end_date:
            available_slots = slot.get_available_slots()

            print(f'------ Attempt number {cnt} --------------')

            if not available_slots:
                time.sleep(args.interval*60)
                continue
            else:
                print(json.dumps(available_slots, indent=2))

                start_date, end_date = slot.book_first_available_slot(slots=available_slots,
                                                                      branch_id=BRANCH_ID,
                                                                      postcode=POSTCODE,
                                                                      address_id=session.last_address_id,
                                                                      slot_type=SLOT_TYPE)

        if session.is_trolley_empty():
            session.merge_order_to_trolley(session.last_order_id)

        if args.card_num:
            card_id = session.get_card_id(args.card_num)
            if not card_id:
                raise ValueError(f'Card number with last 4 digits "***{args.card_num}" is not found!')
            else:
                session.checkout_trolley(session.customerOrderId, args.cvv)

        # all done, exit
        break
