# franklin

Now with Github deploys!

![franklin](http://www.brand-licensing.com/DBImages/lizenzen/franklin-logo.jpg)

## Installation

1. Install [docker toolbox](https://www.docker.com/toolbox)
1. Initialize your docker machine system if you have not already: `docker-machine start default`
1. Create a .env file at the root of the project. (See below for .env contents)
1. Run our startup script: `. ./scripts/setup.sh`
1. In a new shell run `docker-machine ip default` to find out the IP address of your container
1. Visit site at `<my-ip>:5000`
1. Run commands inside the container like such: `docker-compose run web python manage.py migrate`

## Other Considerations

- You will need a `.env` file in the root of your project that defines the following keys:


    ```
      BASE_PROJECT_PATH=~/Desktop                  (root folder where build will save built assets to)
      DJANGO_SETTINGS_MODULE=config.settings.local
      BASE_URL=franklinstatic.com
      SECRET_KEY=<your_secret_key>                 (random key used by django)
      BUILDER_URL=<franklin_builder_url>           (where api can call the running builder)
      ENV='local'
      API_BASE_URL=<franklin_api_url>              (used for services like github to call. usually an ngrok url for testing)
      SOCIAL_AUTH_GITHUB_KEY=<github_client_id>
      SOCIAL_AUTH_GITHUB_SECRET=<github_client_secret>
      GITHUB_SECRET=<for_validating_github_webhook_messages>    (random key used to secure communication with github)
    ```
- Projects you wish to be deployed by franklin will need a `.franklin` file in their root

  ```
    TODO - add example build/deploy settings here.
    Note - Environment configuration will likely be handled during the registration step. So not here.
  ```

### Viewing models at /admin
1. create a superuser `docker-compose run web python manage.py createsuperuser`
1. Login as super user as `http://192.168.99.100:5000/admin/`

## Making Changes to the Code

- If your code change includes a new requirement, you will likely have to run `docker-compose build`. This will re-run the build step which will include a pip install of all requirements.

## Testing
- Details on how to test locally can be [found here](https://github.com/istrategylabs/franklin-api/wiki/testing)
