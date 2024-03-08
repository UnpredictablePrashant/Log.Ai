from flask import Flask, render_template, request
import requests
import re
import time

app = Flask(__name__)

JENKINS_URL = 'http://192.168.100.95:8080'
JENKINS_JOB = 'test4'

# Jenkins API credentials
JENKINS_USERNAME = 'admin'
JENKINS_API_TOKEN = '11b670728ca3486374c851b0203e661ffb'

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        github_url = request.form['github_url']
        sonarqube_report_url = trigger_jenkins_pipeline(github_url)
        if sonarqube_report_url:
            return render_template('success.html', github_url=github_url, sonarqube_report_url=sonarqube_report_url)
        else:
            return render_template('failure.html')

    return render_template('index.html')


def trigger_jenkins_pipeline(github_url):
    job_url = f'{JENKINS_URL}/job/{JENKINS_JOB}/buildWithParameters'
    auth = (JENKINS_USERNAME, JENKINS_API_TOKEN)
    params = {'GITHUB_URL': github_url}  # Pass the GitHub URL as a parameter to Jenkins
    response = requests.post(job_url, auth=auth, params=params)

    if response.status_code == 201:
        print("Jenkins job triggered successfully!")
        return get_sonarqube_report_url()  # Get SonarQube report URL after triggering job
    else:
        print("Failed to trigger Jenkins job")
        return None

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

@app.route('/success')
def success():
    return render_template('success.html')



if __name__ == '__main__':
    app.run(debug=True)
