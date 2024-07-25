import requests
import re
from datetime import datetime
import openai
import os
import json

# Set up OpenAI API key
openai.api_key = os.environ.get("OPENAI_API_KEY")

def get_starred_repos(username):
    url = f"https://api.github.com/users/{username}/starred"
    headers = {"Authorization": f"token {os.environ['GITHUB_TOKEN']}"}
    response = requests.get(url, headers=headers)
    return response.json()

def categorize_repos(repos):
    # Prepare the input for the LLM
    repo_info = "\n".join([f"{repo['name']}: {repo['description']}" for repo in repos])
    
    prompt = f"""
    Categorize the following GitHub repositories into relevant categories for AI and Data Science. 
    Create appropriate category names and group the repositories under them. 
    Here are the repositories:

    {repo_info}

    Provide the output in JSON format with category names as keys and lists of repository names as values.
    """

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that categorizes GitHub repositories."},
            {"role": "user", "content": prompt}
        ]
    )

    # Parse the JSON response
    categories = json.loads(response.choices[0].message.content)
    return categories

def update_readme(repos, categories):
    with open('README.md', 'r') as file:
        content = file.read()

    # Update the starred repos section
    start_marker = "## My Starred Repositories\n"
    end_marker = "## "
    pattern = re.compile(f'{re.escape(start_marker)}.*?{re.escape(end_marker)}', re.DOTALL)
    
    new_content = start_marker + "\n"
    for category, repo_names in categories.items():
        new_content += f"### {category}\n"
        for repo_name in repo_names:
            repo = next((r for r in repos if r['name'] == repo_name), None)
            if repo:
                new_content += f"- [{repo['name']}]({repo['html_url']}): {repo['description']}\n"
        new_content += "\n"
    new_content += end_marker

    updated_content = pattern.sub(new_content, content)

    # Update the last edited date
    today = datetime.now().strftime("%Y-%m-%d")
    date_pattern = re.compile(r'Last edited: \d{4}-\d{2}-\d{2}')
    updated_content = date_pattern.sub(f'Last edited: {today}', updated_content)

    with open('README.md', 'w') as file:
        file.write(updated_content)

if __name__ == "__main__":
    username = "seantauber"  # Replace with your GitHub username
    repos = get_starred_repos(username)
    categories = categorize_repos(repos)
    update_readme(repos, categories)
