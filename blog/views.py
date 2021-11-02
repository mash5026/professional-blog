from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView
from .models import Post, Comment
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Count
from .forms import EmailPostForm, CommentForm,SearchForm
from django.core.mail import send_mail
from taggit.models import Tag
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank


#class PostListView(ListView):
    #model = Post be sorate khodkar hameye object haye class post ra birun mikeshab
    #special query set:
    #queryset = Post.published.all()
    # name moteghayeri ke gharar ast be html pass dade shavad.
    #context_object_name = 'posts'
    # paginate kardane safehat
    #paginate_by = 3
    # moarefi file html jahate namayeshe dadeha.
    #template_name = 'blog/post/list.html'
def post_list(request, tag_slug=None):
    object_list = Post.published.all()
    tag=None

    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        object_list = object_list.filter(tags__in=[tag])

    paginator = Paginator(object_list, 3)
    page = request.GET.get('page')
    try:
       posts = paginator.page(page)
    except PageNotAnInteger:
       posts = paginator.page(1)
    except EmptyPage:
       posts = paginator.page(paginator.num_pages)
    content = {'page': page, 'posts': posts, 'tag': tag}
    return render(request, 'blog/post/list.html', content)


def post_detail(request, year, month, day, post):
    post_details = get_object_or_404(Post, slug=post, status='published', publish__year=year,
                             publish__month=month, publish__day=day)
    comments = post_details.comments.filter(active=True)
    new_comment = None
    if request.method == 'POST':
        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid():
            new_comment = comment_form.save(commit=False)
            new_comment.post = post_details
            new_comment.save()
    else:
        comment_form = CommentForm()

    post_tags_ids = post_details.tags.values_list('id', flat=True)
    similar_posts = Post.published.filter(tags__in=post_tags_ids).distinct().exclude(id=post_details.id)
    similar_posts = similar_posts.annotate(same_tags = Count('tags'))\
        .order_by('-same_tags', '-publish')[:5]


    content = {'detail': post_details, 'comments': comments, 'comment_form': comment_form,
               'new_comment': new_comment, 'similar_posts': similar_posts}
    return render(request, 'blog/post/detail.html', content)


def post_share(request, post_id):
    post = get_object_or_404(Post, id=post_id, status='published')
    sent = False
    if request.method == 'POST':
        form = EmailPostForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = "{} recommends you read".format(cd['name']) + ' ' + "{}".format(post.title)
            message = "Read {} at {} ".format(post.title, post_url) +  "{} comments: {}".format(cd['name'], cd['comments'])
            send_mail(subject,message, 'shamsmahdi098@gmail.com', [cd['to']])
            sent = True


    else:
        form = EmailPostForm()
    context = {'form': form, 'post': post, 'sent': sent}
    return render(request, 'blog/post/share.html', context)


def post_search(request):
    form = SearchForm()
    query = None
    results = []
    if 'query' in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
        #Step1:
            #query = form.cleaned_data['query']
            #results = Post.published.annotate(search=SearchVector('title', 'body'))\
            #.filter(search=query)
        #Step2:
            #search_vector = SearchVector('title','body')
            #search_query = SearchQuery(query)
            #results = Post.published.annotate(search=search_vector,rank=SearchRank(search_vector,search_query)) \
                #.filter(search=search_query).order_by('-rank')
            query = form.cleaned_data['query']
            search_vector = SearchVector('title', weight='A') + SearchVector('body', weight='B')
            search_query = SearchQuery(query)
            results = Post.published.annotate(rank=SearchRank(search_vector, search_query))\
            .filter(rank__gte=0.3).order_by('-rank')
    context = {
        'form': form,
        'query': query,
        'results': results,
    }
    return render(request, 'blog/post/search.html', context)








