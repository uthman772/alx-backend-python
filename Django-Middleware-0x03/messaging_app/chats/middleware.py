import datetime
import logging
from django.utils.deprecation import MiddlewareMixin

# Configure logger
logger = logging.getLogger('request_logger')
logger.setLevel(logging.INFO)

# Create file handler
file_handler = logging.FileHandler('requests.log')
file_handler.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter('%(message)s')
file_handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(file_handler)

class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log user requests including timestamp, user, and request path.
    """
    
    def __init__(self, get_response=None):
        self.get_response = get_response
        super().__init__(get_response)
    
    def __call__(self, request):
        # Log the request before processing
        self.log_request(request)
        
        # Get the response
        response = self.get_response(request)
        
        return response
    
    def log_request(self, request):
        """
        Log the request details including timestamp, user, and path.
        """
        # Get current timestamp
        timestamp = datetime.datetime.now()
        
        # Get user information
        if request.user.is_authenticated:
            user = request.user.username
        else:
            user = "Anonymous"
        
        # Log the request information
        log_message = f"{timestamp} - User: {user} - Path: {request.path}"
        logger.info(log_message)