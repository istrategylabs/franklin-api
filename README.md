# franklin

## Installation

1. Install [boot2docker](http://docs.docker.com/installation/mac/) (if on a Mac)
1. Install docker compose: `sudo pip install -U docker-compose`
1. Initialize your boot2docker system if you have not already: `boot2docker init && boot2docker up`
1. Run `docker-compose up`
1. In a new shell run `boot2docker ip` to find out the IP address of your container
1. Visit site at `<my-ip>:8000`
1. Run commands inside the container like such: `docker-compose run web python manage.py migrate`
