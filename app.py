from flask import Flask, render_template, request,jsonify,session,redirect
import requests
import re
import time
import json
import yaml
from pymongo import MongoClient

app = Flask(__name__)
client = MongoClient('mongodb://localhost:27017/')
db = client['auto_deployment']
collection = db['github_details']

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

with open("config.yaml") as f:
    config = yaml.safe_load(f)

JENKINS_URL = config.get('JENKINS_URL')
JENKINS_JOB = config.get('JENKINS_JOB')
JENKINS_JOB2 = config.get('JENKINS_JOB2')
JENKINS_JOB3 = config.get('JENKINS_JOB3')
JENKINS_USERNAME = config.get('JENKINS_USERNAME')
JENKINS_API_TOKEN = config.get('JENKINS_API_TOKEN')
CLIENT_ID = config.get('CLIENT_ID')
CLIENT_SECRET = config.get('CLIENT_SECRET')
REDIRECT_URI =  config.get('REDIRECT_URI')

@app.route('/login',methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Redirect the user to GitHub's authentication page
        redirect_uri = REDIRECT_URI  # Redirect URI registered with your GitHub app
        github_auth_url = f"https://github.com/login/oauth/authorize?client_id={CLIENT_ID}&redirect_uri={redirect_uri}&scope=user"
        return jsonify({
            'IsSuccess': True,
            'Message': 'Authentication successful',
            'Data': github_auth_url
        }), 200
        # return redirect(github_auth_url)
    return render_template('login.html')

@app.route('/callback')
def callback():
    try:
        # Exchange the authorization code for an access token
        code = request.args.get('code')
        data = {
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'code': code
        }
        response = requests.post('https://github.com/login/oauth/access_token', data=data, headers={'Accept': 'application/json'})
        access_token = response.json()['access_token']

        if access_token:
            user_info_response = requests.get('https://api.github.com/user', headers={'Authorization': f'token {access_token}'})
            user_info = user_info_response.json()
            repos_url = 'https://api.github.com/user/repos'
            repos_response = requests.get(repos_url, headers={'Authorization': f'token {access_token}'})
            repositories = repos_response.json()
           
            insert_or_update_github_details(user_info,access_token,repositories)
            session['username'] = user_info['login']
  
            return redirect('configuration')
        else:
            return render_template('login.html')
    except Exception as e:
        return render_template('login.html')

def insert_or_update_github_details(user_info,access_token, repositories):
    username = user_info['login']
    existing_user = collection.find_one({'username': username})
    if existing_user:
        # Update repositories for existing user
        collection.update_one({'username': username}, {'$set': {'user_info':user_info,'access_token':access_token,'repositories': repositories}})
        print(f"Repositories updated for user {username}")
    else:
        # Insert new user with repositories
        user_data = {
            'username': username,
            'user_info':user_info,
            'access_token':access_token,
            'repositories': repositories
        }
        collection.insert_one(user_data)
        print(f"New user {username} added with repositories")

def get_github_details(username):
    user_data = collection.find_one({'username': username})
    if user_data:
        return user_data
    else:
        return None

@app.route('/configuration',methods=['GET', 'POST'])
def configuration():
    if request.method == 'POST':
        data = request.json
        github_url = data.get('github_url')
        branch = data.get('branch')
        reponame = data.get('reponame')
        result,sonarqube_report_url = trigger_jenkins_pipeline(github_url,branch,reponame)
        if result == "SUCCESS":
           return jsonify({'github_url': github_url, 'sonarqube_report_url': sonarqube_report_url}), 200
        else:
            return jsonify({'error': 'Failed to trigger Jenkins pipeline'}), 400
    return render_template('/configuration.html')


def trigger_jenkins_pipeline(github_url,branch,reponame):
    job_url = f'{JENKINS_URL}/job/{JENKINS_JOB}/buildWithParameters'
    auth = (JENKINS_USERNAME, JENKINS_API_TOKEN)
    params = {'GITHUB_URL': github_url,'BRANCH_NAME':branch,'PROJECT_NAME':reponame}  # Pass the GitHub URL as a parameter to Jenkins
    response = requests.post(job_url, auth=auth, params=params)
    if response.content:
        json_response = response.json()
        print("Response Content:", json_response)

    if response.status_code == 201:
        print("Jenkins job triggered successfully!")
        queue_item_url = response.headers['Location']
        return wait_for_pipeline_completion(queue_item_url)
        
    else:
        print("Failed to trigger Jenkins job")
        return None


def wait_for_pipeline_completion(queue_item_url):
    auth = (JENKINS_USERNAME, JENKINS_API_TOKEN)
    while True:
        try:
            queue_response = requests.get(queue_item_url + "/api/json", auth=auth)
            queue_response.raise_for_status()  # Check for HTTP errors
            
            queue_status = queue_response.json()
            if 'executable' in queue_status and queue_status['executable'] is not None:
                    build_url = queue_status['executable']['url']
                    build_response = requests.get(build_url + "/api/json", auth=auth)
                    build_response.raise_for_status()  # Check for HTTP errors
                    
                    build_status = build_response.json()
                    if build_status['result'] is not None:
                        print(f"Pipeline completed with result: {build_status['result']}")
                        
                        sonarqube_report_url = None
                        actions = build_status.get('actions', [])
                        for action in actions:
                            if 'hudson.plugins.sonar.action.SonarBuildBadgeAction' in action.get('_class', ''):
                                sonarqube_report_url = action.get('url', '')
                                break
                        
                        return build_status['result'],sonarqube_report_url
                    elif build_status['building']:
                        print("Pipeline is still running...")
                    else:
                        print("Pipeline stopped unexpectedly.")
                        return None
            else:
               print("Queue item not yet executable. Waiting...")
        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
        
        # Wait for 10 seconds before checking again
        time.sleep(10)


@app.route('/repos',methods=['GET'])
def repos():
    username = session.get('username')
    if username:
        github_details = get_github_details(username)
        repositories = github_details['repositories']
        if repositories:
            return jsonify({
                    'IsSuccess': True,
                    'Message': 'Successful',
                    'Data': repositories
                }), 200
        else:
            return jsonify({
                'IsSuccess': False,
                'Message': 'No repositories found',
                'Data': []
            }), 200
    else:
        return jsonify({
                'IsSuccess': False,
                'Message': 'Failed',
                'Data': ""
            }), 200

@app.route('/repo_details', methods=['POST'])
def repo_details():
    data = request.json
    git_url = data.get('github_url')
    branch = data.get('branch')
    reponame = data.get('reponame')
    username = session.get('username')

    if username:
        github_details = get_github_details(username)
        access_token = github_details['access_token']
        
        if not git_url or not access_token:
            return jsonify({
                'IsSuccess': False,
                'Message': 'Git URL and access token are required',
                'Data': None
            }), 400

        try:
            # Fetch repository details from Git API using access token
            headers = {'Authorization': f'token {access_token}'}
            url_with_branch = f'https://api.github.com/repos/{username}/{reponame}/contents?ref={branch}'
            response = requests.get(url_with_branch, headers=headers)

            # Check if the request was successful
            if response.ok:
                repo_details = response.json()
                files_and_folders = [{'name': item['name'], 'type': item['type']} for item in repo_details]
                files = []
                for item in repo_details:
                    if item['type'] == 'file':
                        files.append(item['name'])
                    elif item['type'] == 'dir':
                        # Recursively fetch files within the folder
                        #folder_files = fetch_folder_contents(username, reponame, item['path'], branch, access_token)
                        #files.extend([f"{item['path']}/{file}" for file in folder_files])
                        #folder_files = fetch_folder_contents(username, reponame, item['path'], branch, access_token)
                        files.append(item['path']+'/')


                return jsonify({
                    'IsSuccess': True,
                    'Message': 'Repository details fetched successfully',
                    'Data': files
                }), 200
            else:
                return jsonify({
                    'IsSuccess': False,
                    'Message': 'Failed to fetch repository details',
                    'Data': None
                }), response.status_code
        except Exception as e:
            return jsonify({
                'IsSuccess': False,
                'Message': f'An error occurred: {str(e)}',
                'Data': None
            }), 500


@app.route('/fetch_folder_contents', methods=['POST'])
def fetch_folder_contents():
    data = request.json
    branch = data.get('branch')
    reponame = data.get('reponame')
    folder_path = data.get('folderPath')
    username = session.get('username')
    if username:
        github_details = get_github_details(username)
        access_token = github_details['access_token']
        headers = {'Authorization': f'token {access_token}'}
        url = f'https://api.github.com/repos/{username}/{reponame}/contents/{folder_path}?ref={branch}'
        response = requests.get(url, headers=headers)
        if response.ok:
            folder_contents = response.json()
            files = []
            # for item in folder_contents:
            #     if item['type'] == 'file':
            #         files.append(item['name'])
            #     elif item['type'] == 'dir':
            #         # Recursively fetch files within the subfolder
            #         subfolder_files = fetch_folder_contents(username, reponame, item['path'], branch, access_token)
            #         files.extend([f"{item['path']}/{file}" for file in subfolder_files])
            for item in folder_contents:
                if item['type'] == 'file':
                    files.append(item['name'])
                elif item['type'] == 'dir':
                        # Recursively fetch files within the folder
                    # folder_files = fetch_folder_contents(username, reponame, item['path'], branch, access_token)
                    files.append(item['path']+'/')

            return jsonify({
                    'IsSuccess': True,
                    'Message': 'Repository details fetched successfully',
                    'Data': files
                }), 200
        else:
            return []
    else:
        return []

def detect_project_type_with_git_api(repo_url):
    # Assuming the URL is in the format https://github.com/username/repo
    parts = repo_url.split('/')
    username = parts[-2]
    repo_name = parts[-1]

    # Make a request to GitHub API to get the contents of the repository
    url = f'https://api.github.com/repos/{username}/{repo_name}/contents'
    headers = {'Accept': 'application/vnd.github.v3+json'}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        contents = response.json()
        # Check for common project files or directories
        has_python_files = any(file['name'].endswith('.py') for file in contents)
        has_dotnet_files = any(file['name'].endswith('.csproj') for file in contents)
        has_react_files = any(file['name'] == 'package.json' for file in contents)
        
        if has_python_files:
            return 'Python Project'
        elif has_dotnet_files:
            return '.NET Project'
        elif has_react_files:
            return 'React Project'
        else:
            return 'Unknown Project Type'
    else:
        return 'Error: Unable to fetch repository information'

@app.route('/get_branches', methods=['POST'])
def get_branches():
    data = request.json
    repo = data.get('reponame')
    username = session.get('username')
    if username:
        github_details = get_github_details(username)
        access_token = github_details['access_token']
        url = f'https://api.github.com/repos/{username}/{repo}/branches'
        headers = {'Authorization': f'token {access_token}'}
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            branches = response.json()
            return branches
        else:
            print(f"Failed to fetch branches: {response.status_code}")
            return []
    else:
        return []


@app.route('/stack',methods=['GET', 'POST'])
def stack():
    if request.method == 'POST':
        data = request.json
        github_url = data.get('github_url')
        stack = data.get('stack')
        port = data.get('port')
        reponame = data.get('reponame')
        branch = data.get('branch')
        result = trigger_jenkins_pipeline_stack(github_url,port,reponame,branch)
        # result = "SUCCESS"
        if result == "SUCCESS":
           return jsonify({'github_url': github_url}), 200
        else:
            return jsonify({'error': 'Failed to trigger Jenkins pipeline'}), 400
    return render_template('stack.html')

def trigger_jenkins_pipeline_stack(github_url,port,reponame,branch):
    job_url = f'{JENKINS_URL}/job/{JENKINS_JOB2}/buildWithParameters'
    auth = (JENKINS_USERNAME, JENKINS_API_TOKEN)
    params = {'GITHUB_URL': github_url,'PORT': port,'BRANCH_NAME': branch,'PROJECT_NAME': reponame}  # Pass the GitHub URL as a parameter to Jenkins
    # params = {'PORT': port}
    # params = {'NAME_OF_DEPLOYMENT': 'Test'}
    response = requests.post(job_url, auth=auth, params=params)
    if response.content:
        json_response = response.json()
        print("Response Content:", json_response)

    if response.status_code == 201:
        print("Jenkins job triggered successfully!")
        queue_item_url = response.headers['Location']
        return wait_for_pipeline_completion_stack(queue_item_url)
    else:
        print("Failed to trigger Jenkins job")
        return None


def wait_for_pipeline_completion_stack(queue_item_url):
    auth = (JENKINS_USERNAME, JENKINS_API_TOKEN)
    while True:
        try:
            queue_response = requests.get(queue_item_url + "/api/json", auth=auth)
            queue_response.raise_for_status()  # Check for HTTP errors
            
            queue_status = queue_response.json()
            if 'executable' in queue_status and queue_status['executable'] is not None:
                    build_url = queue_status['executable']['url']
                    build_response = requests.get(build_url + "/api/json", auth=auth)
                    build_response.raise_for_status()  # Check for HTTP errors
                    
                    build_status = build_response.json()
                    if build_status['result'] is not None:
                        print(f"Pipeline completed with result: {build_status['result']}")
                        return build_status['result']
                    elif build_status['building']:
                        print("Pipeline is still running...")
                    else:
                        print("Pipeline stopped unexpectedly.")
                        return None
            else:
               print("Queue item not yet executable. Waiting...")
        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
        
        # Wait for 10 seconds before checking again
        time.sleep(10)

@app.route('/deployment',methods=['GET', 'POST'])
def deployment():
    if request.method == 'POST':
        data = request.json
        port = data.get('port')
        reponame = data.get('reponame')
        result = trigger_jenkins_pipeline_deployment(port,reponame)
        if result == "SUCCESS":
           return jsonify({'Message': result}), 200
        else:
            return jsonify({'error': 'Failed to trigger Jenkins pipeline'}), 400
    return render_template('deployment.html')

def trigger_jenkins_pipeline_deployment(port,reponame):
    job_url = f'{JENKINS_URL}/job/{JENKINS_JOB3}/buildWithParameters'
    auth = (JENKINS_USERNAME, JENKINS_API_TOKEN)
    params = {'PORT': port,'PROJECT_NAME': reponame}  # Pass the GitHub URL as a parameter to Jenkins
    response = requests.post(job_url, auth=auth, params=params)
    if response.content:
        json_response = response.json()
        print("Response Content:", json_response)

    if response.status_code == 201:
        print("Jenkins job triggered successfully!")
        queue_item_url = response.headers['Location']
        return wait_for_pipeline_completion_stack(queue_item_url)
        
    else:
        print("Failed to trigger Jenkins job")
        return None

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')








# def get_sonarqube_report_url():
#     # Parse Jenkins console output to extract SonarQube report URL
#     # You may need to adjust the regular expression based on the actual output format
#     console_output_url = f'{JENKINS_URL}/job/{JENKINS_JOB}/lastBuild/consoleText'
#     console_output_response = requests.get(console_output_url, auth=(JENKINS_USERNAME, JENKINS_API_TOKEN))
    
#     if console_output_response.status_code == 200:
#         console_output = console_output_response.text
#         matcher = re.search(r'INFO: ANALYSIS SUCCESSFUL, you can find the results at: (.+)', console_output)
#         if matcher:
#             sonarqube_report_url = matcher.group(1)
#             return sonarqube_report_url
#         else:
#             print("SonarQube report URL not found in Jenkins console output")
#             return None
#     else:
#         print("Failed to fetch Jenkins console output")
#         return None
    
def get_sonarqube_report_url():
    max_retries = 10  # Maximum number of retries
    retry_delay = 10  # Delay between retries in seconds
    
    for _ in range(max_retries):
        time.sleep(retry_delay)  # Wait before making the next attempt
        console_output_url = f'{JENKINS_URL}/job/{JENKINS_JOB}/lastBuild/consoleText'
        console_output_response = requests.get(console_output_url, auth=(JENKINS_USERNAME, JENKINS_API_TOKEN))
        
        if console_output_response.status_code == 200:
            console_output = console_output_response.text
            matcher = re.search(r'INFO: ANALYSIS SUCCESSFUL, you can find the results at: (.+)', console_output)
            if matcher:
                sonarqube_report_url = matcher.group(1)
                return sonarqube_report_url
            else:
                print("SonarQube report URL not found in Jenkins console output")
        else:
            print("Failed to fetch Jenkins console output")

    print("Reached maximum number of retries. Unable to fetch SonarQube report URL.")
    return None

if __name__ == '__main__':
    app.run(debug=True,port=5001)
