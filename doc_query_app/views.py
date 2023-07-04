import os
import json
from django.shortcuts import redirect, render
from django.http import HttpResponse, HttpRequest
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from llama_index import VectorStoreIndex, SimpleDirectoryReader

ALLOWED_EXTENSIONS = ["docx", "pdf", "txt"]
os.environ["OPENAI_API_KEY"] = "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"


"""Returns a human readable string representation of bytes"""
def human_size(bytes: int, units=[" bytes", "KB", "MB", "GB", "TB", "PB", "EB"]) -> str:
    return str(bytes) + units[0] if bytes < 1024 else human_size(bytes >> 10, units[1:])


def index(request: HttpRequest) -> HttpResponse:
    if not request.user.is_authenticated:
        print("Not authenticated bro")
        return render(request, "index.html")

    if request.method == "POST":
        uploaded_file = request.FILES.get("file")
        filenames = os.listdir(f"media/{request.user.username}")
        files = [
            {
                "name": name,
                "size": human_size(
                    default_storage.size(f"media/{request.user.username}/{name}")
                ),
            }
            for name in filenames
        ]
        print("files", files)

        # if file extension is not supported
        if uploaded_file is None or uploaded_file.name.split(".")[-1] not in ALLOWED_EXTENSIONS:
            context = {
                "error": "File must end in either .docx, .txt or .pdf",
                "files": files,
            }
            return render(request, "index.html", context)

        location = f"media/{request.user.username}/{uploaded_file.name}"
        # if file already exists at that location do not store again
        if default_storage.exists(location):
            context = {
                "error": "File already exists",
                "files": files,
            }
            return render(request, "index.html", context)

        path = default_storage.save(location, uploaded_file)
        filenames = os.listdir(f"media/{request.user.username}")
        files = [
            {
                "name": name,
                "size": human_size(
                    default_storage.size(f"media/{request.user.username}/{name}")
                ),
            }
            for name in filenames
        ]
        print("files", files)
        context = {
            "success": "File uploaded at " + str(path),
            "files": files,
        }
        return render(request, "index.html", context)

    try:
        filenames = os.listdir(f"media/{request.user.username}")
        files = [
            {
                "name": name,
                "size": human_size(
                    default_storage.size(f"media/{request.user.username}/{name}")
                ),
            }
            for name in filenames
        ]
        print("files", files)
    except FileNotFoundError:
        files = None

    return render(request, "index.html", {"files": files})


def login_view(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("/doc-query/")

    if request.POST:
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("/doc-query/")
        else:
            return render(
                request,
                "login.html",
                {
                    "username": username,
                    "password": password,
                    "error": "Invalid username or password",
                },
            )
    return render(request, "login.html")


@login_required
def logout_view(request: HttpRequest) -> HttpResponse:
    logout(request)
    return redirect("/doc-query/login")


def signup_view(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("/doc-query/")

    if request.POST:
        username = request.POST["username"]
        password = request.POST["password"]
        confirm_password = request.POST["confirm-password"]
        if password != confirm_password:
            return render(
                request,
                "signup.html",
                {
                    "username": username,
                    "password": password,
                    "error": "Passwords need to match to confirm",
                },
            )

        user = User.objects.create_user(username=username, password=password)
        user.save()
        return redirect("/doc-query/login")

    return render(request, "signup.html")


@login_required
def query_files(request) -> HttpResponse:
    query = request.POST.get("question", "Who is this CV for?")
    print(f"Query: {query}")
    documents = SimpleDirectoryReader(f"media/{request.user.username}").load_data()
    index = VectorStoreIndex.from_documents(documents)
    query_engine = index.as_query_engine()
    response = query_engine.query(query)
    print(response)
    return HttpResponse(json.dumps({"message": str(response)}))


@login_required
def delete_file(request, username, filename) -> HttpResponse:
    path = f"media/{username}/{filename}"
    default_storage.delete(path)
    print(path)
    return redirect("/doc-query/")
