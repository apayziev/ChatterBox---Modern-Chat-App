# chat/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import Room, Message


@login_required
def room_list(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        if title:
            Room.objects.create(title=title)
            return redirect('room_list')
    
    rooms = Room.objects.all().order_by('-id')
    return render(request, 'room_list.html', {'rooms': rooms})


@login_required
def room_detail(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    message_list = Message.objects.filter(room=room).order_by('timestamp')
    
    # Add pagination with larger page size
    paginator = Paginator(message_list, 100)  # Increased to 100 messages per page
    page = request.GET.get('page')
    messages = paginator.get_page(page)
    
    return render(request, 'room.html', {
        'room': room,
        'messages': messages,
        'user': request.user
    })
