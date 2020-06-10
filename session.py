from python_graphql_client import GraphqlClient


class Session:

    def __init__(self, login, password):
        self.login = login
        self.password = password
        self.client = GraphqlClient(endpoint="https://www.waitrose.com/api/graphql-prod/graph/live")

        query = """
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
        variables = {"session": {"username": login, "password": password, "customerId": "-1", "clientId": "WEB_APP"}}

        data = self.client.execute(query=query, variables=variables)
        #print(data)
        self.token = data['data']['generateSession']['accessToken']
        self.customerId = data['data']['generateSession']['customerId']
        self.customerOrderId = data['data']['generateSession']['customerOrderId']


    def execute(self, query, variables):
        return self.client.execute(query=query, variables=variables, headers={'authorization': f"Bearer {self.token}"})