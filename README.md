# franklin

Now with Github deploys!

![franklin](http://www.brand-licensing.com/DBImages/lizenzen/franklin-logo.jpg)

## Installation

1. Install [docker toolbox](https://www.docker.com/toolbox)
1. Initialize your docker machine system if you have not already: `docker-machine start default`
1. Run our startup script: `. ./scripts/setup.sh`
1. In a new shell run `docker-machine ip default` to find out the IP address of your container
1. Visit site at `<my-ip>:8000`
1. Run commands inside the container like such: `docker-compose run web python manage.py migrate`

## Other Considerations

- You will need a `.env` file in the root of your project that defines the following keys:


    ```
      CLIENT_ID=<github_client_id>
      CLIENT_SECRET=<github_client_secret>
      BASE_PROJECT_PATH=~/Desktop
      DJANGO_SETTINGS_MODULE=config.settings.local
      BASE_URL=franklinstatic.com
      SECRET_KEY=<your_secret_key>
    ```

## Making Changes to the Code

- If your code change includes a new requirement, you will likely have to run `docker-compose build`. This will re-run the build step which will include a pip install of all requirements.
