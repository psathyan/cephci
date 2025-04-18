/*
    Pipeline script for fetching rhos-d quota.
*/
// Global variables section
def sharedLib
def user_csv_url = "${params.Users_Csv_Url}"
node("rhel-9-medium") {
    try {
        stage('prepareNode') {
            checkout(
                scm: [
                    $class: 'GitSCM',
                    branches: [[name: "origin/main"]],
                    extensions: [[
                        $class: 'CleanBeforeCheckout',
                        deleteUntrackedNestedRepositories: true
                    ], [
                        $class: 'WipeWorkspace'
                    ], [
                        $class: 'CloneOption',
                        depth: 1,
                        noTags: true,
                        shallow: true,
                        timeout: 10,
                        reference: ''
                    ]],
                    userRemoteConfigs: [[
                        url: "https://github.com/red-hat-storage/cephci.git"
                    ]]
                ],
                changelog: false,
                poll: false
            )
            sharedLib = load("${env.WORKSPACE}/pipeline/vars/v3.groovy")
            sharedLib.prepareNode(2)
        }
        stage('retrieveQuota') {
            println("Fetch quota and Send Email")
            cmd = ".venv/bin/python ${env.WORKSPACE}/utility/psi_quota.py --osp-cred ${env.HOME}/osp-cred-ci-2.yaml --rhosd-user-csv ${user_csv_url}"

            rc = sh(script: "${cmd}", returnStatus: true)
            if (rc != 0) {
                println("Something went wrong...${rc}")
                currentBuild.result = 'FAILURE'
            }
        }
    } catch(Exception err) {
        if (currentBuild.result == "ABORTED") {
            println("Aborting the workflow")
            return
        }

        // notify about failure
        currentBuild.result = "FAILURE"
        def failureReason = err.getMessage()
        def subject =  "[CEPHCI-PIPELINE-ALERT] [JOB-FAILURE] - ${env.JOB_NAME}/${env.BUILD_NUMBER}"
        def body = "<body><h3><u>Job Failure</u></h3></p>"
        body += "<dl><dt>Jenkins Build:</dt><dd>${env.BUILD_URL}</dd>"
        body += "<dt>Failure Reason:</dt><dd>${failureReason}</dd></dl></body>"

        emailext (
            mimeType: 'text/html',
            subject: "${subject}",
            body: "${body}",
            from: "cephci@redhat.com",
            to: "cephci@redhat.com"
        )
        subject += "\n Jenkins URL: ${env.BUILD_URL}"
        googlechatnotification(url: "id:rhcephCIGChatRoom", message: subject)
    }
}
