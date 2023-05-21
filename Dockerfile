FROM ubuntu


RUN apt-get update && \
    apt-get -y upgrade && \
    apt-get install -y \
    sudo


RUN DEBIAN_FRONTEND=noninteractive apt-get -y install python3 pip vim mc wget curl 


COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt



CMD python3 -c "print('Docker is more simple Deployment Tool')"

RUN pwd
RUN ls -l


EXPOSE 7860



CMD "flask run --host=0.0.0.0 --port=7860"