from django.shortcuts import render
print("*** DEBUG: views.py is being loaded ***")
from .models import Blog
from django.contrib.auth import get_user_model
from django.conf import settings
from .serializers import SimpleAuthorSerializer, UpdateUserProfileSerializer, UserInfoSerializer, UserRegistrationSerializer, BlogSerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
import os
import requests # Import the requests library

# Create your views here.
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def blog_list(request):
    blogs = Blog.objects.all()

    search_query = request.GET.get('search', None)
    category_filter = request.GET.get('category', None)

    if search_query:
        blogs = blogs.filter(title__icontains=search_query) | blogs.filter(content__icontains=search_query)
    
    if category_filter:
        blogs = blogs.filter(category__iexact=category_filter)

    serializer = BlogSerializer(blogs, many=True)
    return Response(serializer.data)


# @api_view(['GET'])
# def blog_list(request):
#     blogs = Blog.objects.all()
#     serializer = BlogSerializer(blogs, many=True)
#     return Response(serializer.data)

@api_view(['GET'])
def get_blog(request, slug):
    blog = Blog.objects.get(slug=slug)
    serializer = BlogSerializer(blog)
    return Response(serializer.data)



@api_view(["POST"])
def register_user(request):
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_user_profile(request):
    user = request.user
    serializer = UpdateUserProfileSerializer(user, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_blog(request):
    user = request.user
    serializer = BlogSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(author=user)
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# @api_view(["POST"])
# def create_blog(request):
#     serializer = BlogSerializer(data=request.data)
#     if serializer.is_valid():
#         serializer.save()
#         return Response(serializer.data)
#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_blog(request, pk):
    user = request.user
    blog = Blog.objects.get(id=pk)
    if blog.author != user:
        return Response({"error": "You are not the author of this blog"}, status=status.HTTP_403_FORBIDDEN)
    serializer = BlogSerializer(blog, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# @api_view(["PUT"])
# def update_blog(request, pk):
#     blog = Blog.objects.get(id=pk)
#     serializer = BlogSerializer(blog, data=request.data)
#     if serializer.is_valid():
#         serializer.save()
#         return Response(serializer.data)
#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def delete_blog(request, pk):
    blog = Blog.objects.get(id=pk)
    user = request.user 
    if blog.author != user:
        return Response({"error": "You are not the author of this blog"}, status=status.HTTP_403_FORBIDDEN)
    blog.delete()
    return Response({"message": "Blog deleted successfully"}, status=status.HTTP_204_NO_CONTENT)



@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_username(request):
    user = request.user
    username = user.username
    return Response({"username": username})


@api_view(['GET'])
def get_userinfo(request, username):
    User = get_user_model()
    user = User.objects.get(username=username)
    serializer = UserInfoSerializer(user)
    return Response(serializer.data)


@api_view(["GET"])
def get_user(request, email):
    User = get_user_model()
    try:
        existing_user = User.objects.get(email=email)
        serializer = SimpleAuthorSerializer(existing_user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)
    





@api_view(["POST"])
@permission_classes([IsAuthenticated])
def generate_description(request):
    if request.method == "POST":
        title = request.data.get("title")
        print(f"[DEBUG] Received title: {title}")
        print(f"[DEBUG] Using OPENROUTER_API_KEY: {settings.OPENROUTER_API_KEY[:5]}...{settings.OPENROUTER_API_KEY[-5:]}")
        if not title:
            return Response(
                {"error": "Title is required for description generation."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            headers = {
                "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                "HTTP-Referer": "http://localhost:5173", # Replace with your actual domain
                "Content-Type": "application/json"
            }
            data = {
                "model": "google/gemini-2.5-pro", # Updated model name based on user input
                "messages": [
                    {"role": "user", "content": f"Generate a short description for a blog post with the following title: {title}"}
                ]
            }
            print(f"[DEBUG] Sending headers: {headers}")
            print(f"[DEBUG] Sending data: {data}")
            
            openrouter_response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=data
            )
            print(f"[DEBUG] OpenRouter Response Status: {openrouter_response.status_code}")
            print(f"[DEBUG] OpenRouter Response Text: {openrouter_response.text}")
            openrouter_response.raise_for_status() # Raise an exception for HTTP errors
            
            response_data = openrouter_response.json()
            description = response_data["choices"][0]["message"]["content"].strip()

            return Response({"description": description}, status=status.HTTP_200_OK)
        except requests.exceptions.RequestException as e:
            return Response(
                {"error": f"Failed to connect to OpenRouter API: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception as e:
            return Response(
                {"error": f"Failed to generate description: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

# Facebook: https://www.facebook.com/sampleusername
# Instagram: https://www.instagram.com/sampleusername
# YouTube: https://www.youtube.com/user/sampleusername
# Twitter (now X): https://twitter.com/sampleusername
