# constants for the utility


SESSION_ENDPOINT_URL = "https://www.waitrose.com/api/graphql-prod/graph/live"

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

CONFIRM_SLOT_QUERY = """
            "query": "query currentSlot($currentSlotInput: CurrentSlotInput) {
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
