from session import Session
from slot_getter import SlotGetter


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('integers', metavar='N', type=int, nargs='+',
                        help='an integer for the accumulator')
    parser.add_argument('--sum', dest='accumulate', action='store_const',
                        const=sum, default=max,
                        help='sum the integers (default: find the max)')

    args = parser.parse_args()
    print(args.accumulate(args.integers))

    mySession = Session('clrn@mail.ru', '3zbiWViHJuE&{Ns')

    token = mySession.token

    myG = SlotGetter(token=token, fulfilment_type='DELIVERY', postcode='E14 3TJ')
    # print(myG.get_last_address_id())
    # print(myG.get_slots(753,mySession.customerId))
    print(myG.get_available_slots(753, mySession.customerOrderId))
