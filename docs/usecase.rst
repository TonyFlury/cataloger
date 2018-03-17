================
Typical Use Case
================

The cataloger was designed initially to verfiy the deployment of of a Django based web site. When Using the Django framework the directory structure in the development environment (that of a project directory containing one or more app directories) is the same directory structure replicated in when the project is deployed; the same files in the same relative places - with a few exceptions - for instance in Django you may well not deploy the contents of your Static content directory from your development environment).

There are a number of production/live environments which use git/git hub to transfer between development and deployment - the normal process would be :

On the development machine :

 #. Develop
 #. Test
 #. git commit
 #. git push

On the deployment platform :

 #. Clone from github
 #. Setup
 #. Deployment tests
 #. enable

The challenge with this process can be that there is no confirmation that all the neccessary files have been added to your git repo, so the content on the deployment platform maybe missing key files, or a file gets inadvertantly omitted from the latest committ, and therefore the clone on the deployment server fails to replace some files which were actually updated during development - no amount of testing on the development server will identify files missing from the github repo.

With cataloger, the development process becomes :

On the development machine :

 #. Develop
 #. Test
 #. catalog create
 #. add catalog file and catalog.cfg to git repo
 #. git commit
 #. git push

On the deployment platform :

 #. Clone from github
 #. catalog check - using the cloned catalog.cfg
 #. Setup
 #. Deployment tests
 #. enable

With this revised process, you know by step 2 on the deployment platform if there are missing, extra or non-updated files within the deployment platform; it is very literally a confirmation that what you are deploying is what you have tested - without even have to run any potentially expensive tests.