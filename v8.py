import os
import requests
import random
import base64
import json
from datetime import datetime

def get_random_file_content(token):
    headers = {
        "Authorization": f"token {token}"
    }
    search_url = "https://api.github.com/search/repositories?q=README"
    response = requests.get(search_url, headers=headers)
    if response.status_code == 200:
        repositories = response.json()['items']
        if repositories:
            random_repo = random.choice(repositories)
            repo_owner = random_repo['owner']['login']
            repo_name = random_repo['name']
            contents_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents"
            response = requests.get(contents_url, headers=headers)
            if response.status_code == 200:
                files = response.json()
                if files:
                    random_file_info = random.choice(files)
                    file_path = random_file_info['path']
                    content_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{file_path}"
                    response = requests.get(content_url, headers=headers)
                    if response.status_code == 200:
                        file_info = response.json()
                        if file_info['type'] == 'file' and file_info['encoding'] == 'base64':
                            content = base64.b64decode(file_info['content']).decode()
                            return content
                        else:
                            print("File is not text, skipping...")
                    else:
                        print("Failed to get content of random file. Status code:", response.status_code)
                else:
                    print("No files found in the repository.")
            else:
                print("Failed to get contents of repository. Status code:", response.status_code)
        else:
            print("No repositories found.")
    else:
        print("Failed to search for repositories. Status code:", response.status_code)
    return None

def get_user_info(token):
    headers = {
        "Authorization": f"token {token}"
    }
    url = "https://api.github.com/user"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        user_info = response.json()
        username = user_info['login']
        email = user_info['email'] if user_info['email'] else "example@example.com"
        return username, email
    else:
        print("Failed to get user info. Status code:", response.status_code)
        return None, None

def get_user_repos(token):
    headers = {
        "Authorization": f"token {token}"
    }
    url = "https://api.github.com/user/repos"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        repos_info = response.json()
        repo_names = [repo['name'] for repo in repos_info]
        return repo_names
    else:
        print("Failed to get user repos. Status code:", response.status_code)
        return None

def get_file_sha(token, repository_owner, repository_name, file_path):
    headers = {
        "Authorization": f"token {token}"
    }
    url = f"https://api.github.com/repos/{repository_owner}/{repository_name}/contents/{file_path}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        file_info = response.json()
        return file_info['sha']
    else:
        print("Failed to get file SHA. Status code:", response.status_code)
        return None

def create_commit_with_date(token, username, email, repository_owner, repository_name, commit_message, content, sha, date):
    url = f"https://api.github.com/repos/{repository_owner}/{repository_name}/git/commits"

    content_encoded = base64.b64encode(content.encode()).decode()

    headers = {
        "Authorization": f"token {token}"
    }

    # Create a blob for the file content
    blob_data = {
        "content": content_encoded,
        "encoding": "base64"
    }
    blob_url = f"https://api.github.com/repos/{repository_owner}/{repository_name}/git/blobs"
    blob_response = requests.post(blob_url, headers=headers, json=blob_data)
    if blob_response.status_code != 201:
        print("Failed to create blob. Status code:", blob_response.status_code)
        return

    blob_sha = blob_response.json()['sha']

    # Get the current reference of the branch
    ref_url = f"https://api.github.com/repos/{repository_owner}/{repository_name}/git/refs/heads/main"
    ref_response = requests.get(ref_url, headers=headers)
    if ref_response.status_code != 200:
        print("Failed to get branch reference. Status code:", ref_response.status_code)
        return

    base_commit_sha = ref_response.json()['object']['sha']

    # Get the tree of the base commit
    tree_url = f"https://api.github.com/repos/{repository_owner}/{repository_name}/git/trees/{base_commit_sha}"
    tree_response = requests.get(tree_url, headers=headers)
    if tree_response.status_code != 200:
        print("Failed to get tree. Status code:", tree_response.status_code)
        return

    base_tree_sha = tree_response.json()['sha']

    # Create a new tree with the updated file
    tree_data = {
        "base_tree": base_tree_sha,
        "tree": [
            {
                "path": "README.md",
                "mode": "100644",
                "type": "blob",
                "sha": blob_sha
            }
        ]
    }
    new_tree_url = f"https://api.github.com/repos/{repository_owner}/{repository_name}/git/trees"
    new_tree_response = requests.post(new_tree_url, headers=headers, json=tree_data)
    if new_tree_response.status_code != 201:
        print("Failed to create new tree. Status code:", new_tree_response.status_code)
        return

    new_tree_sha = new_tree_response.json()['sha']

    # Create a new commit with the specified date
    commit_data = {
        "message": commit_message,
        "author": {
            "name": username,
            "email": email,
            "date": date
        },
        "parents": [base_commit_sha],
        "tree": new_tree_sha
    }
    commit_response = requests.post(url, headers=headers, json=commit_data)
    if commit_response.status_code != 201:
        print("Failed to create commit. Status code:", commit_response.status_code)
        return

    new_commit_sha = commit_response.json()['sha']

    # Update the reference of the branch to point to the new commit
    update_ref_data = {
        "sha": new_commit_sha,
        "force": True
    }
    update_ref_response = requests.patch(ref_url, headers=headers, json=update_ref_data)
    if update_ref_response.status_code == 200:
        print("Commit created successfully!")
    else:
        print("Failed to update branch reference. Status code:", update_ref_response.status_code)

def main():
    personal_access_token = os.environ.get('PERSONAL_ACCESS_TOKEN')
    if personal_access_token:
        random_file_content = get_random_file_content(personal_access_token)
        if random_file_content:
            username, email = get_user_info(personal_access_token)
            if username and email:
                repo_names = get_user_repos(personal_access_token)
                if repo_names:
                    repository_name = random.choice(repo_names)
                    file_path = "README.md"
                    file_sha = get_file_sha(personal_access_token, username, repository_name, file_path)
                    if file_sha:
                        commit_message = "Update README.md"
                        commit_date = "2023-01-01T12:00:00Z"  # Định dạng ISO 8601

                        create_commit_with_date(personal_access_token, username, email, username, repository_name, commit_message, random_file_content, file_sha, commit_date)
                    else:
                        print("Failed to get file SHA.")
                else:
                    print("User has no repositories.")
            else:
                print("Failed to get user info. Please check your access token.")
        else:
            print("Failed to get random file content.")
    else:
        print("Failed to get personal access token from environment variables.")

if __name__ == "__main__":
    main()
