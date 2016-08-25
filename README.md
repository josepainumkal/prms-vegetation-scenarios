## prms-fire-scenarios

In keeping with our aim of serving specific hydrologists' needs while building or demonstrating core
cyberinfrastructure (CI), this tool uses Virtual Watershed technology to provide a tool for
hydrologists wanting to investigate the effects of fire on the outputs of PRMS models.

## Prototype Goals and Milestones (as of 2/25)

There is [one current milestone](https://github.com/VirtualWatershed/prms-fire-scenarios/milestones):

1. [v1.0 Release due May 13](https://github.com/VirtualWatershed/prms-fire-scenarios/milestones/v1.0%20Release)

The [issues](https://github.com/VirtualWatershed/prms-fire-scenarios/issues)
show what needs to be done.

# Info and Getting Started

## Installing and Launching Dockerized Auth/Modeling Server

The first step to getting started is to set up the development
modeling and authorization server using Docker. You will need to install the
[docker-toolkit](https://www.docker.com/products/docker-toolbox) no matter what
OS you're working with. 

Next, clone
[vw-deploy](https://github.com/VirtualWatershed/vw-deploy), start a new docker
machine, then create an account on the docker machine you started by visiting
`ip-of-your-docker-machine:5005`. (Let's use "a@b.com" as the username and "123456" as the password)

To get the ip of your docker machine, run `docker-machine ip vw-machine`.
Probably it will be `196.168.99.100`. But it may not be, so be sure to check.

Here are the commands to get your docker machine (named `vw-machine`) going:

```bash
docker-machine create --driver virtualbox vw-machine
```

excluding `vw-machine` will create a machine called `default`.

This starts the machine. You need to set this machine to be the environment
you're working with. Running

```bash
docker-machine env vw-machine
```

will give you a message saying on how to configure your shell, as well as the
environment variables that will be set when you execute the command. That
command is

```bash
eval $(docker-machine env vw-machine)
```

Next, we need to bring up our docker container on the docker machine. The first
time it runs, it will need to download and install some dependencies on the
docker machine. This will not make any changes to your local file system.

```bash
cd vw-deploy/v1.0/development && docker-compose -f docker-compose.dev.yml up
```

When it's finished, navigate to
[http://196.168.99.100:5005](http://196.168.99.100:5005) and create a
development account. Unfortunately you'll have to create on every time you use
the development system. But on the upside, it's easy to create a new development
account. To "receive" your confirmation email, navigate to
[http://196.168.99.100:1080](http://196.168.99.100:1080) to read your
development emails.

And then we need to open another terminal and connect to our docker virtual machine:
```bash
eval $(docker-machine env default)
``` 
Start a mongo container with the name mongo:
```bash
docker run --name mongo -d mongo
```
Go to the prms vegetation repo folder, for me it is: Desktop/prms-vegetation-scenarios
Run this command to create an docker image with the name proms-veg:
```
docker build -t prms-veg .
```
Run a container with the image prms-veg, the port number is 5010. The container name is prms:
```
docker run --name prms -e APP_PORT=5010 -e APP_USERNAME='a@b.com' -e APP_PASSWORD='123456'  -e MONGODB_HOST=mongo  -p 5010:5010 -v /Users/rwu/Desktop/prms-vegetation-scenarios/app:/var/www/prms-veg/app --link mongo:mongo  prms-veg python manage.py runserver -h 0.0.0.0 -p 5010 --threaded
```
And then visit [http://192.168.99.100:5010/scenario_table](http://192.168.99.100:5010/scenario_table)
You will see the scenario table and create a scenario by yourself.

## Install Non-Dockerized Dependencies and Run the App

Install Python dependencies using virtualenv

```
virtualenv venv && source venv/bin/activate && pip install -r requirements.txt
```

Next, install Javascript dependencies using [Bower](http://bower.io).

```
bower install
```

At this point bower has overwritten something in the repository. To put it back,

```
git checkout -- app/static/bower_components/swagger-ui/dist/index.html
```

Now use gunicorn to start the server. We need multiple threads and this
configuration seemed to be best.

```bash
gunicorn --worker-class eventlet -w 4 manage:app -b 127.0.0.1:5000 \
  --error-logfile='err.log' --access-logfile='log.log' --log-level DEBUG
  -e APP_USERNAME='maturner01@gmail.com' -e APP_PASSWORD='ajajaj'
```

If the MongoDB collection is empty (you haven't inserted any documents manually
or run any scenarios), a single record will be inserted as a placeholder for
development purposes. After you start the server, visit
[localhost:5000](http://localhost:5000) to see the web interface. Scroll to the
bottom to view the list of scenarios. There will be a hydrograph in the
`hydrograph` attribute of the JSON that gets delivered to your browser when you
click the `View JSON` link in the list at the bottom.

If you visit [localhost:5000/api/scenarios](http://localhost:5000/api/scenarios)
you will see the list of current scenarios with one current scenario.

API routes are in
[app/api/views.py](https://github.com/VirtualWatershed/prms-fire-scenarios/blob/master/app/api/views.py).



### Run Swagger-UI to see spec

Now, finally, we can run our Swagger-UI and look at the spec by running

```
./serve-swag.sh
```

and visiting [http://localhost:8000/swagger-ui/dist/?url=/../../api-spec.yaml](http://localhost:8000/swagger-ui/dist/?url=/../../api-spec.yaml).

We need to make this spec actually happen. This is the API the frontend and Chase's Unity vis will use to run and access scenarios.
