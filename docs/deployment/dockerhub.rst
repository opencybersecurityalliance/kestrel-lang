| The jupyter hub docker images are at: https://github.com/jupyter/docker-stacks.  We will extend them for Kestrel-as-a-Service and other use cases.  At the moment the docker image is getting pushed to - https://hub.docker.com/repository/docker/kpeeples/kaas-baseline/general.  The dockerfile in this repo includes kestrel-lang, kestrel-analytics, kestrel-huntbook and tutorials.  The workflow file automatically builds the image upon commits.
| 
| Login to dockerhub using one of the examples:  
| A. $ docker login  
| Username:   
| Password:  
| Login Succeeded  
| B. $ docker login --username demo --password example  
| C. $ cat password.txt | docker login --username demo --password-stdin  
| Note: you can use a credential helper - https://docs.docker.com/engine/reference/commandline/login/#credentials-store  
|   
| Manually Build image using one of the examples, the below url should change to the kestrel-lang url  
| A. $ docker build -t kpeeples/kaas-baseline:latest -t kpeeples/kaas-baseline:v1  
| B. $ sudo docker build -t kpeeples/kaas-baseline:latest -t kpeeples/kaas-baseline:v2 https://raw.githubusercontent.com/kpeeples/kestrel-as-a-service/main/dockerhub/Dockerfile  
|   
| Push image, version should be incremental and will be standardized later  
| A. $ sudo docker push kpeeples/kaas-baseline:v1   
| B. $ sudo docker push kpeeples/kaas-baseline:latest  
| 
