from rest_framework.pagination import PageNumberPagination

class CustomPagination(PageNumberPagination):
    page_size = 10  
    page_size_query_param = 'page_size'  
    max_page_size = 100  
    page_query_param = 'page'

    def get_paginated_response(self, data):
        response = super().get_paginated_response(data)
        response.data['page'] = self.page.number
        response.data['count'] = self.page.paginator.count
        response.data['next'] = self.get_next_link()
        response.data['previous'] = self.get_previous_link()
        return response