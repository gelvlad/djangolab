from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views import View
from django.views.generic.edit import FormView
from .forms import TaskCreateForm, TaskDetailForm
from .settings import APIserver, domain
import requests
from .authentication.views import check_auth_token
from operator import methodcaller
import re


class TasklistCreate(View):
    APIurl = APIserver.format('todolists/')

    def get(self, request):
        response, is_ok = send_request(url=self.APIurl,
                                       user=request.user,
                                       method='get')
        if is_ok:
            context = {"tasklists": response.json()}
            return render(request, 'todolists.html', context=context)
        else:
            return HttpResponse(response)

    def post(self, request):
        tasklist_id = request.POST.get('delete', None)
        tasklist_name = request.POST.get('name', None)
        if tasklist_id:
            response, is_ok = send_request(url=self.APIurl + tasklist_id,
                                           user=request.user,
                                           method='delete')
        elif tasklist_name:
            response, is_ok = send_request(url=self.APIurl,
                                           user=request.user,
                                           method='post',
                                           data={"name": tasklist_name})
        else:
            return redirect('.')
        if is_ok:
            return redirect('.')
        else:
            return HttpResponse(response)


class TasklistDetail(View):
    def get(self, request, tasklist_id):
        APIurl = APIserver.format('todolists/' + tasklist_id)
        tasklistResponse, tasklist_ok = send_request(url=APIurl,
                                                     user=request.user,
                                                     method='get')
        tasksResponse, tasks_ok = send_request(url=APIurl + '/tasks',
                                               user=request.user,
                                               method='get')
        if not tasklist_ok and not tasks_ok:
            return HttpResponse("API server errors:\n {}\n {}".format(
                tasklistResponse, tasksResponse))
        elif not tasklist_ok:
            return HttpResponse(tasklistResponse)
        elif not tasks_ok:
            return HttpResponse(tasksResponse)
        context = {"tasklist": tasklistResponse.json(),
                   "tasks": tasksResponse.json()}
        return render(request, 'todolist_detail.html', context=context)

    def post(self, request, tasklist_id):
        keys = request.POST.keys()
        APIurl = APIserver.format('todolists/{}/'.format(tasklist_id))
        if 'delete_task' in keys:
            response, is_ok = send_request(url=APIurl + 'tasks/{}/'
                                           .format(request.POST
                                                   .get('delete_task', None)),
                                           user=request.user,
                                           method='delete')
            if is_ok:
                return redirect('.')
        elif 'delete_tasklist' in keys:
            response, is_ok = send_request(url=APIurl,
                                           user=request.user,
                                           method='delete')
            if is_ok:
                return redirect('/todolists/')
        elif 'remove_sharer' in keys:
            response, is_ok = send_request(url=APIserver.format('todolists/'
                                                                + tasklist_id),
                                           user=request.user,
                                           method='get')
            if not is_ok:
                return HttpResponse(response)
            tasklist_sharers = response.json().get('sharers', None)
            sharer = request.POST.get('remove_sharer', None)
            if sharer:
                tasklist_sharers.remove({'username': sharer})
            if not tasklist_sharers:
                tasklist_sharers =[{}]
            response, is_ok = send_request(url=APIurl,
                                           user=request.user,
                                           method='patch',
                                           json={'sharers': tasklist_sharers})
            if is_ok:
                return redirect('.')
        elif 'add_sharers' in keys:
            response, is_ok = send_request(url=APIserver.format('todolists/'
                                                                + tasklist_id),
                                           user=request.user,
                                           method='get')
            if not is_ok:
                return HttpResponse(response)
            tasklist_sharers = response.json().get('sharers', None)
            sharers = request.POST.get('sharers', None)
            if not sharers:
                return redirect('.')
            sharers = re.split('\W+', sharers)
            for sharer in sharers:
                tasklist_sharers.append({'username': sharer})
            response, is_ok = send_request(url=APIurl,
                                           user=request.user,
                                           method='patch',
                                           json={'sharers': tasklist_sharers})
            if is_ok:
                return redirect('.')
        elif 'rename_tasklist' in keys:
            tasklist_name = request.POST.get('name', None)
            if not tasklist_name:
                return redirect('.')
            response, is_ok = send_request(url=APIurl,
                                           user=request.user,
                                           method='patch',
                                           data={"name": tasklist_name})
            if is_ok:
                return redirect('.')
        else:
            return redirect('.')
        return HttpResponse(response)


