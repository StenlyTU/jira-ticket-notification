pipeline {
     options {
        retry(1)
        ansiColor('xterm')
    }
  agent {
    kubernetes {
	  label "${UUID.randomUUID().toString()}"
      defaultContainer 'python'
      yaml """
apiVersion: v1
kind: Pod
metadata:
  labels:
    some-label: some-label-value
spec:
  containers:
  - name: python
    image: python:3.6-buster
    command:
    - cat
    tty: true
"""
    }
  }
  stages {
    stage('Run_Ticket_Notification') {
      steps {
        container('python') {
			withCredentials( [file(credentialsId: '0ab7d3e1-17cf-4bb2-a9e8-15e530a16XXX', variable: 'MY_SECRET_FILE')])
						{
							sh('cp $MY_SECRET_FILE /tmp/config.ini')
						}
			sh 'rm -rf ./jira-ticket-notification || true'
			withCredentials([usernamePassword(credentialsId: 'github-Puser', passwordVariable: 'PSPASSWORD', usernameVariable: 'PSUSERNAME')]) {sh 'git clone https://$PSUSERNAME:$PSPASSWORD@github.com/jira-ticket-notification.git'}
			sh 'pip3 install -r ./jira-ticket-notification/requirements.txt'
			sh 'python3 ./jira-ticket-notification/ticket_notification.py'
		}
      }
    }
  }
  post {
      failure {
      sh """
        # Skip posting during the Weekend.
        if [ \$(date +%u) -le 5 ]; then
            curl -X POST -H 'Content-type: application/json' --data '{"text":"Ticket Notification build failure at ${env.BUILD_URL}", "channel": "#some_name","icon_emoji":":bell:","username":"Our Jira Integration"}' 'https://hooks.slack.com/services/...XXX'
        fi
      """
      }
  }
}
