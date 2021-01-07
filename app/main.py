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
                continue
            else:
                print(json.dumps(available_slots, indent=2))

                start_date, end_date = slot.book_first_available_slot(slots=available_slots,
                                                                      branch_id=BRANCH_ID,
                                                                      postcode=POSTCODE,
                                                                      address_id=session.last_address_id,
                                                                      slot_type=SLOT_TYPE)

        basket_product_cnt = None
        # if a basket is empty then adding items from the last order
        if not basket_product_cnt:
            print(session.merge_last_order_to_basket())

        if args.card_num:
            # first we get internal card_id
            print(session._get_payment_cards())
            # second we make a checkout
            print(session.checkout_order(33505187324, 825))

        # all done, exit
        break
