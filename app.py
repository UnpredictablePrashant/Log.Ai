from flask import Flask, render_template, request,jsonify
import requests
import re
import time
import json


app = Flask(__name__)

JENKINS_URL = 'http://192.168.0.105:8080'
JENKINS_JOB = 'test'

# Jenkins API credentials
JENKINS_USERNAME = 'admin'
JENKINS_API_TOKEN = '11eb6ad305f810440698eaa7f1b1b58706'


# @app.route('/')
# def index():
#     return render_template('index.html')

@app.route('/1Page',methods=['GET', 'POST'])
def page1():
    if request.method == 'POST':
        data = request.json
        github_url = data.get('github_url')
        result,sonarqube_report_url = trigger_jenkins_pipeline(github_url)
        if result == "SUCCESS":
           return jsonify({'github_url': github_url, 'sonarqube_report_url': sonarqube_report_url}), 200
        else:
            return jsonify({'error': 'Failed to trigger Jenkins pipeline'}), 400
    return render_template('1Page.html')


@app.route('/2Page',methods=['GET', 'POST'])
def page2():
    if request.method == 'POST':
        data = request.json
        github_url = data.get('github_url')
        stack = data.get('stack')
        port = data.get('port')
        result = "SUCCESS"
        if result == "SUCCESS":
           return jsonify({'github_url': github_url}), 200
        else:
            return jsonify({'error': 'Failed to trigger Jenkins pipeline'}), 400
    return render_template('2Page.html')


@app.route('/3Page',methods=['GET', 'POST'])
def page3():
    if request.method == 'POST':
        data = request.json
        github_url = data.get('github_url')
        result,sonarqube_report_url = trigger_jenkins_pipeline(github_url)
        if result == "SUCCESS":
           return jsonify({'github_url': github_url, 'sonarqube_report_url': sonarqube_report_url}), 200
        else:
            return jsonify({'error': 'Failed to trigger Jenkins pipeline'}), 400
    return render_template('3Page.html')

@app.route('/', methods=['GET', 'POST'])
def index():
        # trigger_jenkins_pipeline(github_url)
        # return render_template('success.html', github_url=github_url)

    return render_template('index.html')


def trigger_jenkins_pipeline(github_url):
    job_url = f'{JENKINS_URL}/job/{JENKINS_JOB}/buildWithParameters'
    auth = (JENKINS_USERNAME, JENKINS_API_TOKEN)
    params = {'GITHUB_URL': github_url}  # Pass the GitHub URL as a parameter to Jenkins
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