class TaskCreate(FormView):
    template_name = 'task_create.html'
    form_class = TaskCreateForm
    success_url = '.'

    def form_valid(self, form):
        APIurl = APIserver.format('todolists/{}/tasks/'.format(self.args[0]))
        data = self.request.POST.dict()
        tags = data.get('tags', None)
        task_tags = []
        if tags:
            tags = re.split('\W+', tags)
            for tag in tags:
                task_tags.append({'name': tag})
            data.pop('tags')
        response, is_ok = send_request(url=APIurl,
                                       user=self.request.user,
                                       method='post',
                                       data=data)
        if not is_ok:
            return HttpResponse(response)
        response, is_ok = send_request(url=APIurl +
                                           '{}/'.format(response.json()['id']),
                                       user=self.request.user,
                                       method='patch',
                                       json={'tags': task_tags})
        if is_ok:
            return redirect('/todolists/{}/task/{}/'.format(
                self.args[0], response.json()['id']))
        return HttpResponse(response)


class TaskDetail(View):
    buttons = []

    def get(self, request, list_id, pk):
        APIurl = APIserver.format('todolists/{}/tasks/{}/'.format(list_id, pk))
        response, is_ok = send_request(url=APIurl,
                                       user=request.user,
                                       method='get')
        if not is_ok:
            return HttpResponse(response)
        form = TaskDetailForm()
        for field in form:
            self.buttons.append("edit_{}".format(field.name))
        context = {"task": response.json(), "form": form}
        return render(request, 'task_detail.html', context=context)

    def post(self, request, list_id, pk):
        print(request.POST)
        APIurl = APIserver.format('todolists/{}/tasks/{}/'.format(list_id, pk))
        if 'delete' in request.POST.keys():
            response, is_ok = send_request(url=APIurl,
                                user=request.user,
                                method='delete')
            if is_ok:
                return redirect('http://{}/todolists/{}/'.format(domain, list_id))
            else:
                return HttpResponse(response)
        response, is_ok = self._patch_field(APIurl, request)
        if is_ok:
            return redirect('.')
        return HttpResponse(response)

    def _patch_field(self, url, request):
        for button in self.buttons:
            if button in request.POST.keys():
                if button == 'edit_tags':
                    tags = request.POST.get('tags', None)
                    task_tags = []
                    if tags:
                        tags = re.split('\W+', tags)
                        for tag in tags:
                            task_tags.append({'name': tag})
                    return send_request(url=url,
                                        user=request.user,
                                        method='patch',
                                        json={'tags': task_tags})
                field = button[5:]
                if field == 'completed':
                    data = request.POST.get('completed', 'off')
                else:
                    data = request.POST[field]
                return send_request(url=url,
                                    user=request.user,
                                    data={field: data},
                                    method='patch')


def send_request(url, user, method, data=None, json=None):
    auth_token = check_auth_token(user)
    if not auth_token:
        return 'Access denied', False
    header = {'Authorization': 'Token {}'.format(auth_token)}
    try:
        if method in ('post', 'put', 'patch'):
            response = methodcaller(method, url, data=data, json=json,
                                    headers=header)(requests)
        elif method in ('get', 'delete'):
            response = methodcaller(method, url, headers=header)(requests)
        else:
            return 'Unknown method', False
    except ConnectionError:
        return 'Failed to connect to API server', False
    except:
        return 'Something is wrong!', False
    if response.ok:
        return response, True
    elif response.status_code == 403:
        return 'Access denied', False
    else:
        return 'Server error ' + str(response.status_code), False

