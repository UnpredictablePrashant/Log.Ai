# Log.Ai

# jenkins installation

```
sudo apt update -y
#sudo apt upgrade -y
wget -O - https://packages.adoptium.net/artifactory/api/gpg/key/public | tee /etc/apt/keyrings/adoptium.asc
echo "deb [signed-by=/etc/apt/keyrings/adoptium.asc] https://packages.adoptium.net/artifactory/deb $(awk -F= '/^VERSION_CODENAME/{print$2}' /etc/os-release) main" | tee /etc/apt/sources.list.d/adoptium.list
sudo apt update -y
sudo apt install temurin-17-jdk -y
/usr/bin/java --version
curl -fsSL https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key | sudo tee \
                  /usr/share/keyrings/jenkins-keyring.asc > /dev/null
echo deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc] \
                  https://pkg.jenkins.io/debian-stable binary/ | sudo tee \
                              /etc/apt/sources.list.d/jenkins.list > /dev/null
sudo apt-get update -y
sudo apt-get install jenkins -y
sudo systemctl start jenkins
sudo systemctl status jenkins
```

http://<>:8080

password -  sudo cat /var/lib/jenkins/secrets/initialAdminPassword

![image](https://github.com/UnpredictablePrashant/Log.Ai/assets/60352729/1465df3b-634e-4395-ab9c-9476b88adaca)


# sonarqube

```
docker run -d --name sonar -p 9000:9000 sonarqube:lts-community
```
![image](https://github.com/UnpredictablePrashant/Log.Ai/assets/60352729/a19e85ed-5f15-4865-b53e-49af75256cdb)

username - admin

password - admin

![image](https://github.com/UnpredictablePrashant/Log.Ai/assets/60352729/24af1c6f-2e52-4d5b-b3a1-8515a260773a)


# Email Integration With Jenkins and Plugin Setup for notification


# Install Plugins like JDK, Sonarqube Scanner, NodeJs, OWASP Dependency Check

![image](https://github.com/UnpredictablePrashant/Log.Ai/assets/60352729/9325a0e3-bc97-491f-af12-3b6ca9fd5e5e)

Goto Manage Jenkins →Plugins → Available Plugins 
Install below plugins

1 → Eclipse Temurin Installer (Install without restart)

2 → SonarQube Scanner (Install without restart)

3 → NodeJs Plugin (Install Without restart)

# Configure Java and Nodejs in Global Tool Configuration

Goto Manage Jenkins → Tools → Install JDK(17) and NodeJs(16)→ Click on Apply and Save

![image](https://github.com/UnpredictablePrashant/Log.Ai/assets/60352729/a27f73fd-127e-4712-9158-c78cb106559b)

![image](https://github.com/UnpredictablePrashant/Log.Ai/assets/60352729/9a83f2ad-7bc4-4587-ace2-5ac7a4201c3f)


# Configure Sonar Server in Manage Jenkins

Click on Administration → Security → Users → Click on Tokens and Update Token → Give it a name → and click on Generate Token
![image](https://github.com/UnpredictablePrashant/Log.Ai/assets/60352729/592bd5da-9e98-48a3-8f0f-be704126eb0c)


![image](https://github.com/UnpredictablePrashant/Log.Ai/assets/60352729/affa5db3-7a2f-4256-9134-4e2ad1e1fb3f)

Goto Jenkins Dashboard → Manage Jenkins → Credentials → Add Secret Text. It should look like this

![image](https://github.com/UnpredictablePrashant/Log.Ai/assets/60352729/9f6fb8fc-c732-4a79-b59d-aa7d685bfa76)


![image](https://github.com/UnpredictablePrashant/Log.Ai/assets/60352729/5654d4ec-eb70-472c-8099-e9ff97267e0c)

Now, go to Dashboard → Manage Jenkins → System 
![image](https://github.com/UnpredictablePrashant/Log.Ai/assets/60352729/4fbd1509-2824-4161-a293-292798faa681)



![image](https://github.com/UnpredictablePrashant/Log.Ai/assets/60352729/38b811ad-9d66-4577-af7d-1a7e7691c612)

In the Sonarqube Dashboard add a quality gate also

Administration--> Configuration-->Webhooks
![image](https://github.com/UnpredictablePrashant/Log.Ai/assets/60352729/9946104b-ecce-41df-a95d-41c0d5e91219)


![image](https://github.com/UnpredictablePrashant/Log.Ai/assets/60352729/0e6373fd-3c9d-482f-9b17-bf3a2923886e)


To build docker inside the jenkins it will ask for root previdledges

```
sudo visudo
jenkins ALL=(ALL) NOPASSWD: ALL
service jenkins start
```
