import requests
import re

def get_starred_repos(username):
    url = f"https://api.github.com/users/{username}/starred"
    response = requests.get(url)
    return response.json()

def update_readme(repos):
    with open('README.md', 'r') as file:
        content = file.read()

    # Find the section to update
    start_marker = "## My Starred Repositories\n"
    end_marker = "## "
    pattern = re.compile(f'{re.escape(start_marker)}.*?{re.escape(end_marker)}', re.DOTALL)
    
    # Prepare new content
    new_content = start_marker
    for repo in repos[:10]:  # Limit to top 10 starred repos
        new_content += f"- [{repo['name']}]({repo['html_url']}): {repo['description']}\n"
    new_content += end_marker

    # Replace the old content with new content
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
    update_readme(repos)
