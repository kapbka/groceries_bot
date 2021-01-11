# constants for the utils


SESSION_ENDPOINT_URL = "https://www.waitrose.com/api/graphql-prod/graph/live"

ACCOUNT_URL = 'https://www.waitrose.com/api/account-orchestration-prod/v1/accounts/self'

LAST_ADDRESS_ID_URL = 'https://www.waitrose.com/api/address-prod/v1/addresses?sortBy=-lastDelivery'

ORDER_LIST_URL = 'https://www.waitrose.com/api/order-orchestration-prod/v1/orders?size=15&statuses=COMPLETED%2BCANCELLED%2BREFUND_PENDING'

PRODUCT_LIST_URL = 'https://www.waitrose.com/api/products-prod/v1/products/{}?view=SUMMARY'

SHOP_FROM_ORDER_URL = 'https://www.waitrose.com/ecom/myaccount/my-orders/order/shop-from-order/$order_id'

TROLLEY_PRODUCTS_URL = 'https://www.waitrose.com/api/orderitems-prod/v4/orders/{}/trolley'

TROLLEY_ITEMS_URL = 'https://www.waitrose.com/api/orderitems-prod/v4/orders/{}/trolley/items?merge=true'

PAYMENTS_CARDS_URL = 'https://www.waitrose.com/api/payment-orchestration-prod/v1/payments/paymentcards/'

CHECKOUT_URL = 'https://www.waitrose.com/api/order-orchestration-prod/v1/orders/{}/payment-cards/{}'

SESSION_QUERY = """
            mutation($session: SessionInput) {      
                  generateSession(session: $session) {
                          accessToken
                          customerId
                          customerOrderId
                          customerOrderState
                          defaultBranchId
                          expiresIn
                          permissions
                          principalId
                          failures{
                                type
                                message
                          }
                  }
            }
        """

SLOT_QUERY = """
            query slotDays($slotDaysInput: SlotDaysInput) {  
                slotDays(slotDaysInput: $slotDaysInput) {
                    content {
                        id
                        branchId
                        slotType
                        date
                        slots {
                            slotId: id
                            startDateTime
                            endDateTime
                            shopByDateTime
                            slotStatus: status
                        }
                    }
                    links {
                        rel
                        title
                        href
                    }
                    failures {
                        message
                        type
                    }
                }
            }
        """

BOOK_SLOT_QUERY = """
            mutation($bookSlotInput: BookSlotInput) {
                bookSlot(bookSlotInput: $bookSlotInput) {
                    amendOrderCutoffDateTime
                    orderCutoffDateTime
                    shopByDateTime
                    slotExpiryDateTime
                    failures {
                        message
                        type
                    }
                }
            }
        """

CURRENT_SLOT_QUERY = """
            query currentSlot($currentSlotInput: CurrentSlotInput) {
                currentSlot(currentSlotInput: $currentSlotInput) {
                    slotType
                    branchId
                    addressId
                    postcode
                    startDateTime
                    endDateTime
                    expiryDateTime
                    orderCutoffDateTime
                    amendOrderCutoffDateTime
                    shopByDateTime
                }
            }
        """
