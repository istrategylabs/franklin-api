# franklin

## Installation

1. Install [boot2docker](http://docs.docker.com/installation/mac/) (if on a Mac)
1. [Install docker compose](https://docs.docker.com/compose/install/)
1. Initialize your boot2docker system if you have not already: `boot2docker init && boot2docker up`
1. Run `docker-compose up`
1. In a new shell run `boot2docker ip` to find out the IP address of your container
1. Visit site at `<my-ip>:8000`
1. Run commands inside the container like such: `docker-compose run web python manage.py migrate`

## Other Considerations

- You will need a `.env` file in the root of your project that defines the following keys:


    ```
      CLIENT_ID=<github_client_id>
      CLIENT_SECRET=<github_client_secret>
      BASE_PROJECT_PATH=~/Desktop
      DJANGO_SETTINGS_MODULE=config.settings.local
    ```

## Making Changes to the Code

- If your code change includes a new requirement, you will likely have to run `docker-compose build`. This will re-run the build step which will include a pip install of all requirements.
