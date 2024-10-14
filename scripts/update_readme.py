import requests
import re
from datetime import datetime
from openai import OpenAI
import os
import json

def get_starred_repos(username):
    url = f"https://api.github.com/users/{username}/starred"
    headers = {"Authorization": f"token {os.environ['GITHUB_TOKEN']}"}
    response = requests.get(url, headers=headers)
    return response.json()

def update_readme_with_llm(current_readme, starred_repos):
    # Prepare the input for the LLM
    repo_info = "\n".join([f"{repo['full_name']}: {repo['description']} - {repo['html_url']}" for repo in starred_repos])
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    prompt = f"""
    You are tasked with updating a GitHub README.md file. Here's what you need to do:

    1. The current README content is provided below, enclosed in triple backticks.
    2. A list of all currently starred repositories is provided after that, also enclosed in triple backticks.
    3. Replace the contents of the repositories currently in the README with the repositories from the current star list.
    4. Reorganize the repositories into categories, with a strong bias towards changing as little as possible of the category structure of the original README file.
    5. If there are repos that you are unable to classify with reasonable certainty, place them in a catch-all "Other" category. This should be the final category in the document.
    6. Update the table of contents to accurately reflect all of the category sections in the document including links to those sections.
    7. Update the "Last edited" field of the README with the current date: {current_date}.
    8. All parts of the README that are not part of the list of repositories or table of contents(explanations about how this repo works, overviews of what the repo is, user info such as LinkedIn, etc.) should remain unchanged.
    9. Make sure the updated README does not contain triple ticks indication markdown at the beginning or end of the file because this will cause it to not render properly as markdown once it's written into the new README.md
    10. For each repository, use the full URL provided to create a proper markdown link. The format should be: [repository name](full URL)

    Current README:
    ```
    {current_readme}
    ```

    Current starred repositories:
    ```
    {repo_info}
    ```

    Please provide the updated README content, maintaining its original structure as much as possible while incorporating the new repository information. Don't add any comments. Return only the contents of the markdown readme file.
    """

    client = OpenAI()
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that updates GitHub README files."},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content

def main():
    username = "seantauber"  # Replace with your GitHub username
    
    # Read current README
    with open('README.md', 'r') as file:
        current_readme = file.read()
    
    # Get starred repos
    starred_repos = get_starred_repos(username)
    
    # Update README using LLM
    updated_readme = update_readme_with_llm(current_readme, starred_repos)
    
    # Write updated README
    with open('README.md', 'w') as file:
        file.write(updated_readme)

if __name__ == "__main__":
    main()