from django.shortcuts import render
from scraper_module.models import ScrapedTopicGroups


def home(request):
    topics = ScrapedTopicGroups.objects.all()
    context = {'topics': topics}
    return render(request, 'home.html', context)


def topic(request, tag_id):
    scraped_topic = ScrapedTopicGroups.objects.get(id=tag_id)
    context = {'topic': scraped_topic}
    return render(request, 'topic.html', context)