import os 
import json
import tempfile
import openai
from openai import OpenAI
from datetime import datetime
from django.urls import reverse
from django.http import JsonResponse
from django.views import View
from django.utils import timezone
from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse

from .models import *

def api_key_view(request):
    try:
        api_key = APIKey.objects.first()
    except APIKey.DoesNotExist:
        api_key = None

    # Handle form submission
    if request.method == 'POST':
        key = request.POST.get('api_key')
        if key:
            if api_key:
                api_key.api_key = key  # Update the existing key
                api_key.save()
            else:
                APIKey.objects.create(api_key=key)  # Create a new key

            # Validate the API key after saving it
            openai.api_key = key
            try:
                openai.models.list()  # Validate the key
                return redirect('models-list')  # Redirect to the dashboard if valid
            except openai.AuthenticationError:
                return render(request, 'api_key/index.html', {
                    'error': 'Invalid API Key',
                    'api_key': None
                })

        else:
            return render(request, 'api_key/index.html', {
                'error': 'API Key is required',
                'api_key': None
            })

    # Handle displaying the error from the URL
    error_message = request.GET.get('error')
    return render(request, 'api_key/index.html', {
        'error': error_message,
        'api_key': api_key.api_key if api_key else None
    })


def format_record(record):
    """Format a single record to match the desired JSON Lines format."""
    
    # Create the message structure
    messages = [
        {"role": 'system', "content": record['system']},
        {"role": 'user', "content": record['user']},
        {"role": 'assistant', "content": record['assistant']}
    ]
    
    return {"messages": messages}


def select_model(request,job_id):
    action = request.POST.get('action','')
    output_model = request.POST.get('output_model','')
    all_fine_tune_models = FineTunningModel.objects.update(selected=False)
    if action == 'select':
        fine_tune_model = FineTunningModel.objects.get(model_id=job_id)
        fine_tune_model.selected = True
        fine_tune_model.output_model = output_model
        fine_tune_model.save()
    return JsonResponse({
        'status':'success'
    })


def fine_tune(request):
    if request.method == 'POST':
        api_key = APIKey.objects.first().api_key
        openai.api_key = api_key

        model_name = request.POST.get('model_name','')
        base_model = request.POST.get('base_model','')
        prompts = FineTuneExample.objects.all()
        if len(prompts) < 10:
            return JsonResponse({'status': 'failed', 'err': 'There should be at least 10 prompts'})

        data = [format_record(record) for record in prompts.values()]
        with tempfile.NamedTemporaryFile(delete=False, mode='w') as temp_file:
            for record in data:
                temp_file.write(json.dumps(record) + '\n')

            temp_file_name = temp_file.name
        try:
            # Upload the temporary file
            with open(temp_file_name, 'rb') as file_to_upload:
                file = openai.files.create(
                    file=file_to_upload,
                    purpose="fine-tune"
                )
            response = openai.fine_tuning.jobs.create(
                    training_file=file.id,
                    model=base_model
                )
            
            created_at_datetime = datetime.fromtimestamp(response.created_at)
            created_at_datetime = timezone.make_aware(created_at_datetime)
            FineTunningModel.objects.create(model_id=response.id,created_at=created_at_datetime,model_name=model_name)
            return JsonResponse({'status': 'success'})
        finally:
            # Ensure the temporary file is deleted after use
            os.remove(temp_file_name)


class FineTunningListView(View):
    def get(self,request):
        api_key = APIKey.objects.first().api_key
        openai.api_key = api_key

        try:
            response = openai.fine_tuning.jobs.list()
            jobs = []
            for job in response:

                # Convert created_at timestamp to a datetime object
                created_at_datetime = datetime.fromtimestamp(job.created_at)
                created_at_datetime = timezone.make_aware(created_at_datetime)
                model,created = FineTunningModel.objects.get_or_create(model_id=job.id,
                            defaults={'created_at': created_at_datetime}  # Use defaults to set 'created_at' only if created
                )
                # Convert datetime object to a formatted string
                job_dict = job.to_dict()  # Convert job object to a dictionary
                job_dict['model_name'] = model.model_name
                job_dict['selected'] = model.selected
                job_dict['created_at'] = created_at_datetime.strftime('%d-%m-%y %H:%M')
                jobs.append(job_dict)
        except Exception as e:
            jobs = []
            print(f"An error occurred: {e}")
        return render(request,'fine_tunning/index.html', {'jobs': jobs})
    

class FineTunnigDetailView(View):
    def get(self,request, job_id):
        api_key = APIKey.objects.first().api_key
        openai.api_key = api_key

        job = openai.fine_tuning.jobs.retrieve(job_id)
        fine_tune_model = FineTunningModel.objects.get(model_id=job_id)
        created_at_datetime = datetime.fromtimestamp(job.created_at)
        job_dict = job.to_dict()  # Convert job object to a dictionary
        job_dict['selected'] = fine_tune_model.selected
        job_dict['created_at'] = created_at_datetime.strftime('%Y-%m-%d %H:%M:%S')
        
        return JsonResponse({
            'job':job_dict
        })

class FineTuneExampleListView(View):
    LIST_OF_BASE_MODELS = [
        'babbage-002',
        'davinci-002',
        'gpt-3.5-turbo-0125',
        'gpt-3.5-turbo-0613',
        'gpt-3.5-turbo-1106',
        'gpt-4o-2024-08-06',
        'gpt-4o-mini-2024-07-18',
    ]
    def get(self,request):
        examples = FineTuneExample.objects.all()
        examples_data = [{
            'id':example.pk,
            'user':example.user,
            'system':example.system,
            'assistant':example.assistant
        } for example in examples]
        return render(request,'fine_tunning/components/create_model.html',context={"base_models":self.LIST_OF_BASE_MODELS,"saved_prompts":examples_data})

    def post(self,request):
        user = request.POST.get('user','')
        system = request.POST.get('system','')
        assistant = request.POST.get('assistant','')
        example = FineTuneExample.objects.create(user=user,system=system,assistant=assistant)
        example_data = {
            'id':example.pk,
            'user':example.user,
            'assistant':example.assistant,
            'system':example.system
        }
        return JsonResponse({
            'status':'success',
            'example':example_data
        })
