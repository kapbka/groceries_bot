# constants for waitrose chain


USER_AGENT = """Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.190 Safari/537.36"""

MAIN_PAGE_URL = "https://www.waitrose.com"

SESSION_ENDPOINT_URL = "https://www.waitrose.com/api/graphql-prod/graph/live"

# returns strange data
ACCOUNT_URL = 'https://www.waitrose.com/api/account-orchestration-prod/v1/accounts/self'

MEMBERSHIP_URL = 'https://www.waitrose.com/api/memberships-prod/v1/memberships'

LAST_ADDRESS_ID_URL = 'https://www.waitrose.com/api/address-prod/v1/addresses?sortBy=-lastDelivery'

#AMENDING+FULFIL+PAID+PAYMENT_FAILED+PICKED+PLACED
ORDER_LIST_URL = 'https://www.waitrose.com/api/order-orchestration-prod/v1/orders?size=15&statuses=COMPLETED%2BPLACED%2BREFUND_PENDING'

BRANCH_ID_BY_POSCODE_URL = 'https://www.waitrose.com/api/branch-prod/v3/branches?fulfilment_type=DELIVERY&location={}'

PRODUCT_LIST_URL = 'https://www.waitrose.com/api/products-prod/v1/products/{}?view=SUMMARY'

SHOP_FROM_ORDER_URL = 'https://www.waitrose.com/ecom/myaccount/my-orders/order/shop-from-order/$order_id'

TROLLEY_PRODUCTS_URL = 'https://www.waitrose.com/api/orderitems-prod/v4/orders/{}/trolley'

TROLLEY_ITEMS_URL = 'https://www.waitrose.com/api/orderitems-prod/v4/orders/{}/trolley/items?merge=true'

PAYMENTS_CARDS_URL = 'https://www.waitrose.com/api/payment-orchestration-prod/v1/payments/paymentcards/'

CHECKOUT_URL = 'https://www.waitrose.com/api/order-orchestration-prod/v1/orders/{}/payment-cards/{}'

PLACE_ORDER_URL = 'https://www.waitrose.com/api/order-orchestration-prod/v1/orders/{}/place'

DELETE_SESSION_QUERY = """
            mutation($session: DeleteSessionInput) {
                  deleteSession(session: $session)
            }
        """

SESSION_QUERY = """mutation($session: SessionInput) {
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
    }"""

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

TROLLEY_QUERY = """
            query getTrolley($orderId: ID!) {
              getTrolley(orderId: $orderId) {
                checkoutReadiness {
                  orderTypeValid
                  slotTypeValid
                }
                instantCheckout
                itemsReservable
                products {
                  barCode
                  brandName
                  categories {
                    categoryIds
                    id
                    name
                    parentId
                    subCategories
                  }
                  contents {
                    cookingStatus
                  }
                  currentSaleUnitPrice {
                    price {
                      amount
                      currencyCode
                    }
                    quantity {
                      amount
                      uom
                    }
                  }
                  defaultQuantity {
                    amount
                    uom
                  }
                  displayPrice
                  displayPriceEstimated
                  displayPriceQualifier
                  formattedPriceRange
                  formattedWeightRange
                  id
                  leadTime
                  lineNumber
                  maxPersonalisedMessageLength
                  name
                  persistDefault
                  productType
                  promotion {
                    groups {
                      threshold
                      name
                      lineNumbers
                    }
                    myWaitrosePromotion
                    promotionDescription
                    promotionExpiryDate
                    promotionId
                    promotionTypeCode
                    promotionUnitPrice {
                      amount
                      currencyCode
                    }
                    promotionalPricePerUnit
                    pyoPromotion
                  }
                  promotions {
                    groups {
                      threshold
                      name
                      lineNumbers
                    }
                    myWaitrosePromotion
                    promotionDescription
                    promotionExpiryDate
                    promotionId
                    promotionTypeCode
                    promotionUnitPrice {
                      amount
                      currencyCode
                    }
                    promotionalPricePerUnit
                    pyoPromotion
                  }
                  restriction {
                    availableDates {
                      restrictionId
                      startDate
                      endDate
                      cutOffDate
                    }
                  }
                  resultType
                  reviews {
                    averageRating
                    reviewCount
                  }
                  servings {
                    max
                    min
                  }
                  size
                  thumbnail
                  typicalWeight {
                    amount
                    uom
                  }
                  weights {
                    perUomQualifier
                    pricePerUomQualifier
                    uoms
                  }
                  productImageUrls {
                    small
                    medium
                    large
                    extraLarge
                  }
                }
                slotChangeable
                trolley {
                  amendingOrder
                  conflicts {
                    itemId
                    productId
                    messages
                    priority
                    outOfStock
                    resolutionActions
                    prohibitedActions
                    type
                    slotOptionDates {
                      date
                      type
                    }
                  }
                  orderId
                  slot {
                    branchId
                    serviceCounterAllowed
                    slotDate
                    slotEndTime
                    slotStartTime
                    slotType
                  }
                  trolleyItems {
                    canSubstitute
                    lineNumber
                    noteToShopper
                    personalisedMessage
                    productId
                    quantity {
                      amount
                      uom
                    }
                    reservedQuantity
                    retailPrice {
                      price {
                        amount
                        currencyCode
                      }
                      quantity {
                        amount
                        uom
                      }
                    }
                    saving {
                      amount
                      currencyCode
                    }
                    totalPrice {
                      amount
                      currencyCode
                    }
                    triggeredPromotions
                    trolleyItemId
                    untriggeredPromotions
                    productSummary {
                      availableDays
                      containsAlcohol
                      deliveryDaysEarly
                      deliveryOnDay
                      productShelfLife
                      productType
                      substitutionsProhibited
                      supplierOrder
                    }
                  }
                  trolleyTotals {
                    collectionMinimumOrderValue {
                      amount
                      currencyCode
                    }
                    deliveryMinimumOrderValue {
                      amount
                      currencyCode
                    }
                    entertainingMinimumOrderValue {
                      amount
                      currencyCode
                    }
                    minimumOrderValue {
                      amount
                      currencyCode
                    }
                    minimumSpendThresholdMet
                    savingsFromIncentives {
                      amount
                      currencyCode
                    }
                    savingsFromOffers {
                      amount
                      currencyCode
                    }
                    savingsFromOffersAndIncentives {
                      amount
                      currencyCode
                    }
                    savingsFromOrderLines {
                      amount
                      currencyCode
                    }
                    savingsFromMyWaitrose {
                      amount
                      currencyCode
                    }
                    totalEstimatedCost {
                      amount
                      currencyCode
                    }
                    trolleyItemCounts {
                      hardConflicts
                      noConflicts
                      softConflicts
                    }
                  }
                }
                failures {
                  field
                  message
                  type
                }
              }
            }
        """
