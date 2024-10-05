import openai
from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse
from .models import APIKey

class CheckAPIKeyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Allow access to the API key form
        if request.path == reverse('api-key'):
            return self.get_response(request)

        # Check if an API key exists
        api_key = APIKey.objects.first()
        if api_key:
            openai.api_key = api_key.api_key
            try:
                # Verify the API key by making a simple API call
                openai.models.list()  # This will raise an error if the key is invalid
            except openai.AuthenticationError:
                # Redirect to the API key form with an error message
                return redirect(f"{reverse('api-key')}?error=Invalid API Key")
        else:
            # If no API key exists, redirect to the API key form
            return redirect('api-key')

        # Proceed with the request if everything is valid
        response = self.get_response(request)
        return response
